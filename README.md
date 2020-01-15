# pygrep

A `grep` clone written from scratch in Python, with no third-party dependencies.

I built this to understand how a real command-line search tool is put together:
argument parsing, streaming input, context windows, recursive directory walks,
colored output and POSIX exit codes.

## Features

- Regular expressions (Python `re` syntax) or fixed strings (`-F`)
- `-i` ignore case, `-v` invert, `-w` whole words, `-x` whole lines
- `-n` line numbers, `-c` count, `-o` only the matching part
- `-l` / `-L` list files with / without matches
- `-A N`, `-B N`, `-C N` context lines with `--` group separators
- `-r` recursive search with `--include` / `--exclude` globs
- `-m N` stop after N matches, `-q` quiet mode
- `--color=always|never|auto` highlighting
- grep-compatible exit codes: `0` match, `1` no match, `2` error

## Usage

```sh
python pygrep.py -rn "TODO" src/
python pygrep.py -i -C 2 "error" server.log
cat file.txt | python pygrep.py -c "^#"
python pygrep.py -o "[0-9]+" data.csv
```

## Running the tests

```sh
python -m unittest discover -s tests -v
```

## How it works

1. `build_parser()` turns argv into an `Options` dataclass.
2. `compile_pattern()` wraps the pattern for `-F`, `-w`, `-x` and `-i`.
3. `iter_files()` expands paths (stdin, files or a recursive walk).
4. `search_lines()` is a generator that keeps a small ring buffer of "before"
   lines and a countdown of "after" lines, so context is emitted lazily without
   loading whole files into memory.
5. `grep_stream()` formats each emitted line (prefixes, colors, separators) and
   handles the summary modes (`-c`, `-l`, `-L`, `-q`).

## License

MIT
