"""
Atividade de Compiladores - Analise Semantica

Resolucao baseada no arquivo:
docs/activities/AcoesSemantico.pdf

Acao semantica implementada:
1. Carregar uma tabela de simbolos com Nome, Categoria, Tipo e Nivel.
2. Inserir declaracoes const como categoria "constante" no nivel global.
3. Impedir alteracao posterior do valor de uma constante.

Este arquivo fica separado do compilador principal, no mesmo estilo da
atividade sintatica, mas reaproveita o lexer e parser ja implementados.
"""

import argparse
import io
from pathlib import Path
from dataclasses import dataclass
from contextlib import redirect_stdout

from compilador import (
    ErroLexico,
    ErroSintatico,
    Lexer,
    Parser,
    Token,
    TokenType,
    vetores_para_tokens,
)


RAIZ_PROJETO = Path(__file__).resolve().parent.parent
EXEMPLO_PADRAO = RAIZ_PROJETO / "examples" / "semantico" / "6_erro_semantico_const.txt"


class ErroSemantico(Exception):
    pass


@dataclass
class Simbolo:
    nome: str
    categoria: str
    tipo: TokenType
    nivel: int
    linha: int


ACOES_SEMANTICAS = [
    ["Acao", "Descricao"],
    ["Tabela", "Nome | Categoria | Tipo | Nivel"],
    ["Insercao", "const nome = valor; entra como categoria constante no nivel 0"],
    ["Regra", "O valor de uma constante nao pode ser alterado"],
    ["Erro", "Mostrar numero da linha e erro semantico"],
]


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
    mostrar_tabela("Acoes semanticas do PDF:", ACOES_SEMANTICAS)


def mostrar_codigo(origem, codigo):
    print(f"\nArquivo analisado: {origem}")
    print("\nCodigo-fonte:")
    for numero, linha in enumerate(codigo.splitlines(), start=1):
        print(f"{numero:>3} | {linha}")


def nome_tipo(tipo: TokenType):
    if tipo == TokenType.INT:
        return "int"
    if tipo == TokenType.FLOAT:
        return "float"
    return tipo.name.lower()


def mostrar_tabela_simbolos(simbolos: list[Simbolo]):
    linhas = [["Nome", "Categoria", "Tipo", "Nivel"]]

    for simbolo in simbolos:
        linhas.append(
            [
                simbolo.nome,
                simbolo.categoria,
                nome_tipo(simbolo.tipo),
                str(simbolo.nivel),
            ]
        )

    if len(linhas) == 1:
        print("\nTabela de simbolos vazia.")
        return

    mostrar_tabela("Tabela de simbolos gerada:", linhas)


def obter_codigo(entrada):
    caminho = Path(entrada)

    if caminho.is_file():
        return caminho.read_text(encoding="utf-8"), caminho.name

    return entrada, "entrada direta"


def eh_const_decl(tokens: list[Token], posicao: int) -> bool:
    return (
        posicao + 3 < len(tokens)
        and tokens[posicao].tipo == TokenType.ID
        and tokens[posicao].valor == "const"
        and tokens[posicao + 1].tipo == TokenType.ID
        and tokens[posicao + 2].tipo == TokenType.ASSIGN
    )


def inferir_tipo_constante(tokens: list[Token], inicio: int, fim: int, tipos: dict[str, TokenType]) -> TokenType:
    for token in tokens[inicio:fim]:
        if token.tipo == TokenType.NUM and "." in str(token.valor):
            return TokenType.FLOAT

        if token.tipo == TokenType.ID and token.valor in tipos:
            if tipos[token.valor] == TokenType.FLOAT:
                return TokenType.FLOAT

    return TokenType.INT


def coletar_constantes_globais(tokens: list[Token]):
    simbolos = []
    tipos = {}
    posicao = 0

    while eh_const_decl(tokens, posicao):
        nome = tokens[posicao + 1]
        pos_expr = posicao + 3
        fim_expr = pos_expr

        while fim_expr < len(tokens) and tokens[fim_expr].tipo != TokenType.SEMICOLON:
            fim_expr += 1

        if fim_expr >= len(tokens):
            raise ErroSintatico(
                f"Linha {tokens[posicao].linha}: faltou ';' ao final da declaracao const"
            )

        tipo = inferir_tipo_constante(tokens, pos_expr, fim_expr, tipos)
        tipos[str(nome.valor)] = tipo
        simbolos.append(Simbolo(str(nome.valor), "constante", tipo, 0, nome.linha))
        posicao = fim_expr + 1

    return simbolos, tipos, posicao


def coletar_simbolos_do_programa(tokens: list[Token], simbolos: list[Simbolo]):
    posicao = 0

    while posicao < len(tokens):
        if (
            posicao + 2 < len(tokens)
            and tokens[posicao].tipo in (TokenType.INT, TokenType.FLOAT)
            and tokens[posicao + 1].tipo == TokenType.ID
            and tokens[posicao + 2].tipo == TokenType.LPAREN
        ):
            tipo_funcao = tokens[posicao].tipo
            nome_funcao = tokens[posicao + 1]
            simbolos.append(Simbolo(str(nome_funcao.valor), "funcao", tipo_funcao, 0, nome_funcao.linha))
            posicao += 3

            while posicao + 1 < len(tokens) and tokens[posicao].tipo != TokenType.RPAREN:
                if tokens[posicao].tipo in (TokenType.INT, TokenType.FLOAT) and tokens[posicao + 1].tipo == TokenType.ID:
                    simbolos.append(
                        Simbolo(
                            str(tokens[posicao + 1].valor),
                            "parametro",
                            tokens[posicao].tipo,
                            1,
                            tokens[posicao + 1].linha,
                        )
                    )
                    posicao += 2
                    continue

                posicao += 1

        if (
            posicao + 2 < len(tokens)
            and tokens[posicao].tipo in (TokenType.INT, TokenType.FLOAT)
            and tokens[posicao + 1].tipo == TokenType.ID
            and tokens[posicao + 2].tipo == TokenType.SEMICOLON
        ):
            simbolos.append(
                Simbolo(
                    str(tokens[posicao + 1].valor),
                    "variavel",
                    tokens[posicao].tipo,
                    1,
                    tokens[posicao + 1].linha,
                )
            )
            posicao += 3
            continue

        posicao += 1


def verificar_alteracao_constante(tokens: list[Token], nomes_constantes: set[str]):
    for indice, token in enumerate(tokens[:-1]):
        if (
            token.tipo == TokenType.ID
            and token.valor in nomes_constantes
            and tokens[indice + 1].tipo == TokenType.ASSIGN
        ):
            raise ErroSemantico(
                f"Linha {token.linha}: o valor da constante '{token.valor}' nao pode ser alterado"
            )


def analisar_semantico(codigo):
    lexer = Lexer(codigo)
    tokens_codigos, lexemas, linhas = lexer.tokenizar()
    tokens = vetores_para_tokens(tokens_codigos, lexemas, linhas)
    simbolos, tipos_constantes, posicao_programa = coletar_constantes_globais(tokens)
    tokens_programa = tokens[posicao_programa:]
    parser = Parser(tokens_programa)

    try:
        with redirect_stdout(io.StringIO()):
            parser.programa()

        coletar_simbolos_do_programa(tokens_programa, simbolos)
        verificar_alteracao_constante(tokens_programa, set(tipos_constantes))
    except ErroSemantico as erro:
        mostrar_tabela_simbolos(simbolos)
        print(f"\nERRO SEMANTICO: {erro}")
        return False

    mostrar_tabela_simbolos(simbolos)
    print("\nAnalise semantica concluida sem erros.")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Analise semantica separada conforme AcoesSemantico.pdf."
    )
    parser.add_argument(
        "entrada",
        nargs="?",
        default=str(EXEMPLO_PADRAO),
        help="Caminho de um arquivo .txt ou codigo-fonte direto.",
    )
    args = parser.parse_args()

    mostrar_resolucao_do_pdf()

    try:
        codigo, origem = obter_codigo(args.entrada)
        mostrar_codigo(origem, codigo)
        sucesso = analisar_semantico(codigo)
    except ErroLexico as erro:
        print(f"\nERRO LEXICO: {erro}")
        return 1
    except ErroSintatico as erro:
        print(f"\nERRO SINTATICO: {erro}")
        return 1
    except OSError as erro:
        print(f"\nErro ao ler entrada: {erro}")
        return 1

    if sucesso:
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
