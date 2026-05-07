import json
from pathlib import Path
from enum import Enum

# ─────────────────────────────────────────────
#  TOKENS E CÓDIGOS TERMINAIS 
# ─────────────────────────────────────────────

class TokenType(Enum):
    INT       = 1   # int
    FLOAT     = 2   # float
    IF        = 3   # if
    ELSE      = 4   # else
    WHILE     = 5   # while
    RETURN    = 6   # return
    PRINT     = 7   # print
    ID        = 8   # id
    NUM       = 9   # num
    ASSIGN    = 10  # =
    PLUS      = 11  # +
    MINUS     = 12  # -
    STAR      = 13  # *
    SLASH     = 14  # /
    EQ        = 15  # ==
    NEQ       = 16  # !=
    LT        = 17  # <
    GT        = 18  # >
    LEQ       = 19  # <=
    GEQ       = 20  # >=
    LPAREN    = 21  # (
    RPAREN    = 22  # )
    LBRACE    = 23  # {
    RBRACE    = 24  # }
    COMMA     = 25  # ,
    SEMICOLON = 26  # ;
    EOF       = 27  # $

KEYWORDS = {
    'int':    TokenType.INT,
    'float':  TokenType.FLOAT,
    'if':     TokenType.IF,
    'else':   TokenType.ELSE,
    'while':  TokenType.WHILE,
    'print':  TokenType.PRINT,
    'return': TokenType.RETURN,
}

# ─────────────────────────────────────────────
#  ERROS LÉXICOS [cite: 171-172]
# ─────────────────────────────────────────────

class ErroLexico(Exception):
    """Exceção para reportar erros durante a análise léxica[cite: 405]."""
    pass

# ─────────────────────────────────────────────
#  ANALISADOR LÉXICO (ETAPA 3)
# ─────────────────────────────────────────────

class Lexer:
    """
    Realiza a quebra da cadeia de caracteres em tokens[cite: 256].
    Implementa as regras definidas para a disciplina de Compiladores da UNESC[cite: 6].
    """

    def __init__(self, fonte: str):
        self.fonte = fonte
        self.pos = 0
        self.linha = 1

        # Estrutura principal baseada em vetores paralelos 
        self.tokens_codigos: list[int] = []
        self.lexemas: list[str | None] = []
        self.linhas: list[int] = []

    def _atual(self) -> str:
        return self.fonte[self.pos] if self.pos < len(self.fonte) else '\0'

    def _proximo(self) -> str:
        p = self.pos + 1
        return self.fonte[p] if p < len(self.fonte) else '\0'

    def _avanca(self) -> str:
        c = self._atual()
        self.pos += 1
        if c == '\n':
            self.linha += 1
        return c

    def _adiciona_token(self, tipo: TokenType, valor, linha: int):
        self.tokens_codigos.append(tipo.value)
        self.lexemas.append(valor)
        self.linhas.append(linha)

    def _pular_espacos_e_comentarios(self):
        """Ignora espaços e processa comentários de linha (ç#) e bloco (ç@)[cite: 145, 149]."""
        while self.pos < len(self.fonte):
            c = self._atual()
            if c in (' ', '\t', '\r', '\n'):
                self._avanca()
            elif c == 'ç':
                prox = self._proximo()
                if prox == '#':  # Comentário de linha [cite: 145]
                    self._avanca()
                    self._avanca()
                    while self.pos < len(self.fonte) and self._atual() != '\n':
                        self._avanca()
                elif prox == '@':  # Comentário de bloco [cite: 149]
                    linha_inicio = self.linha
                    self._avanca()
                    self._avanca()
                    fechado = False
                    while self.pos < len(self.fonte):
                        if self._atual() == '@' and self._proximo() == 'ç':
                            self._avanca()
                            self._avanca()
                            fechado = True
                            break
                        self._avanca()
                    if not fechado:
                        raise ErroLexico(f"Linha {linha_inicio}: Comentário de bloco não fechado (@ç esperado).")
                else:
                    break
            else:
                break

    def tokenizar(self) -> tuple[list[int], list[str | None], list[int]]:
        """Executa a análise completa da fonte[cite: 400]."""
        while self.pos < len(self.fonte):
            self._pular_espacos_e_comentarios()
            if self.pos >= len(self.fonte):
                break

            c = self._atual()
            linha_atual = self.linha

            # Identificadores: letras ou '_' [cite: 161, 162]
            if c.isalpha() or c == '_':
                lexeme = ''
                while self._atual().isalnum() or self._atual() == '_':
                    lexeme += self._avanca()
                
                if len(lexeme) > 64:  # [cite: 164]
                    raise ErroLexico(f"Linha {linha_atual}: Identificador excede 64 caracteres.")

                tipo = KEYWORDS.get(lexeme, TokenType.ID)
                self._adiciona_token(tipo, lexeme, linha_atual)

            # Números (int e float) [cite: 167, 168]
            elif c.isdigit():
                lexeme = ''
                while self._atual().isdigit():
                    lexeme += self._avanca()

                if self._atual() == '.' and self._proximo().isdigit():
                    lexeme += self._avanca()
                    while self._atual().isdigit():
                        lexeme += self._avanca()
                
                self._adiciona_token(TokenType.NUM, lexeme, linha_atual)

            # Operadores Relacionais e Atribuição [cite: 136]
            elif c == '=':
                self._avanca()
                if self._atual() == '=':
                    self._avanca()
                    self._adiciona_token(TokenType.EQ, '==', linha_atual)
                else:
                    self._adiciona_token(TokenType.ASSIGN, '=', linha_atual)

            elif c == '!':
                self._avanca()
                if self._atual() == '=':
                    self._avanca()
                    self._adiciona_token(TokenType.NEQ, '!=', linha_atual)
                else:
                    raise ErroLexico(f"Linha {linha_atual}: Operador inválido '!', esperado '!='.")

            elif c == '<':
                self._avanca()
                if self._atual() == '=':
                    self._avanca()
                    self._adiciona_token(TokenType.LEQ, '<=', linha_atual)
                else:
                    self._adiciona_token(TokenType.LT, '<', linha_atual)

            elif c == '>':
                self._avanca()
                if self._atual() == '=':
                    self._avanca()
                    self._adiciona_token(TokenType.GEQ, '>=', linha_atual)
                else:
                    self._adiciona_token(TokenType.GT, '>', linha_atual)

            # Aritméticos [cite: 134]
            elif c == '+':
                self._avanca(); self._adiciona_token(TokenType.PLUS, '+', linha_atual)
            elif c == '-':
                self._avanca(); self._adiciona_token(TokenType.MINUS, '-', linha_atual)
            elif c == '*':
                self._avanca(); self._adiciona_token(TokenType.STAR, '*', linha_atual)
            elif c == '/':
                self._avanca(); self._adiciona_token(TokenType.SLASH, '/', linha_atual)

            # Delimitadores [cite: 289]
            elif c == '(':
                self._avanca(); self._adiciona_token(TokenType.LPAREN, '(', linha_atual)
            elif c == ')':
                self._avanca(); self._adiciona_token(TokenType.RPAREN, ')', linha_atual)
            elif c == '{':
                self._avanca(); self._adiciona_token(TokenType.LBRACE, '{', linha_atual)
            elif c == '}':
                self._avanca(); self._adiciona_token(TokenType.RBRACE, '}', linha_atual)
            elif c == ';':
                self._avanca(); self._adiciona_token(TokenType.SEMICOLON, ';', linha_atual)
            elif c == ',':
                self._avanca(); self._adiciona_token(TokenType.COMMA, ',', linha_atual)

            else:
                char_err = self._avanca()
                raise ErroLexico(f"Linha {linha_atual}: Caractere inesperado '{char_err}'.")

        self._adiciona_token(TokenType.EOF, '$', self.linha)
        return self.tokens_codigos, self.lexemas, self.linhas

# ─────────────────────────────────────────────
#  FUNÇÕES DE SUPORTE
# ─────────────────────────────────────────────

def mostrar_tabela_tokens(codigos, lexemas, linhas):
    print(f"\n{'CÓDIGO':<8} | {'TOKEN':<15} | {'LEXEMA':<20} | LINHA")
    print("-" * 55)
    for c, lex, lin in zip(codigos, lexemas, linhas):
        nome_token = TokenType(c).name
        print(f"{c:<8} | {nome_token:<15} | {str(lex):<20} | {lin}")

def exportar_json(codigos, lexemas, linhas, caminho_txt: Path):
    dados = {"tokens": codigos, "lexemas": lexemas, "linhas": linhas}
    caminho_json = caminho_txt.with_name(f"{caminho_txt.stem}_tokens.json")
    with caminho_json.open('w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
    return caminho_json

if __name__ == "__main__":
    pasta = Path(__file__).resolve().parent
    arquivos = sorted([f for f in pasta.iterdir() if f.suffix == '.txt'])

    if not arquivos:
        print("Nenhum arquivo .txt encontrado.")
    else:
        for i, arq in enumerate(arquivos, 1): print(f"{i} - {arq.name}")
        escolha = int(input("\nEscolha o arquivo: "))
        arq_sel = arquivos[escolha-1]

        try:
            with arq_sel.open('r', encoding='utf-8') as f:
                fonte = f.read()
            
            lexer = Lexer(fonte)
            codigos, lexemas, linhas = lexer.tokenizar()
            
            mostrar_tabela_tokens(codigos, lexemas, linhas)
            caminho = exportar_json(codigos, lexemas, linhas, arq_sel)
            print(f"\n[SUCESSO] Léxico concluído. JSON gerado: {caminho.name}")
            
        except ErroLexico as e:
            print(f"\n[ERRO LÉXICO] {e}")
        except Exception as e:
            print(f"\n[ERRO] {e}")