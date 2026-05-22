# Compiladores

Projeto educacional com dois blocos principais:

- `compilador.py`: analisador lexico e sintatico para a linguagem LangC#.
- `atividade_sintatico.py` e `web/`: resolucao da atividade de analise sintatica LL(1).

## Estrutura

```text
Compiladores/
├── README.md
├── src/
│   ├── compilador.py
│   └── atividade_sintatico.py
├── web/
│   ├── index.html
│   └── assets/
│       ├── css/
│       ├── js/
│       └── images/
├── examples/
│   ├── langc/
│   └── ll1/
├── outputs/
│   ├── cache/
│   └── tokens/
├── docs/
│   ├── manuals/
│   └── activities/
└── archives/
```

## Pastas

- `src/`: codigos-fonte Python.
- `web/`: pagina HTML da atividade LL(1), com CSS, JavaScript e imagens separados em `assets/`.
- `examples/langc/`: arquivos `.txt` usados como entrada do compilador LangC#.
- `examples/ll1/`: exemplo de entrada da atividade sintatica LL(1).
- `outputs/tokens/`: arquivos JSON gerados pelo analisador lexico.
- `outputs/cache/`: caches gerados anteriormente pelo Python.
- `docs/manuals/`: manual e especificacao da linguagem.
- `docs/activities/`: PDFs das atividades.
- `archives/`: arquivos compactados recebidos ou de backup.

## Como executar

Compilador LangC#:

```bash
python src/compilador.py
```

O programa lista os arquivos em `examples/langc/` e salva os tokens gerados em `outputs/tokens/`.

Atividade sintatica LL(1):

```bash
python src/atividade_sintatico.py examples/ll1/atividade_sintatico_exemplo.txt
```

Site da atividade:

```text
web/index.html
```

Abra esse arquivo no navegador para usar a interface visual.

## Observacoes

- Nao ha dependencias externas obrigatorias.
- `__pycache__/` e outros arquivos gerados podem ser recriados automaticamente pelo Python.
- Os JSONs em `outputs/tokens/` representam saidas geradas a partir dos exemplos em `examples/langc/`.
