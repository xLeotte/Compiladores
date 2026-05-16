"""
Atividade de Compiladores - Parser LL(1)

Gramatica:
1) S -> cAa
2) A -> cB
3) A -> B
4) B -> bcB
5) B -> epsilon

Sentenca usada como exemplo:
cbca
"""

import argparse
from pathlib import Path


TERMINAIS = {"a", "b", "c", "$"}
NAO_TERMINAIS = {"S", "A", "B"}


PRODUCOES = {
    1: ("S", ["c", "A", "a"]),
    2: ("A", ["c", "B"]),
    3: ("A", ["B"]),
    4: ("B", ["b", "c", "B"]),
    5: ("B", []),  # epsilon
}


TABELA = {
    ("S", "c"): 1,
    ("A", "c"): 2,
    ("A", "b"): 3,
    ("A", "a"): 3,
    ("B", "b"): 4,
    ("B", "a"): 5,
}


FIRST = {
    "S": ["c"],
    "A": ["c", "b", "epsilon"],
    "B": ["b", "epsilon"],
}


FOLLOW = {
    "S": ["$"],
    "A": ["a"],
    "B": ["a"],
}


def formatar_producao(numero):
    esquerda, direita = PRODUCOES[numero]
    if direita:
        return f"{esquerda} -> {''.join(direita)}"
    return f"{esquerda} -> epsilon"


def formatar_conjunto(simbolos):
    return "{ " + ", ".join(simbolos) + " }"


def mostrar_tabela_first_follow():
    linhas = [["Simbolo", "FIRST", "FOLLOW"]]

    for simbolo in ["S", "A", "B"]:
        linhas.append(
            [
                simbolo,
                formatar_conjunto(FIRST[simbolo]),
                formatar_conjunto(FOLLOW[simbolo]),
            ]
        )

    larguras = []
    for coluna in range(len(linhas[0])):
        largura = max(len(linha[coluna]) for linha in linhas)
        larguras.append(largura)

    print("\nTabela FIRST/FOLLOW:")
    for indice, linha in enumerate(linhas):
        texto = " | ".join(
            valor.ljust(larguras[coluna])
            for coluna, valor in enumerate(linha)
        )
        print(texto)

        if indice == 0:
            print("-" * len(texto))


def mostrar_tabela_parser():
    colunas = ["a", "b", "c", "$"]
    linhas = [[" "] + colunas]

    for nao_terminal in ["S", "A", "B"]:
        linha = [nao_terminal]

        for terminal in colunas:
            numero_producao = TABELA.get((nao_terminal, terminal))
            if numero_producao is None:
                linha.append("-")
            else:
                linha.append(formatar_producao(numero_producao))

        linhas.append(linha)

    larguras = []
    for coluna in range(len(linhas[0])):
        largura = max(len(linha[coluna]) for linha in linhas)
        larguras.append(largura)

    print("\nTabela de parsing M(X, t):")
    for indice, linha in enumerate(linhas):
        texto = " | ".join(
            valor.ljust(larguras[coluna])
            for coluna, valor in enumerate(linha)
        )
        print(texto)

        if indice == 0:
            print("-" * len(texto))


def preparar_entrada(sentenca):
    sentenca = "".join(sentenca.split()).lower()

    if sentenca.endswith("$"):
        sentenca = sentenca[:-1]

    for simbolo in sentenca:
        if simbolo not in {"a", "b", "c"}:
            raise ValueError(f"Simbolo invalido na entrada: {simbolo}")

    return list(sentenca + "$")


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
    pilha = ["$", "S"]
    posicao = 0
    passo = 1

    print("Passo | Pilha    | Entrada  | Acao")
    print("-" * 45)

    while pilha:
        topo = pilha[-1]
        simbolo = entrada[posicao]

        if topo == "$" and simbolo == "$":
            print("\nSentenca aceita.")
            return True

        if topo in TERMINAIS:
            if topo == simbolo:
                mostrar_passo(passo, pilha, entrada, posicao, f"Consome {topo}")
                pilha.pop()
                posicao += 1
                passo += 1
            else:
                print(f"\nErro sintatico: esperado {topo}, encontrado {simbolo}.")
                return False

        elif topo in NAO_TERMINAIS:
            numero_producao = TABELA.get((topo, simbolo))

            if numero_producao is None:
                print(f"\nErro sintatico: nao existe M({topo}, {simbolo}).")
                return False

            mostrar_passo(
                passo,
                pilha,
                entrada,
                posicao,
                f"Usa {formatar_producao(numero_producao)}",
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
    parser = argparse.ArgumentParser(description="Parser LL(1) da gramatica da atividade.")
    parser.add_argument("entrada", nargs="?", default="cbca")
    args = parser.parse_args()

    print("Gramatica usada:")
    for numero in sorted(PRODUCOES):
        print(f"{numero}) {formatar_producao(numero)}")

    mostrar_tabela_first_follow()
    mostrar_tabela_parser()

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
    main()
