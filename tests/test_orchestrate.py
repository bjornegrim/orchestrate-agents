"""Offline checks. Run: python -m unittest discover -s tests"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "plugins" / "orchestrate-claude"
SKILL = CLAUDE / "skills" / "orchestrate"
SCRIPTS = SKILL / "scripts"


def git_shell():
    """Return sh and an environment where its core tools resolve."""
    env = os.environ.copy()
    if os.name != "nt":
        return shutil.which("sh"), env
    exec_path = subprocess.check_output(["git", "--exec-path"], text=True).strip()
    for parent in Path(exec_path).parents:
        sh = parent / "usr" / "bin" / "sh.exe"
        if sh.exists():
            # Started outside Git Bash, sh finds neither mktemp nor sort without this.
            env["PATH"] = f"{sh.parent}{os.pathsep}{env['PATH']}"
            return str(sh), env
    raise RuntimeError("Git for Windows sh.exe not found")


SH, ENV = git_shell()


class TempCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="orchestrate test "))
        self.addCleanup(shutil.rmtree, self.tmp, onexc=self._force_remove)

    @staticmethod
    def _force_remove(func, path, _exc):
        os.chmod(path, 0o700)  # git objects are read-only on Windows
        func(path)

    def run_script(self, name, *args, cwd=None):
        return subprocess.run(
            [SH, str(SCRIPTS / name), *map(str, args)],
            cwd=cwd or self.tmp, env=ENV, capture_output=True, text=True,
        )


class SnapshotTests(TempCase):
    def setUp(self):
        super().setUp()
        self.git("init", "-q")
        # The Windows default, where line-ending conversion could split the two ids.
        self.git("config", "core.autocrlf", "true")
        self.git("config", "commit.gpgsign", "false")

    def git(self, *args):
        return subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@localhost", *args],
            cwd=self.tmp, env=ENV, capture_output=True, text=True, check=True,
        ).stdout.strip()

    def write(self, name, text):
        path = self.tmp / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, **files):
        for name, text in files.items():
            self.write(name, text)
        self.git("add", "-A")
        self.git("commit", "-qm", "base")

    def snap(self, *paths, cwd=None):
        result = self.run_script("snapshot.sh", *paths, cwd=cwd)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout.strip(), r"^[0-9a-f]{40,64}$")
        return result.stdout.strip()

    def test_changes(self):
        self.commit(changed="a\n", gone="b\n")
        self.write("changed", "a2\n")
        (self.tmp / "gone").unlink()
        self.write("new", "n\n")
        self.write("secret.env", "not named\n")
        tree = self.snap("changed", "gone", "new")
        status = self.git("diff", "--name-status", "HEAD", tree).splitlines()
        self.assertEqual(sorted(status), ["A\tnew", "D\tgone", "M\tchanged"])

    def test_untracked_edit(self):
        self.commit(base="a\n")
        self.write("new", "one\n")
        before = self.snap("new")
        self.write("new", "two\n")
        self.assertNotEqual(before, self.snap("new"))

    def test_no_commits(self):
        self.write("first", "a\n")
        tree = self.snap("first")
        self.assertEqual(self.git("ls-tree", "--name-only", tree), "first")

    def test_no_args(self):
        result = self.run_script("snapshot.sh")
        self.assertEqual((result.returncode, result.stdout), (2, ""))

    def test_missing_path_fails(self):
        self.commit(base="a\n")
        result = self.run_script("snapshot.sh", "no-such-file")
        self.assertTrue((SCRIPTS / "snapshot.sh").exists())
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_index_untouched(self):
        self.commit(base="a\n")
        self.write("staged", "s\n")
        self.git("add", "staged")
        self.write("base", "a2\n")
        before = self.git("write-tree")
        self.snap("base")
        self.assertEqual(before, self.git("write-tree"))

    def test_spaces_and_subdir(self):
        self.commit(base="a\n")
        self.write("dir with space/a b.txt", "x\n")
        from_root = self.snap("dir with space/a b.txt")
        self.assertEqual(from_root, self.snap("a b.txt", cwd=self.tmp / "dir with space"))
        self.assertIn("dir with space/a b.txt", self.git("ls-tree", "-r", "--name-only", from_root))

    def test_unrelated_staged(self):
        self.commit(base="a\n")
        self.write("base", "a2\n")
        self.write("other", "x\n")
        approved = self.snap("base")
        self.git("add", "base")
        self.assertEqual(self.git("write-tree"), approved)
        self.git("add", "other")
        self.assertNotEqual(self.git("write-tree"), approved)


class ServedModelTests(TempCase):
    def log(self, *rows, agent="abc123"):
        path = self.tmp / "project" / "session" / "subagents" / f"agent-{agent}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = (json.dumps(row, separators=(",", ":")) for row in rows)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def requested(model):
        return {"type": "api-request", "params": {"model": model}}

    @staticmethod
    def answered(model, text="ok"):
        message = {"model": model, "role": "assistant", "content": [{"type": "text", "text": text}]}
        return {"type": "assistant", "message": message}

    def served(self, agent="abc123"):
        return self.run_script("served-model.sh", agent, self.tmp)

    def test_served_ignores_requested(self):
        quoted = '"message":{"model":"claude-fable-5-2"'
        self.log(self.requested("claude-fable-5-2"), self.answered("claude-opus-4-8", quoted))
        result = self.served()
        self.assertEqual((result.returncode, result.stdout.split()), (0, ["claude-opus-4-8"]))

    def test_served_mixed(self):
        self.log(
            self.answered("claude-opus-4-8"),
            self.answered("claude-fable-5-2"),
            self.answered("claude-opus-4-8"),
        )
        self.assertEqual(self.served().stdout.splitlines(), ["claude-fable-5-2", "claude-opus-4-8"])

    def test_served_missing(self):
        self.assertEqual(self.served().returncode, 3)

    def test_served_no_answer(self):
        self.log(self.requested("claude-fable-5-2"))
        self.assertEqual(self.served().returncode, 3)

    def test_served_rejects_wildcard_id(self):
        self.log(self.answered("claude-fable-5-2"))
        # MSYS expands a glob that matches in cwd, so use one that matches only the log name.
        result = self.served("abc*")
        self.assertEqual((result.returncode, result.stdout), (2, ""))


class CheckoutTests(unittest.TestCase):
    def test_lf(self):
        for name in ("snapshot.sh", "served-model.sh"):
            path = SCRIPTS / name
            self.assertTrue(path.exists(), name)
            self.assertNotIn(b"\r\n", path.read_bytes(), name)
            attr = subprocess.check_output(
                ["git", "check-attr", "eol", "--", path.relative_to(ROOT).as_posix()],
                cwd=ROOT, text=True,
            )
            self.assertTrue(attr.strip().endswith("eol: lf"), attr)


def frontmatter(path):
    return path.read_text(encoding="utf-8").split("---", 2)[1]


READ = ["Read", "Grep", "Glob"]
BUILD = [*READ, "Edit", "Write", "Bash", "PowerShell"]
REVIEW = [*READ, "Bash", "PowerShell"]
BROWSE = [*READ, "Bash", "ToolSearch", "mcp__obscura__*", "mcp__plugin_playwright_playwright__*"]
AGENTS = {
    "fable-oracle": ("fable", "high", 40, READ),
    "opus-specialist": ("opus", "high", 120, BUILD),
    "opus-reviewer": ("opus", "high", 80, REVIEW),
    "opus-reviewer-deep": ("opus", "xhigh", 100, REVIEW),
    "sonnet-worker": ("sonnet", "medium", 80, BUILD),
    "sonnet-ui-tester": ("sonnet", "medium", 120, BROWSE),
    "haiku-scout": ("haiku", "medium", 40, READ),
}


class AgentTests(unittest.TestCase):
    def agents(self):
        return {p.stem: yaml.safe_load(frontmatter(p)) for p in (CLAUDE / "agents").glob("*.md")}

    def test_agents(self):
        # An unknown or misspelt field is ignored without an error, so check the parsed values.
        found = {}
        for stem, meta in self.agents().items():
            self.assertEqual(meta["name"], stem)
            tools = [tool.strip() for tool in meta.get("tools", "").split(",") if tool.strip()]
            found[stem] = (meta.get("model"), meta.get("effort"), meta.get("maxTurns"), tools)
        self.assertEqual(found, AGENTS)

    def test_oracle_only_omits_claude_md(self):
        omits = [name for name, meta in self.agents().items() if meta.get("omitClaudeMd")]
        self.assertEqual(omits, ["fable-oracle"])

    def test_descriptions_quoted(self):
        for path in [*(CLAUDE / "agents").glob("*.md"), *ROOT.glob("plugins/*/skills/*/SKILL.md")]:
            self.assertRegex(frontmatter(path), r'(?m)^description: ".*"$', path.name)


class SkillTests(unittest.TestCase):
    def text(self):
        return (SKILL / "SKILL.md").read_text(encoding="utf-8")

    def test_skill_limits(self):
        self.assertLessEqual(len(self.text().splitlines()), 120)
        meta = yaml.safe_load(frontmatter(SKILL / "SKILL.md"))
        # Either key would hold for one turn only and then silently revert.
        self.assertFalse({"model", "effort"} & meta.keys())

    def test_triggers(self):
        description = yaml.safe_load(frontmatter(SKILL / "SKILL.md"))["description"]
        phrases = ("orchestrate", "orkestrera", "use subagents", "använd subagenter", "kör med agenter")
        for phrase in phrases:
            self.assertIn(f"'{phrase}'", description)
        self.assertNotIn("large task", description.lower())

    def test_skill_paths(self):
        paths = set(re.findall(r"\$\{CLAUDE_SKILL_DIR\}/([\w./-]+\.(?:md|sh))", self.text()))
        expected = {"references/briefs.md", "references/gates.md", "scripts/snapshot.sh", "scripts/served-model.sh"}
        self.assertEqual(paths, expected)
        for path in paths:
            self.assertTrue((SKILL / path).is_file(), path)

    def test_references_have_no_placeholders(self):
        # Claude Code substitutes variables in SKILL.md only.
        files = list((SKILL / "references").glob("*.md"))
        self.assertEqual(len(files), 2)
        for path in files:
            self.assertNotIn("${CLAUDE_", path.read_text(encoding="utf-8"), path.name)

    def test_roles_named(self):
        for name in AGENTS:
            self.assertIn(f"orchestrate:{name}`", self.text())
        for path in SKILL.rglob("*.md"):
            named = re.findall(r"orchestrate:([a-z][a-z-]+)", path.read_text(encoding="utf-8"))
            self.assertLessEqual(set(named), set(AGENTS), path.name)

    def test_brief_fields(self):
        path = SKILL / "references" / "briefs.md"
        self.assertTrue(path.exists())
        template = path.read_text(encoding="utf-8").split("```")[1]
        fields = re.findall(r"(?m)^(\w+):", template)
        self.assertEqual(fields, ["Goal", "Why", "Decided", "Freedom", "Files", "Traps", "Proof", "Risk"])


class PackageTests(unittest.TestCase):
    def test_versions(self):
        def version(path):
            return json.loads((ROOT / "plugins" / path).read_text(encoding="utf-8"))["version"]

        self.assertEqual(version("orchestrate-claude/.claude-plugin/plugin.json"), "2.0.0")
        self.assertEqual(version("orchestrate-codex/.codex-plugin/plugin.json"), "1.1.0")

    def test_codex_profile(self):
        found = {}
        for path in (ROOT / "plugins" / "orchestrate-codex" / "agents").glob("*.toml"):
            meta = tomllib.loads(path.read_text(encoding="utf-8"))
            found[meta["name"]] = (meta["model"], meta["model_reasoning_effort"])
        self.assertEqual(found, {
            "luna_scout": ("gpt-6-luna", "low"),
            "sol_worker": ("gpt-6.2-sol", "medium"),
            "astra_reviewer": ("gpt-6.2-astra", "high"),
        })

    def test_no_root_copy(self):
        self.assertFalse((ROOT / "skills").exists())

    def test_public_hygiene(self):
        listed = subprocess.check_output(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT, text=True, encoding="utf-8",
        )
        private = re.compile(r"[A-Za-z]:[\/]+Users[\/]|/c/Users/\w|[\w.+-]+@[\w-]+\.[A-Za-z]{2,}")
        for name in filter(None, listed.split("\0")):
            path = ROOT / name
            if path.is_file():
                self.assertNotRegex(path.read_text(encoding="utf-8"), private, name)


class ProcedureTests(TempCase):
    """Run the commands the skill tells the orchestrator to run, in a real repository."""

    def setUp(self):
        super().setUp()
        self.sh("git init -q && git config core.autocrlf false && git config commit.gpgsign false")
        self.sh("git config user.name t && git config user.email t@localhost")

    def sh(self, command):
        result = subprocess.run(
            [SH, "-c", command], cwd=self.tmp, env=ENV, capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def write(self, name, text="content\n"):
        (self.tmp / name).write_text(text, encoding="utf-8")

    def procedure(self):
        gates = (SKILL / "references" / "gates.md").read_text(encoding="utf-8")
        blocks = re.findall(r"```sh\n(.*?)```", gates.split("## Frozen diff", 1)[1], re.S)
        self.assertEqual(len(blocks), 2, "expected one block that lists paths and one that writes the diff")
        return [re.sub(r"(?m)^\s+", "", block) for block in blocks]

    def record_base(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        command = re.search(r"`(git rev-parse -q --verify HEAD[^`]*)`", skill)
        self.assertIsNotNone(command, "step 1 records no base")
        return self.sh(command.group(1))

    def freeze(self, base):
        list_paths, write_diff = self.procedure()
        paths = sorted(set(self.sh(list_paths).splitlines()))
        snapshot = self.run_script("snapshot.sh", *paths)
        self.assertEqual(snapshot.returncode, 0, snapshot.stderr)
        command = write_diff.replace("<base>", base).replace("<id>", snapshot.stdout.strip())
        self.sh(command.replace("<file>", ".git/frozen review.diff"))
        return paths, (self.tmp / ".git" / "frozen review.diff").read_text(encoding="utf-8")

    def test_diff_covers_work_committed_during_the_job(self):
        self.write("old")
        self.sh("git add old && git commit -qm base")
        base = self.record_base()
        self.sh("git mv old moved && git commit -qm 'committed during the job'")
        self.write("later")
        paths, diff = self.freeze(base)
        self.assertEqual(paths, ["later"])
        for name in ("old", "moved", "later"):
            self.assertIn(name, diff)

    def test_paths_unquoted_and_both_sides_of_rename(self):
        self.write("gammal")
        self.sh("git add gammal && git commit -qm base")
        base = self.record_base()
        self.sh("git mv gammal ny")
        self.write("räksmörgås fil.txt")
        paths, _ = self.freeze(base)
        self.assertEqual(paths, ["gammal", "ny", "räksmörgås fil.txt"])

    def test_file_removed_by_a_fix_drops_out(self):
        self.write("kept")
        self.sh("git add kept && git commit -qm base")
        base = self.record_base()
        self.write("kept", "changed\n")
        self.write("temporary")
        self.assertEqual(self.freeze(base)[0], ["kept", "temporary"])
        (self.tmp / "temporary").unlink()
        self.assertEqual(self.freeze(base)[0], ["kept"])

    def test_procedure_without_commits(self):
        self.write("first")
        paths, diff = self.freeze(self.record_base())
        self.assertEqual(paths, ["first"])
        self.assertIn("first", diff)
