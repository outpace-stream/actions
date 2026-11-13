"""Tests for identifier-hygiene/check_identifiers.py.

Each test builds a throwaway git repository and runs the script against it
from that repository's working directory, as the action and hooks do.
"""
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "identifier-hygiene", "check_identifiers.py")

# High-entropy 40-hex built at runtime so this file itself never carries one.
REAL = "".join("9f3a1c7e5b2d8046"[(i * 7 + 3) % 16] for i in range(20)) + \
       "".join("e1b4d7a03c6f9285"[(i * 5 + 1) % 16] for i in range(20))
PLACEHOLDER = "0123456789abcdef0123456789abcdef01234567"


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


class CheckIdentifiers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        git(self.repo, "init", "-q")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, path, text, add=True):
        full = os.path.join(self.repo, path)
        os.makedirs(os.path.dirname(full) or self.repo, exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)
        if add:
            git(self.repo, "add", path)

    def run_script(self, *args):
        return subprocess.run([sys.executable, SCRIPT, *args], cwd=self.repo,
                              capture_output=True, text=True)

    def test_real_value_is_rejected(self):
        self.assertEqual(len(set(REAL)), 16)
        self.write("notes.md", f"id {REAL}\n")
        r = self.run_script()
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("notes.md:1", r.stderr)

    def test_placeholder_passes(self):
        self.write("notes.md", f"id {PLACEHOLDER}\n")
        self.assertEqual(self.run_script().returncode, 0)

    def test_default_allowlist(self):
        self.write("notes.md", f"id {REAL}\n")
        self.write("tools/hygiene/allowed-identifiers.txt", f"{REAL}  fixture digest\n")
        self.assertEqual(self.run_script().returncode, 0)

    def test_custom_allowlist(self):
        self.write("notes.md", f"id {REAL}\n")
        self.write(".hygiene-allow", f"{REAL}  fixture digest\n")
        self.assertEqual(self.run_script().returncode, 1)
        r = self.run_script("--allowlist", ".hygiene-allow")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_failure_names_the_allowlist(self):
        self.write("notes.md", f"id {REAL}\n")
        r = self.run_script("--allowlist", "custom/allow.txt")
        self.assertIn("custom/allow.txt", r.stderr)

    def test_registry_is_blocked(self):
        self.write("acestream-ids.txt", f"cid1 = {PLACEHOLDER}\n")
        r = self.run_script()
        self.assertEqual(r.returncode, 1)
        self.assertIn("registry", r.stderr)

    def test_staged_scans_index_not_worktree(self):
        self.write("notes.md", f"id {REAL}\n")
        self.write("notes.md", f"id {PLACEHOLDER}\n", add=False)
        self.assertEqual(self.run_script("--staged").returncode, 1)
        self.assertEqual(self.run_script().returncode, 0)

    def test_allowlist_with_staged(self):
        self.write("notes.md", f"id {REAL}\n")
        self.write("allow.txt", f"{REAL}  fixture digest\n")
        r = self.run_script("--allowlist", "allow.txt", "--staged")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_outside_git_repository(self):
        with tempfile.TemporaryDirectory() as bare:
            r = subprocess.run([sys.executable, SCRIPT], cwd=bare,
                               capture_output=True, text=True,
                               env={**os.environ, "GIT_CEILING_DIRECTORIES": os.path.dirname(bare)})
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
