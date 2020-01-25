# pygrep

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

**EN:** a `grep` clone in dependency-free Python, written to learn how a real search tool is put together: argument parsing that mirrors GNU grep (including how the flags interact), streaming input with a small ring buffer for `-A/-B/-C` context so huge files never sit in memory, recursive walks with include/exclude globs, colored output and grep-compatible exit codes. Run the tests with `python -m unittest discover -s tests -v`. MIT.
