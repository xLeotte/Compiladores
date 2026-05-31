# Compiladores

Projeto educacional com dois blocos principais:

- `compilador.py`: analisador lexico e analisador sintatico preditivo tabular para a linguagem LangC#.
- `atividade_sintatico.py` e `web/`: resolucao da atividade de analise sintatica LL(1).
- `atividade_semantico.py`: resolucao separada da atividade de analise semantica.

## Estrutura

```text
Compiladores/
├── README.md
├── src/
│   ├── compilador.py
│   ├── atividade_sintatico.py
│   └── atividade_semantico.py
├── web/
│   ├── index.html
│   └── assets/
│       ├── css/
│       ├── js/
│       └── images/
├── examples/
│   ├── langc/
│   ├── semantico/
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
- `examples/semantico/`: exemplos da atividade semantica com `const`.
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
Durante a analise, a saida mostra codigo do token, token, lexema, linha e a pilha do analisador sintatico a cada passo.

As tabelas da E4 ficam em:

```text
docs/tabelas_e4.md
```

O analisador tambem implementa a acao semantica de `const` descrita em `docs/activities/AcoesSemantico.pdf`: constantes globais entram na tabela de simbolos como categoria `constante` e nao podem receber nova atribuicao.

Atividade sintatica LL(1):

```bash
python src/atividade_sintatico.py examples/ll1/atividade_sintatico_exemplo.txt
```

Atividade semantica:

```bash
python src/atividade_semantico.py examples/semantico/6_erro_semantico_const.txt
```

Para validar um exemplo sem erro semantico:

```bash
python src/atividade_semantico.py examples/semantico/5_const_ok.txt
```

Site da atividade:

```text
web/index.html
```

Abra esse arquivo no navegador para usar a interface visual.

## Observacoes

- Nao ha dependencias externas obrigatorias.
- `__pycache__/` e outros arquivos gerados podem ser recriados automaticamente pelo Python.
- Os JSONs em `outputs/tokens/` representam saidas geradas pelos scripts durante os testes.
