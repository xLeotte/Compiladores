"""
Atividade de Compiladores - Analise Sintatica LL(1)

Resolucao baseada no arquivo:
AtividadeSintatico - Pagina1.pdf

Gramatica:
1-S -> cAa
2-A -> cB
3-A -> B
4-B -> bcB
5-B -> epsilon

Sentenca usada no exemplo resolvido:
cbca
"""

import argparse
from pathlib import Path


EPSILON = "epsilon"
FIM = "$"

TERMINAIS = {"a", "b", "c", FIM}
NAO_TERMINAIS = {"S", "A", "B"}


PRODUCOES = {
    1: ("S", ["c", "A", "a"]),
    2: ("A", ["c", "B"]),
    3: ("A", ["B"]),
    4: ("B", ["b", "c", "B"]),
    5: ("B", []),
}


FIRST_FOLLOW_RESOLVIDO = [
    ["producao", "first", "follow"],
    ["1-S -> cAa", "c", FIM],
    ["2-A -> cB", "c", ""],
    ["3-A -> B", f"b, {EPSILON}", "a"],
    ["4-B -> bcB", "b", ""],
    ["5-B -> epsilon", EPSILON, "a"],
]


TABELA_PARSER_RESOLVIDA = [
    ["tabela parser", "a", "b", "c", EPSILON, FIM],
    ["S", "", "", "1", "", ""],
    ["A", "3 (follow)", "3", "2", "3 (didatico)", ""],
    ["B", "5 (follow)", "4", "", "5 (didatico)", ""],
]


PILHA_RESOLVIDA = [
    ["pilha", "c", "b", "c", "a", "", ""],
    ["", "", "b", "", "", "", ""],
    ["c", "", "c", "c", "", "", ""],
    ["A", "A", "B", "B", "B pq tem epsilon", "", ""],
    ["a", "a", "a", "a", "a", "a", ""],
    [FIM, FIM, FIM, FIM, FIM, FIM, "terminou de esvaziar a pilha"],
    ["c,c", "A,a", "b,b", "c,c", "B,a", "a,a", ""],
]


TABELA_ANALISE = {
    ("S", "c"): 1,
    ("A", "c"): 2,
    ("A", "b"): 3,
    ("A", "a"): 3,
    ("B", "b"): 4,
    ("B", "a"): 5,
}


def formatar_producao(numero):
    esquerda, direita = PRODUCOES[numero]

    if direita:
        return f"{esquerda} -> {''.join(direita)}"

    return f"{esquerda} -> {EPSILON}"


def mostrar_tabela(titulo, linhas):
    larguras = []

    for coluna in range(len(linhas[0])):
        larguras.append(max(len(linha[coluna]) for linha in linhas))

    print(f"\n{titulo}")

    for indice, linha in enumerate(linhas):
        texto = " | ".join(
            valor.ljust(larguras[coluna])
            for coluna, valor in enumerate(linha)
        )
        print(texto)

        if indice == 0:
            print("-" * len(texto))


def mostrar_resolucao_do_pdf():
    mostrar_tabela("Tabela FIRST/FOLLOW resolvida:", FIRST_FOLLOW_RESOLVIDO)
    mostrar_tabela("Tabela parser resolvida:", TABELA_PARSER_RESOLVIDA)
    mostrar_tabela("Pilha resolvida para cbca:", PILHA_RESOLVIDA)


def preparar_entrada(sentenca):
    sentenca = "".join(sentenca.split()).lower()

    if sentenca.endswith(FIM):
        sentenca = sentenca[:-1]

    for simbolo in sentenca:
        if simbolo not in {"a", "b", "c"}:
            raise ValueError(f"Simbolo invalido na entrada: {simbolo}")

    return list(sentenca + FIM)


def obter_sentenca(entrada):
    caminho = Path(entrada)

    if caminho.is_file():
        return caminho.read_text(encoding="utf-8"), caminho.name

    return entrada, entrada


def mostrar_passo(numero, pilha, entrada, posicao, acao):
    pilha_texto = "".join(reversed(pilha))
    entrada_texto = "".join(entrada[posicao:])

    print(f"{numero:<5} | {pilha_texto:<8} | {entrada_texto:<8} | {acao}")


def analisar(sentenca):
    entrada = preparar_entrada(sentenca)
    pilha = [FIM, "S"]
    posicao = 0
    passo = 1

    print("\nAnalise da sentenca:")
    print("Passo | Pilha    | Entrada  | Acao")
    print("-" * 45)

    while pilha:
        topo = pilha[-1]
        simbolo = entrada[posicao]

        if topo == FIM and simbolo == FIM:
            print("\nSentenca aceita.")
            return True

        if topo in TERMINAIS:
            if topo != simbolo:
                print(f"\nErro sintatico: esperado {topo}, encontrado {simbolo}.")
                return False

            mostrar_passo(passo, pilha, entrada, posicao, f"Consome {topo}")
            pilha.pop()
            posicao += 1
            passo += 1

        elif topo in NAO_TERMINAIS:
            numero_producao = TABELA_ANALISE.get((topo, simbolo))

            if numero_producao is None:
                print(f"\nErro sintatico: nao existe M({topo}, {simbolo}).")
                return False

            mostrar_passo(
                passo,
                pilha,
                entrada,
                posicao,
                f"Usa {numero_producao}: {formatar_producao(numero_producao)}",
            )

            pilha.pop()
            _, direita = PRODUCOES[numero_producao]

            for simbolo_producao in reversed(direita):
                pilha.append(simbolo_producao)

            passo += 1

        else:
            print(f"\nErro sintatico: simbolo desconhecido {topo}.")
            return False

    print("\nErro sintatico: pilha vazia antes do fim da entrada.")
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Parser LL(1) conforme a resolucao do PDF da atividade."
    )
    parser.add_argument("entrada", nargs="?", default="cbca")
    args = parser.parse_args()

    mostrar_resolucao_do_pdf()

    try:
        sentenca, origem = obter_sentenca(args.entrada)
        print(f"\nValidando sentenca: {origem}")
        sucesso = analisar(sentenca)
    except (OSError, ValueError) as erro:
        print(f"\nErro: {erro}")
        return 1

    if sucesso:
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
