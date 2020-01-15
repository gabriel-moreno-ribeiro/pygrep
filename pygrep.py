#!/usr/bin/env python3
"""pygrep - a grep clone written from scratch in Python.

Supports the most used GNU grep flags: regex/fixed-string search, recursive
walks, context lines, inversion, counting, line numbers, colored output and
grep-compatible exit codes (0 = match, 1 = no match, 2 = error).
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import re
import sys
from dataclasses import dataclass, field
from typing import IO, Iterable, Iterator, List, Optional, Sequence, Tuple

RED = "\033[1;31m"
MAGENTA = "\033[35m"
GREEN = "\033[32m"
CYAN = "\033[36m"
RESET = "\033[0m"


@dataclass
class Options:
    pattern: str
    ignore_case: bool = False
    invert: bool = False
    fixed: bool = False
    word: bool = False
    line_regexp: bool = False
    count: bool = False
    files_with_matches: bool = False
    files_without_match: bool = False
    line_number: bool = False
    only_matching: bool = False
    recursive: bool = False
    no_filename: bool = False
    with_filename: Optional[bool] = None
    before: int = 0
    after: int = 0
    color: bool = False
    max_count: Optional[int] = None
    quiet: bool = False
    include: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)


def compile_pattern(opts: Options) -> re.Pattern[str]:
    pat = re.escape(opts.pattern) if opts.fixed else opts.pattern
    if opts.word:
        pat = rf"(?<![\w]){pat}(?![\w])"
    if opts.line_regexp:
        pat = rf"^(?:{pat})$"
    flags = re.IGNORECASE if opts.ignore_case else 0
    try:
        return re.compile(pat, flags)
    except re.error as exc:
        raise ValueError(f"invalid regular expression: {exc}") from exc


def _glob_match(name: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch.fnmatch(name, p) for p in patterns)


def iter_files(paths: Sequence[str], opts: Options) -> Iterator[Tuple[str, Optional[str]]]:
    """Yield (display_name, real_path). real_path is None for stdin."""
    if not paths:
        paths = ["-"] if not opts.recursive else ["."]
    for path in paths:
        if path == "-":
            yield "(standard input)", None
            continue
        if os.path.isdir(path):
            if not opts.recursive:
                yield path, "__DIR__"
                continue
            for root, dirs, files in os.walk(path):
                dirs.sort()
                dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules")]
                for name in sorted(files):
                    if opts.include and not _glob_match(name, opts.include):
                        continue
                    if opts.exclude and _glob_match(name, opts.exclude):
                        continue
                    full = os.path.join(root, name)
                    yield full, full
        else:
            yield path, path


def read_lines(fh: IO[str]) -> Iterator[str]:
    for line in fh:
        yield line.rstrip("\n").rstrip("\r")


def highlight(line: str, regex: re.Pattern[str]) -> str:
    return regex.sub(lambda m: f"{RED}{m.group(0)}{RESET}" if m.group(0) else "", line)


def search_lines(lines: Iterable[str], regex: re.Pattern[str], opts: Options) -> Iterator[Tuple[int, str, bool]]:
    """Yield (lineno, text, is_match) for every line that should be printed."""
    before: List[Tuple[int, str]] = []
    after_left = 0
    matches = 0
    for idx, line in enumerate(lines, start=1):
        hit = bool(regex.search(line)) != opts.invert
        if hit:
            matches += 1
            for b in before:
                yield b[0], b[1], False
            before.clear()
            yield idx, line, True
            after_left = opts.after
            if opts.max_count is not None and matches >= opts.max_count:
                return
        elif after_left > 0:
            yield idx, line, False
            after_left -= 1
        elif opts.before:
            before.append((idx, line))
            if len(before) > opts.before:
                before.pop(0)


def format_line(name: Optional[str], lineno: int, text: str, is_match: bool,
                regex: re.Pattern[str], opts: Options) -> str:
    sep = ":" if is_match else "-"
    parts = []
    if name is not None:
        parts.append(f"{MAGENTA}{name}{RESET}{CYAN}{sep}{RESET}" if opts.color else f"{name}{sep}")
    if opts.line_number:
        parts.append(f"{GREEN}{lineno}{RESET}{CYAN}{sep}{RESET}" if opts.color else f"{lineno}{sep}")
    body = highlight(text, regex) if (opts.color and is_match and not opts.invert) else text
    return "".join(parts) + body


def grep_stream(fh: IO[str], display: str, show_name: bool, regex: re.Pattern[str],
                opts: Options, out: IO[str]) -> bool:
    """Search one stream. Returns True if at least one line matched."""
    name = display if show_name else None
    matched = False
    count = 0
    last_printed = 0
    for lineno, text, is_match in search_lines(read_lines(fh), regex, opts):
        if is_match:
            matched = True
            count += 1
        if opts.quiet:
            return True
        if opts.count or opts.files_with_matches or opts.files_without_match:
            continue
        if opts.only_matching:
            if is_match and not opts.invert:
                for m in regex.finditer(text):
                    if m.group(0):
                        out.write(format_line(name, lineno, m.group(0), True, regex, opts) + "\n")
            continue
        if (opts.before or opts.after) and last_printed and lineno > last_printed + 1:
            out.write("--\n")
        out.write(format_line(name, lineno, text, is_match, regex, opts) + "\n")
        last_printed = lineno
    if opts.count:
        prefix = f"{display}:" if show_name else ""
        out.write(f"{prefix}{count}\n")
    elif opts.files_with_matches and matched:
        out.write(f"{display}\n")
    elif opts.files_without_match and not matched:
        out.write(f"{display}\n")
    return matched


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pygrep", add_help=False,
                                description="Search for PATTERN in each FILE (or stdin).")
    p.add_argument("pattern")
    p.add_argument("files", nargs="*")
    p.add_argument("-i", "--ignore-case", action="store_true")
    p.add_argument("-v", "--invert-match", dest="invert", action="store_true")
    p.add_argument("-F", "--fixed-strings", dest="fixed", action="store_true")
    p.add_argument("-w", "--word-regexp", dest="word", action="store_true")
    p.add_argument("-x", "--line-regexp", dest="line_regexp", action="store_true")
    p.add_argument("-c", "--count", action="store_true")
    p.add_argument("-l", "--files-with-matches", action="store_true")
    p.add_argument("-L", "--files-without-match", action="store_true")
    p.add_argument("-n", "--line-number", action="store_true")
    p.add_argument("-o", "--only-matching", action="store_true")
    p.add_argument("-r", "-R", "--recursive", action="store_true")
    p.add_argument("-h", "--no-filename", action="store_true")
    p.add_argument("-H", "--with-filename", action="store_true", default=None)
    p.add_argument("-A", "--after-context", dest="after", type=int, default=0, metavar="N")
    p.add_argument("-B", "--before-context", dest="before", type=int, default=0, metavar="N")
    p.add_argument("-C", "--context", type=int, default=0, metavar="N")
    p.add_argument("-m", "--max-count", type=int, default=None, metavar="N")
    p.add_argument("-q", "--quiet", "--silent", action="store_true")
    p.add_argument("--color", "--colour", choices=["never", "always", "auto"], default="auto")
    p.add_argument("--include", action="append", default=[], metavar="GLOB")
    p.add_argument("--exclude", action="append", default=[], metavar="GLOB")
    p.add_argument("--help", action="help")
    return p


def run(argv: Sequence[str], stdin: IO[str] = sys.stdin, out: IO[str] = sys.stdout,
        err: IO[str] = sys.stderr) -> int:
    ns = build_parser().parse_args(list(argv))
    opts = Options(
        pattern=ns.pattern, ignore_case=ns.ignore_case, invert=ns.invert, fixed=ns.fixed,
        word=ns.word, line_regexp=ns.line_regexp, count=ns.count,
        files_with_matches=ns.files_with_matches, files_without_match=ns.files_without_match,
        line_number=ns.line_number, only_matching=ns.only_matching, recursive=ns.recursive,
        no_filename=ns.no_filename, with_filename=ns.with_filename,
        before=max(ns.before, ns.context), after=max(ns.after, ns.context),
        color=(ns.color == "always" or (ns.color == "auto" and hasattr(out, "isatty") and out.isatty())),
        max_count=ns.max_count, quiet=ns.quiet, include=ns.include, exclude=ns.exclude,
    )
    try:
        regex = compile_pattern(opts)
    except ValueError as exc:
        err.write(f"pygrep: {exc}\n")
        return 2

    files = list(iter_files(ns.files, opts))
    multiple = len(files) > 1 or opts.recursive
    show_name = (opts.with_filename is True) or (multiple and not opts.no_filename)
    any_match = False
    had_error = False
    for display, real in files:
        if real == "__DIR__":
            err.write(f"pygrep: {display}: Is a directory\n")
            had_error = True
            continue
        try:
            if real is None:
                matched = grep_stream(stdin, display, show_name, regex, opts, out)
            else:
                with open(real, "r", encoding="utf-8", errors="replace") as fh:
                    matched = grep_stream(fh, display, show_name, regex, opts, out)
        except OSError as exc:
            err.write(f"pygrep: {display}: {exc.strerror}\n")
            had_error = True
            continue
        any_match = any_match or matched
        if opts.quiet and matched:
            return 0
    if had_error and not any_match:
        return 2
    return 0 if any_match else 1


def main() -> None:
    sys.exit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
