import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygrep  # noqa: E402


def run(args, stdin=""):
    out, err = io.StringIO(), io.StringIO()
    code = pygrep.run(args, stdin=io.StringIO(stdin), out=out, err=err)
    return code, out.getvalue(), err.getvalue()


SAMPLE = "alpha\nbeta\nGamma\ndelta\nalphabet\n"


class StdinTests(unittest.TestCase):
    def test_basic_match(self):
        code, out, _ = run(["alpha"], SAMPLE)
        self.assertEqual(code, 0)
        self.assertEqual(out, "alpha\nalphabet\n")

    def test_no_match_exit_code(self):
        code, out, _ = run(["zzz"], SAMPLE)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")

    def test_ignore_case(self):
        _, out, _ = run(["-i", "gamma"], SAMPLE)
        self.assertEqual(out, "Gamma\n")

    def test_invert(self):
        _, out, _ = run(["-v", "a"], SAMPLE)
        self.assertEqual(out, "")
        _, out, _ = run(["-v", "alpha"], SAMPLE)
        self.assertEqual(out, "beta\nGamma\ndelta\n")

    def test_word(self):
        _, out, _ = run(["-w", "alpha"], SAMPLE)
        self.assertEqual(out, "alpha\n")

    def test_line_regexp(self):
        _, out, _ = run(["-x", "beta"], "beta\nbetamax\n")
        self.assertEqual(out, "beta\n")

    def test_count(self):
        _, out, _ = run(["-c", "a"], SAMPLE)
        self.assertEqual(out, "5\n")

    def test_line_numbers(self):
        _, out, _ = run(["-n", "delta"], SAMPLE)
        self.assertEqual(out, "4:delta\n")

    def test_fixed_strings(self):
        _, out, _ = run(["-F", "a.b"], "a.b\naxb\n")
        self.assertEqual(out, "a.b\n")

    def test_only_matching(self):
        _, out, _ = run(["-o", r"\d+"], "a1b22c333\n")
        self.assertEqual(out, "1\n22\n333\n")

    def test_context(self):
        text = "1\n2\n3\n4\n5\n6\n7\n"
        _, out, _ = run(["-n", "-C", "1", "4"], text)
        self.assertEqual(out, "3-3\n4:4\n5-5\n")
        _, out, _ = run(["-A", "1", "^[15]$"], text)
        self.assertEqual(out, "1\n2\n--\n5\n6\n")

    def test_max_count(self):
        _, out, _ = run(["-m", "1", "a"], SAMPLE)
        self.assertEqual(out, "alpha\n")

    def test_quiet(self):
        code, out, _ = run(["-q", "beta"], SAMPLE)
        self.assertEqual((code, out), (0, ""))

    def test_bad_regex(self):
        code, _, err = run(["("], SAMPLE)
        self.assertEqual(code, 2)
        self.assertIn("invalid regular expression", err)

    def test_color(self):
        _, out, _ = run(["--color=always", "ph"], "alpha\n")
        self.assertEqual(out, f"al{pygrep.RED}ph{pygrep.RESET}a\n")


class FileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        os.makedirs(os.path.join(self.root, "sub"))
        self._write("a.txt", "hello world\nbye\n")
        self._write("b.py", "print('hello')\n")
        self._write(os.path.join("sub", "c.txt"), "HELLO again\n")

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, rel, content):
        with open(os.path.join(self.root, rel), "w") as fh:
            fh.write(content)

    def test_single_file_no_prefix(self):
        _, out, _ = run(["hello", os.path.join(self.root, "a.txt")])
        self.assertEqual(out, "hello world\n")

    def test_multiple_files_prefix(self):
        a, b = os.path.join(self.root, "a.txt"), os.path.join(self.root, "b.py")
        _, out, _ = run(["hello", a, b])
        self.assertEqual(out, f"{a}:hello world\n{b}:print('hello')\n")

    def test_recursive_and_include(self):
        _, out, _ = run(["-ri", "--include=*.txt", "hello", self.root])
        lines = sorted(out.splitlines())
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(l.endswith("hello world") or l.endswith("HELLO again") for l in lines))

    def test_files_with_matches(self):
        _, out, _ = run(["-rl", "hello", self.root])
        self.assertEqual(sorted(os.path.basename(l) for l in out.splitlines()), ["a.txt", "b.py"])

    def test_files_without_match(self):
        _, out, _ = run(["-rL", "hello", self.root])
        self.assertEqual([os.path.basename(l) for l in out.splitlines()], ["c.txt"])

    def test_missing_file(self):
        code, _, err = run(["x", os.path.join(self.root, "nope")])
        self.assertEqual(code, 2)
        self.assertIn("nope", err)

    def test_directory_without_recursive(self):
        code, _, err = run(["x", self.root])
        self.assertEqual(code, 2)
        self.assertIn("Is a directory", err)


if __name__ == "__main__":
    unittest.main()
