# pygrep

> 🇺🇸 [English version below](#english)

O primeiro da série. Eu queria entender como o `grep` funciona por dentro antes de sair usando ferramenta de busca como caixa preta, então reescrevi ele em Python puro, sem nenhuma dependência. Foi mais trabalho do que eu esperava: o grep "de verdade" tem dezenas de flags e cada uma interage com as outras (tenta combinar `-c` com `-v` e `-m` e vê o que acontece).

```sh
python pygrep.py -rn "TODO" src/
python pygrep.py -i -C 2 "error" server.log
cat file.txt | python pygrep.py -c "^#"
python pygrep.py -o "[0-9]+" data.csv
```

O que ele faz:

- regex (sintaxe do `re`) ou string fixa com `-F`
- `-i`, `-v`, `-w`, `-x` (ignora caixa, inverte, palavra inteira, linha inteira)
- `-n`, `-c`, `-o`, `-l`, `-L`, `-m N`, `-q`
- contexto `-A`, `-B`, `-C` com o separador `--` entre grupos
- `-r` recursivo com `--include` / `--exclude`
- cores (`--color=auto|always|never`) e os mesmos códigos de saída do grep: 0 achou, 1 não achou, 2 erro

A parte que eu mais gostei de fazer foi o contexto: `search_lines()` é um generator que guarda um ring buffer pequeno com as linhas "antes" e uma contagem regressiva das linhas "depois", então o arquivo nunca é carregado inteiro na memoria. Parece detalhe, mas é o que faz um `grep -C 3` num log de 2 GB funcionar.

Testes: `python -m unittest discover -s tests -v`.

---

## English

The first one of the series. I wanted to understand how `grep` works on the inside before going around using search tools as a black box, so I rewrote it in pure Python, with no dependencies at all. It was more work than I expected: the "real" grep has dozens of flags and each one interacts with the others (try combining `-c` with `-v` and `-m` and see what happens).

```sh
python pygrep.py -rn "TODO" src/
python pygrep.py -i -C 2 "error" server.log
cat file.txt | python pygrep.py -c "^#"
python pygrep.py -o "[0-9]+" data.csv
```

What it does:

- regex (`re` syntax) or fixed string with `-F`
- `-i`, `-v`, `-w`, `-x` (ignore case, invert, whole word, whole line)
- `-n`, `-c`, `-o`, `-l`, `-L`, `-m N`, `-q`
- context `-A`, `-B`, `-C` with the `--` separator between groups
- recursive `-r` with `--include` / `--exclude`
- colors (`--color=auto|always|never`) and the same exit codes as grep: 0 found, 1 not found, 2 error

The part I enjoyed the most was the context: `search_lines()` is a generator that keeps a small ring buffer with the "before" lines and a countdown of the "after" lines, so the file is never loaded whole into memory. Looks like a detail, but it's what makes a `grep -C 3` on a 2 GB log actually work.

Tests: `python -m unittest discover -s tests -v`.

MIT.
