"""
Compilador / Analisador Lexico e Sintatico
Linguagem: LangC# (baseada na gramatica fornecida)

Estrutura de transformacao em um unico arquivo:
1. O programa localiza arquivos .txt em examples/langc.
2. O usuario escolhe um arquivo por numero.
3. O Lexer le o conteudo e gera como estrutura principal tres vetores paralelos:
   - tokens  -> codigos numericos exatos dos tokens
   - lexemas -> lexemas reconhecidos
   - linhas  -> linha original de cada token
4. Esses vetores sao usados diretamente para:
   - exibicao no terminal
   - exportacao JSON em outputs/tokens
5. Os vetores sao convertidos localmente em objetos Token antes da analise
   sintatica tabular, que usa pilha explicita e tabela LL(1).
"""

import json
from pathlib import Path
from enum import Enum


RAIZ_PROJETO = Path(__file__).resolve().parent.parent
PASTA_EXEMPLOS = RAIZ_PROJETO / "examples" / "langc"
PASTA_TOKENS = RAIZ_PROJETO / "outputs" / "tokens"


# ---------------------------------------------
#  TOKENS
# ---------------------------------------------

class TokenType(Enum):
    INT        = 1   # int
    FLOAT      = 2   # float
    IF         = 3   # if
    ELSE       = 4   # else
    WHILE      = 5   # while
    RETURN     = 6   # return
    PRINT      = 7   # print
    ID         = 8   # id
    NUM        = 9   # num
    ASSIGN     = 10  # =
    PLUS       = 11  # +
    MINUS      = 12  # -
    STAR       = 13  # *
    SLASH      = 14  # /
    EQ         = 15  # ==
    NEQ        = 16  # !=
    LT         = 17  # <
    GT         = 18  # >
    LEQ        = 19  # <=
    GEQ        = 20  # >=
    LPAREN     = 21  # (
    RPAREN     = 22  # )
    LBRACE     = 23  # {
    RBRACE     = 24  # }
    COMMA      = 25  # ,
    SEMICOLON  = 26  # ;
    EOF        = 27  # $


KEYWORDS = {
    "int": TokenType.INT,
    "float": TokenType.FLOAT,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "print": TokenType.PRINT,
    "return": TokenType.RETURN,
}


class Token:
    def __init__(self, tipo: TokenType, valor, linha: int):
        self.tipo = tipo
        self.valor = valor
        self.linha = linha

    def __repr__(self):
        return f"Token({self.tipo.name}, {self.valor!r}, linha={self.linha})"


# ---------------------------------------------
#  ERROS
# ---------------------------------------------

class ErroLexico(Exception):
    pass


class ErroSintatico(Exception):
    pass


# ---------------------------------------------
#  ANALISADOR LEXICO
# ---------------------------------------------

class Lexer:
    """
    Estrutura principal da saida lexica:
      self.tokens_codigos -> vetor com os codigos numericos exatos
      self.lexemas        -> vetor com os lexemas
      self.linhas         -> vetor com as linhas correspondentes

    Regras lexicas:
      - Identificadores: comecam com letra ou '_', ate 64 chars.
      - Inteiros (num): sequencia de digitos.
      - Reais (num): digitos '.' digitos.
      - Comentarios de linha: ç#
      - Comentarios de bloco: ç@ ... @ç
    """

    def __init__(self, fonte: str):
        self.fonte = fonte
        self.pos = 0
        self.linha = 1

        self.tokens_codigos: list[int] = []
        self.lexemas: list[str | None] = []
        self.linhas: list[int] = []

    def _atual(self) -> str:
        return self.fonte[self.pos] if self.pos < len(self.fonte) else "\0"

    def _proximo(self) -> str:
        p = self.pos + 1
        return self.fonte[p] if p < len(self.fonte) else "\0"

    def _avanca(self) -> str:
        c = self._atual()
        self.pos += 1
        if c == "\n":
            self.linha += 1
        return c

    def _adiciona_token(self, tipo: TokenType, valor, linha: int):
        self.tokens_codigos.append(tipo.value)
        self.lexemas.append(valor)
        self.linhas.append(linha)

    def tokenizar(self) -> tuple[list[int], list[str | None], list[int]]:
        while self.pos < len(self.fonte):
            self._pular_espacos_e_comentarios()
            if self.pos >= len(self.fonte):
                break

            c = self._atual()
            linha_atual = self.linha

            if c.isalpha() or c == "_":
                lexeme = ""
                while self._atual().isalnum() or self._atual() == "_":
                    lexeme += self._avanca()

                if len(lexeme) > 64:
                    raise ErroLexico(
                        f"Linha {linha_atual}: identificador '{lexeme[:20]}...' excede 64 caracteres"
                    )

                tipo = KEYWORDS.get(lexeme, TokenType.ID)
                self._adiciona_token(tipo, lexeme, linha_atual)

            elif c.isdigit():
                lexeme = ""
                while self._atual().isdigit():
                    lexeme += self._avanca()

                if self._atual() == "." and self._proximo().isdigit():
                    lexeme += self._avanca()
                    while self._atual().isdigit():
                        lexeme += self._avanca()

                self._adiciona_token(TokenType.NUM, lexeme, linha_atual)

            elif c == "=":
                self._avanca()
                if self._atual() == "=":
                    self._avanca()
                    self._adiciona_token(TokenType.EQ, "==", linha_atual)
                else:
                    self._adiciona_token(TokenType.ASSIGN, "=", linha_atual)

            elif c == "!":
                self._avanca()
                if self._atual() == "=":
                    self._avanca()
                    self._adiciona_token(TokenType.NEQ, "!=", linha_atual)
                else:
                    raise ErroLexico(f"Linha {linha_atual}: operador '!' invalido, esperado '!='")

            elif c == "<":
                self._avanca()
                if self._atual() == "=":
                    self._avanca()
                    self._adiciona_token(TokenType.LEQ, "<=", linha_atual)
                else:
                    self._adiciona_token(TokenType.LT, "<", linha_atual)

            elif c == ">":
                self._avanca()
                if self._atual() == "=":
                    self._avanca()
                    self._adiciona_token(TokenType.GEQ, ">=", linha_atual)
                else:
                    self._adiciona_token(TokenType.GT, ">", linha_atual)

            elif c == "+":
                self._avanca()
                self._adiciona_token(TokenType.PLUS, "+", linha_atual)

            elif c == "-":
                self._avanca()
                self._adiciona_token(TokenType.MINUS, "-", linha_atual)

            elif c == "*":
                self._avanca()
                self._adiciona_token(TokenType.STAR, "*", linha_atual)

            elif c == "/":
                self._avanca()
                self._adiciona_token(TokenType.SLASH, "/", linha_atual)

            elif c == "(":
                self._avanca()
                self._adiciona_token(TokenType.LPAREN, "(", linha_atual)

            elif c == ")":
                self._avanca()
                self._adiciona_token(TokenType.RPAREN, ")", linha_atual)

            elif c == "{":
                self._avanca()
                self._adiciona_token(TokenType.LBRACE, "{", linha_atual)

            elif c == "}":
                self._avanca()
                self._adiciona_token(TokenType.RBRACE, "}", linha_atual)

            elif c == ";":
                self._avanca()
                self._adiciona_token(TokenType.SEMICOLON, ";", linha_atual)

            elif c == ",":
                self._avanca()
                self._adiciona_token(TokenType.COMMA, ",", linha_atual)

            else:
                raise ErroLexico(f"Linha {linha_atual}: caractere inesperado '{c}'")

        self._adiciona_token(TokenType.EOF, "$", self.linha)
        return self.tokens_codigos, self.lexemas, self.linhas

    def _pular_espacos_e_comentarios(self):
        while self.pos < len(self.fonte):
            c = self._atual()
            if c in (" ", "\t", "\r", "\n"):
                self._avanca()
            elif c == "ç":
                prox = self._proximo()
                if prox == "#":
                    self._avanca()
                    self._avanca()
                    while self.pos < len(self.fonte) and self._atual() != "\n":
                        self._avanca()
                elif prox == "@":
                    linha_inicio = self.linha
                    self._avanca()
                    self._avanca()
                    fechado = False
                    while self.pos < len(self.fonte):
                        if self._atual() == "@" and self._proximo() == "ç":
                            self._avanca()
                            self._avanca()
                            fechado = True
                            break
                        self._avanca()
                    if not fechado:
                        print(
                            f"Aviso: comentario de bloco iniciado na linha {linha_inicio} "
                            "nao foi fechado com '@ç'"
                        )
                else:
                    print(
                        f"Aviso: 'ç' encontrado na linha {self.linha}, esperado 'ç#' "
                        "para comentario de linha ou 'ç@ ... @ç' para comentario de bloco"
                    )
                    break
            else:
                break


def vetores_para_tokens(tokens_codigos: list[int], lexemas: list[str | None], linhas: list[int]) -> list[Token]:
    return [
        Token(TokenType(codigo), lexema, linha)
        for codigo, lexema, linha in zip(tokens_codigos, lexemas, linhas)
    ]


# ---------------------------------------------
#  ANALISADOR SINTATICO (descendente preditivo tabular)
# ---------------------------------------------

class Parser:
    EPSILON = "epsilon"
    FIM = "$"

    PRODUCOES = {
        1: ("PROGRAM", ["FUNCTION_LIST"]),
        2: ("FUNCTION_LIST", ["FUNCTION", "FUNCTION_LIST_TAIL"]),
        3: ("FUNCTION_LIST_TAIL", ["FUNCTION", "FUNCTION_LIST_TAIL"]),
        4: ("FUNCTION_LIST_TAIL", []),
        5: ("FUNCTION", ["TYPE", TokenType.ID, TokenType.LPAREN, "PARAM_LIST_OPT", TokenType.RPAREN, "BLOCK"]),
        6: ("TYPE", [TokenType.INT]),
        7: ("TYPE", [TokenType.FLOAT]),
        8: ("PARAM_LIST_OPT", ["PARAM_LIST"]),
        9: ("PARAM_LIST_OPT", []),
        10: ("PARAM_LIST", ["PARAM", "PARAM_LIST_TAIL"]),
        11: ("PARAM_LIST_TAIL", [TokenType.COMMA, "PARAM", "PARAM_LIST_TAIL"]),
        12: ("PARAM_LIST_TAIL", []),
        13: ("PARAM", ["TYPE", TokenType.ID]),
        14: ("BLOCK", [TokenType.LBRACE, "DECL_LIST_OPT", "STMT_LIST_OPT", TokenType.RBRACE]),
        15: ("DECL_LIST_OPT", ["DECL_LIST"]),
        16: ("DECL_LIST_OPT", []),
        17: ("DECL_LIST", ["VAR_DECL", "DECL_LIST_TAIL"]),
        18: ("DECL_LIST_TAIL", ["VAR_DECL", "DECL_LIST_TAIL"]),
        19: ("DECL_LIST_TAIL", []),
        20: ("VAR_DECL", ["TYPE", TokenType.ID, TokenType.SEMICOLON]),
        21: ("STMT_LIST_OPT", ["STMT_LIST"]),
        22: ("STMT_LIST_OPT", []),
        23: ("STMT_LIST", ["STMT", "STMT_LIST_TAIL"]),
        24: ("STMT_LIST_TAIL", ["STMT", "STMT_LIST_TAIL"]),
        25: ("STMT_LIST_TAIL", []),
        26: ("STMT", ["ASSIGN_STMT"]),
        27: ("STMT", ["IF_STMT"]),
        28: ("STMT", ["WHILE_STMT"]),
        29: ("STMT", ["PRINT_STMT"]),
        30: ("STMT", ["RETURN_STMT"]),
        31: ("STMT", ["BLOCK"]),
        32: ("ASSIGN_STMT", [TokenType.ID, TokenType.ASSIGN, "EXPR", TokenType.SEMICOLON]),
        33: ("RETURN_STMT", [TokenType.RETURN, "EXPR", TokenType.SEMICOLON]),
        34: ("PRINT_STMT", [TokenType.PRINT, TokenType.LPAREN, "EXPR", TokenType.RPAREN, TokenType.SEMICOLON]),
        35: ("IF_STMT", [TokenType.IF, TokenType.LPAREN, "EXPR", TokenType.RPAREN, "STMT", "ELSE_PART"]),
        36: ("ELSE_PART", [TokenType.ELSE, "STMT"]),
        37: ("ELSE_PART", []),
        38: ("WHILE_STMT", [TokenType.WHILE, TokenType.LPAREN, "EXPR", TokenType.RPAREN, "STMT"]),
        39: ("EXPR", ["REL_EXPR"]),
        40: ("REL_EXPR", ["ADD_EXPR", "REL_EXPR_TAIL"]),
        41: ("REL_EXPR_TAIL", ["REL_OP", "ADD_EXPR"]),
        42: ("REL_EXPR_TAIL", []),
        43: ("REL_OP", [TokenType.EQ]),
        44: ("REL_OP", [TokenType.NEQ]),
        45: ("REL_OP", [TokenType.LT]),
        46: ("REL_OP", [TokenType.GT]),
        47: ("REL_OP", [TokenType.LEQ]),
        48: ("REL_OP", [TokenType.GEQ]),
        49: ("ADD_EXPR", ["MUL_EXPR", "ADD_EXPR_TAIL"]),
        50: ("ADD_EXPR_TAIL", [TokenType.PLUS, "MUL_EXPR", "ADD_EXPR_TAIL"]),
        51: ("ADD_EXPR_TAIL", [TokenType.MINUS, "MUL_EXPR", "ADD_EXPR_TAIL"]),
        52: ("ADD_EXPR_TAIL", []),
        53: ("MUL_EXPR", ["FACTOR", "MUL_EXPR_TAIL"]),
        54: ("MUL_EXPR_TAIL", [TokenType.STAR, "FACTOR", "MUL_EXPR_TAIL"]),
        55: ("MUL_EXPR_TAIL", [TokenType.SLASH, "FACTOR", "MUL_EXPR_TAIL"]),
        56: ("MUL_EXPR_TAIL", []),
        57: ("FACTOR", [TokenType.LPAREN, "EXPR", TokenType.RPAREN]),
        58: ("FACTOR", [TokenType.ID, "FACTOR_TAIL"]),
        59: ("FACTOR", [TokenType.NUM]),
        60: ("FACTOR_TAIL", [TokenType.LPAREN, "ARG_LIST_OPT", TokenType.RPAREN]),
        61: ("FACTOR_TAIL", []),
        62: ("ARG_LIST_OPT", ["ARG_LIST"]),
        63: ("ARG_LIST_OPT", []),
        64: ("ARG_LIST", ["EXPR", "ARG_LIST_TAIL"]),
        65: ("ARG_LIST_TAIL", [TokenType.COMMA, "EXPR", "ARG_LIST_TAIL"]),
        66: ("ARG_LIST_TAIL", []),
    }

    NAO_TERMINAIS = {esquerda for esquerda, _ in PRODUCOES.values()}

    REL_OPS = {
        TokenType.EQ, TokenType.NEQ, TokenType.LT,
        TokenType.GT, TokenType.LEQ, TokenType.GEQ
    }
    FIRST_TYPE = {TokenType.INT, TokenType.FLOAT}
    FIRST_STMT = {
        TokenType.ID, TokenType.IF, TokenType.WHILE,
        TokenType.PRINT, TokenType.RETURN, TokenType.LBRACE
    }
    FIRST_EXPR = {TokenType.LPAREN, TokenType.ID, TokenType.NUM}
    FOLLOW_EXPR = {TokenType.RPAREN, TokenType.SEMICOLON, TokenType.COMMA}
    FOLLOW_FACTOR = FOLLOW_EXPR | REL_OPS | {TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH}

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.tabela = self._criar_tabela()

    @property
    def atual(self) -> Token:
        return self.tokens[self.pos]

    @classmethod
    def _criar_tabela(cls):
        tabela = {}

        def add(nao_terminal, terminais, producao):
            for terminal in terminais:
                tabela[(nao_terminal, terminal)] = producao

        add("PROGRAM", cls.FIRST_TYPE, 1)
        add("FUNCTION_LIST", cls.FIRST_TYPE, 2)
        add("FUNCTION_LIST_TAIL", cls.FIRST_TYPE, 3)
        add("FUNCTION_LIST_TAIL", {TokenType.EOF}, 4)
        add("FUNCTION", cls.FIRST_TYPE, 5)
        add("TYPE", {TokenType.INT}, 6)
        add("TYPE", {TokenType.FLOAT}, 7)
        add("PARAM_LIST_OPT", cls.FIRST_TYPE, 8)
        add("PARAM_LIST_OPT", {TokenType.RPAREN}, 9)
        add("PARAM_LIST", cls.FIRST_TYPE, 10)
        add("PARAM_LIST_TAIL", {TokenType.COMMA}, 11)
        add("PARAM_LIST_TAIL", {TokenType.RPAREN}, 12)
        add("PARAM", cls.FIRST_TYPE, 13)
        add("BLOCK", {TokenType.LBRACE}, 14)
        add("DECL_LIST_OPT", cls.FIRST_TYPE, 15)
        add("DECL_LIST_OPT", cls.FIRST_STMT | {TokenType.RBRACE}, 16)
        add("DECL_LIST", cls.FIRST_TYPE, 17)
        add("DECL_LIST_TAIL", cls.FIRST_TYPE, 18)
        add("DECL_LIST_TAIL", cls.FIRST_STMT | {TokenType.RBRACE}, 19)
        add("VAR_DECL", cls.FIRST_TYPE, 20)
        add("STMT_LIST_OPT", cls.FIRST_STMT, 21)
        add("STMT_LIST_OPT", {TokenType.RBRACE}, 22)
        add("STMT_LIST", cls.FIRST_STMT, 23)
        add("STMT_LIST_TAIL", cls.FIRST_STMT, 24)
        add("STMT_LIST_TAIL", {TokenType.RBRACE}, 25)
        add("STMT", {TokenType.ID}, 26)
        add("STMT", {TokenType.IF}, 27)
        add("STMT", {TokenType.WHILE}, 28)
        add("STMT", {TokenType.PRINT}, 29)
        add("STMT", {TokenType.RETURN}, 30)
        add("STMT", {TokenType.LBRACE}, 31)
        add("ASSIGN_STMT", {TokenType.ID}, 32)
        add("RETURN_STMT", {TokenType.RETURN}, 33)
        add("PRINT_STMT", {TokenType.PRINT}, 34)
        add("IF_STMT", {TokenType.IF}, 35)
        add("ELSE_PART", {TokenType.ELSE}, 36)
        add("ELSE_PART", cls.FIRST_STMT | {TokenType.RBRACE, TokenType.EOF}, 37)
        add("WHILE_STMT", {TokenType.WHILE}, 38)
        add("EXPR", cls.FIRST_EXPR, 39)
        add("REL_EXPR", cls.FIRST_EXPR, 40)
        add("REL_EXPR_TAIL", cls.REL_OPS, 41)
        add("REL_EXPR_TAIL", cls.FOLLOW_EXPR, 42)
        for terminal, producao in [
            (TokenType.EQ, 43), (TokenType.NEQ, 44), (TokenType.LT, 45),
            (TokenType.GT, 46), (TokenType.LEQ, 47), (TokenType.GEQ, 48),
        ]:
            add("REL_OP", {terminal}, producao)
        add("ADD_EXPR", cls.FIRST_EXPR, 49)
        add("ADD_EXPR_TAIL", {TokenType.PLUS}, 50)
        add("ADD_EXPR_TAIL", {TokenType.MINUS}, 51)
        add("ADD_EXPR_TAIL", cls.REL_OPS | cls.FOLLOW_EXPR, 52)
        add("MUL_EXPR", cls.FIRST_EXPR, 53)
        add("MUL_EXPR_TAIL", {TokenType.STAR}, 54)
        add("MUL_EXPR_TAIL", {TokenType.SLASH}, 55)
        add("MUL_EXPR_TAIL", {TokenType.PLUS, TokenType.MINUS} | cls.REL_OPS | cls.FOLLOW_EXPR, 56)
        add("FACTOR", {TokenType.LPAREN}, 57)
        add("FACTOR", {TokenType.ID}, 58)
        add("FACTOR", {TokenType.NUM}, 59)
        add("FACTOR_TAIL", {TokenType.LPAREN}, 60)
        add("FACTOR_TAIL", cls.FOLLOW_FACTOR, 61)
        add("ARG_LIST_OPT", cls.FIRST_EXPR, 62)
        add("ARG_LIST_OPT", {TokenType.RPAREN}, 63)
        add("ARG_LIST", cls.FIRST_EXPR, 64)
        add("ARG_LIST_TAIL", {TokenType.COMMA}, 65)
        add("ARG_LIST_TAIL", {TokenType.RPAREN}, 66)
        return tabela

    def _simbolo_token(self, tipo: TokenType) -> str:
        simbolos = {
            TokenType.INT: "int",
            TokenType.FLOAT: "float",
            TokenType.IF: "if",
            TokenType.ELSE: "else",
            TokenType.WHILE: "while",
            TokenType.RETURN: "return",
            TokenType.PRINT: "print",
            TokenType.ID: "identificador",
            TokenType.NUM: "numero",
            TokenType.ASSIGN: "=",
            TokenType.PLUS: "+",
            TokenType.MINUS: "-",
            TokenType.STAR: "*",
            TokenType.SLASH: "/",
            TokenType.EQ: "==",
            TokenType.NEQ: "!=",
            TokenType.LT: "<",
            TokenType.GT: ">",
            TokenType.LEQ: "<=",
            TokenType.GEQ: ">=",
            TokenType.LPAREN: "(",
            TokenType.RPAREN: ")",
            TokenType.LBRACE: "{",
            TokenType.RBRACE: "}",
            TokenType.COMMA: ",",
            TokenType.SEMICOLON: ";",
            TokenType.EOF: "$",
        }
        return simbolos.get(tipo, tipo.name)

    def _formatar_token_encontrado(self, tok: Token) -> str:
        if tok.tipo == TokenType.EOF:
            return "fim de entrada '$'"
        if tok.valor is None:
            return f"token {tok.tipo.name}"
        return f"{tok.valor!r}"

    def _formatar_simbolo(self, simbolo) -> str:
        if isinstance(simbolo, TokenType):
            return self._simbolo_token(simbolo)
        return str(simbolo)

    def _formatar_pilha(self, pilha) -> str:
        return " ".join(self._formatar_simbolo(s) for s in reversed(pilha))

    def _formatar_producao(self, numero: int) -> str:
        esquerda, direita = self.PRODUCOES[numero]
        texto_direita = " ".join(self._formatar_simbolo(s) for s in direita) if direita else self.EPSILON
        return f"{esquerda} -> {texto_direita}"

    def _registrar_passo(self, passo: int, pilha, tok: Token, acao: str):
        lexema = "$" if tok.tipo == TokenType.EOF else tok.valor
        print(
            f"{passo:<5} | {tok.tipo.value:<6} | {tok.tipo.name:<10} | "
            f"{str(lexema):<12} | {tok.linha:<5} | {self._formatar_pilha(pilha):<55} | {acao}"
        )

    def _mensagem_erro_terminal(self, esperado: TokenType, encontrado: Token) -> str:
        anterior = self.tokens[self.pos - 1] if self.pos > 0 else encontrado

        if esperado == TokenType.SEMICOLON:
            return (
                f"Linha {anterior.linha}: faltou ';' ao final da instrucao "
                f"antes de {self._formatar_token_encontrado(encontrado)} "
                f"(linha {encontrado.linha})"
            )
        if esperado == TokenType.RPAREN:
            return (
                f"Linha {anterior.linha}: faltou ')' antes de "
                f"{self._formatar_token_encontrado(encontrado)} "
                f"(linha {encontrado.linha})"
            )
        if esperado == TokenType.RBRACE:
            return (
                f"Linha {anterior.linha}: faltou '}}' antes de "
                f"{self._formatar_token_encontrado(encontrado)} "
                f"(linha {encontrado.linha})"
            )
        if esperado == TokenType.LPAREN:
            return (
                f"Linha {anterior.linha}: faltou '(' apos "
                f"{self._formatar_token_encontrado(anterior)}"
            )
        if esperado == TokenType.ID and anterior.tipo in self.FIRST_TYPE:
            return (
                f"Linha {encontrado.linha}: esperado identificador apos o tipo "
                f"{self._formatar_token_encontrado(anterior)}, "
                f"mas encontrado {self._formatar_token_encontrado(encontrado)}"
            )

        return (
            f"Linha {encontrado.linha}: esperado '{self._simbolo_token(esperado)}', "
            f"encontrado {self._formatar_token_encontrado(encontrado)}"
        )

    def _mensagem_erro_tabela(self, nao_terminal: str, encontrado: Token) -> str:
        esperados = sorted(
            {
                self._simbolo_token(terminal)
                for nt, terminal in self.tabela
                if nt == nao_terminal
            }
        )
        lista = ", ".join(esperados) if esperados else "nenhum token valido"
        return (
            f"Linha {encontrado.linha}: erro sintatico em {nao_terminal}; "
            f"encontrado {self._formatar_token_encontrado(encontrado)}. "
            f"Esperado um de: {lista}"
        )

    def programa(self):
        pilha = [TokenType.EOF, "PROGRAM"]
        passo = 1

        print("\nTabela de analise sintatica (execucao tabular):")
        print("Passo | CodTok | Token      | Lexema       | Linha | Pilha                                                   | Acao")
        print("-" * 116)

        while pilha:
            topo = pilha[-1]
            tok = self.atual

            if isinstance(topo, TokenType):
                if topo != tok.tipo:
                    raise ErroSintatico(self._mensagem_erro_terminal(topo, tok))

                self._registrar_passo(passo, pilha, tok, f"Consome {self._simbolo_token(topo)}")
                pilha.pop()
                self.pos += 1
                passo += 1
                continue

            numero_producao = self.tabela.get((topo, tok.tipo))
            if numero_producao is None:
                raise ErroSintatico(self._mensagem_erro_tabela(topo, tok))

            self._registrar_passo(
                passo,
                pilha,
                tok,
                f"Usa {numero_producao}: {self._formatar_producao(numero_producao)}",
            )
            pilha.pop()
            _, direita = self.PRODUCOES[numero_producao]
            for simbolo in reversed(direita):
                pilha.append(simbolo)
            passo += 1

        print("OK  Analise sintatica concluida sem erros.")


# ---------------------------------------------
#  FUNCOES AUXILIARES DE ENTRADA/SAIDA
# ---------------------------------------------

def obter_pasta_script() -> Path:
    return PASTA_EXEMPLOS if PASTA_EXEMPLOS.is_dir() else Path(__file__).resolve().parent


def listar_arquivos_txt(pasta: Path) -> list[Path]:
    return sorted(
        [arquivo for arquivo in pasta.iterdir() if arquivo.is_file() and arquivo.suffix.lower() == ".txt"],
        key=lambda arquivo: arquivo.name.lower(),
    )


def escolher_arquivo(arquivos: list[Path]) -> Path:
    print("Arquivos .txt encontrados:")
    for i, arquivo in enumerate(arquivos, start=1):
        print(f"  {i} - {arquivo.name}")

    while True:
        escolha = input("\nDigite o numero do arquivo que deseja analisar: ").strip()

        if not escolha:
            print("Entrada vazia. Digite um numero da lista.")
            continue

        if not escolha.isdigit():
            print("Entrada invalida. Digite apenas o numero do arquivo.")
            continue

        indice = int(escolha)
        if 1 <= indice <= len(arquivos):
            return arquivos[indice - 1]

        print(f"Numero fora do intervalo. Escolha entre 1 e {len(arquivos)}.")


def ler_arquivo(caminho: Path) -> str:
    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            return arquivo.read()
    except OSError as e:
        raise RuntimeError(f"Erro ao abrir o arquivo '{caminho.name}': {e}") from e
    except UnicodeDecodeError as e:
        raise RuntimeError(
            f"Erro ao ler '{caminho.name}': o arquivo nao esta em UTF-8 valido."
        ) from e


def mostrar_tabela_tokens(tokens_codigos: list[int], lexemas: list[str | None], linhas: list[int], incluir_eof: bool = False):
    registros = []
    for codigo, lexema, linha in zip(tokens_codigos, lexemas, linhas):
        if not incluir_eof and codigo == TokenType.EOF.value:
            continue
        registros.append((codigo, lexema, linha))

    if not registros:
        print("Nenhum token para exibir.")
        return

    nomes = [TokenType(codigo).name for codigo, _, _ in registros]
    lexemas_formatados = ["" if lexema is None else str(lexema) for _, lexema, _ in registros]

    largura_codigo = max(len("CODIGO"), max(len(str(codigo)) for codigo, _, _ in registros))
    largura_token = max(len("TOKEN"), max(len(nome) for nome in nomes))
    largura_lexema = max(len("LEXEMA"), max(len(lex) for lex in lexemas_formatados))

    cabecalho = (
        f"{'CODIGO':<{largura_codigo}} | "
        f"{'TOKEN':<{largura_token}} | "
        f"{'LEXEMA':<{largura_lexema}} | LINHA"
    )
    print("\n" + cabecalho)
    print("-" * len(cabecalho))

    for (codigo, lexema, linha), nome in zip(registros, nomes):
        lexema_texto = "" if lexema is None else str(lexema)
        print(f"{codigo:<{largura_codigo}} | {nome:<{largura_token}} | {lexema_texto:<{largura_lexema}} | {linha}")


def exportar_tokens_json(tokens_codigos: list[int], lexemas: list[str | None], linhas: list[int], caminho_txt: Path) -> Path:
    tokens_sem_eof = []
    lexemas_sem_eof = []
    linhas_sem_eof = []

    for codigo, lexema, linha in zip(tokens_codigos, lexemas, linhas):
        if codigo == TokenType.EOF.value:
            continue
        tokens_sem_eof.append(codigo)
        lexemas_sem_eof.append("" if lexema is None else str(lexema))
        linhas_sem_eof.append(linha)

    dados = {
        "tokens": tokens_sem_eof,
        "lexemas": lexemas_sem_eof,
        "linhas": linhas_sem_eof,
    }

    PASTA_TOKENS.mkdir(parents=True, exist_ok=True)
    caminho_json = PASTA_TOKENS / f"{caminho_txt.stem}_tokens.json"
    with caminho_json.open("w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)

    return caminho_json


# ---------------------------------------------
#  INTERFACE PRINCIPAL
# ---------------------------------------------

def compilar(fonte: str, mostrar_tokens: bool = True):
    print("=" * 50)
    print("  COMPILADOR LangC#")
    print("=" * 50)

    print("\n[1] Analise Lexica...")
    try:
        lexer = Lexer(fonte)
        tokens_codigos, lexemas, linhas = lexer.tokenizar()
        quantidade_sem_eof = sum(1 for codigo in tokens_codigos if codigo != TokenType.EOF.value)
        print(f"    {quantidade_sem_eof} token(s) gerado(s).")
        if mostrar_tokens:
            mostrar_tabela_tokens(tokens_codigos, lexemas, linhas)
    except ErroLexico as e:
        print(f"    ERRO LEXICO: {e}")
        return None, None, None, False

    print("\n[2] Analise Sintatica...")
    try:
        tokens_parser = vetores_para_tokens(tokens_codigos, lexemas, linhas)
        parser = Parser(tokens_parser)
        parser.programa()
    except ErroSintatico as e:
        print(f"    ERRO SINTATICO: {e}")
        return tokens_codigos, lexemas, linhas, False

    print("\n  Compilacao finalizada com sucesso!")
    print("=" * 50)
    return tokens_codigos, lexemas, linhas, True


if __name__ == "__main__":
    pasta_script = obter_pasta_script()
    arquivos_txt = listar_arquivos_txt(pasta_script)

    if not arquivos_txt:
        print(f"Nenhum arquivo .txt encontrado na pasta de exemplos: {pasta_script}")
    else:
        arquivo_escolhido = escolher_arquivo(arquivos_txt)
        print(f"\nArquivo selecionado: {arquivo_escolhido.name}")

        try:
            codigo = ler_arquivo(arquivo_escolhido)
        except RuntimeError as e:
            print(e)
        else:
            tokens_codigos, lexemas, linhas, _ = compilar(codigo, mostrar_tokens=True)
            if tokens_codigos is not None and lexemas is not None and linhas is not None:
                try:
                    caminho_json = exportar_tokens_json(tokens_codigos, lexemas, linhas, arquivo_escolhido)
                    print(f"\n[3] Tokens exportados em JSON: {caminho_json.relative_to(RAIZ_PROJETO)}")
                except OSError as e:
                    print(f"\n[3] Nao foi possivel exportar o JSON: {e}")
