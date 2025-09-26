# copie todo este arquivo para automato_lexer.py
from typing import List, Tuple, Optional
import sys

RESERVED = {
    'int':'T_TYPE', 'float':'T_TYPE', 'char':'T_TYPE', 'void':'T_TYPE', 'double':'T_TYPE',
    'if':'T_IF', 'else':'T_ELSE', 'for':'T_FOR', 'while':'T_WHILE', 'do':'T_DO',
    'return':'T_RETURN', 'break':'T_BREAK', 'continue':'T_CONTINUE'
}

SINGLE_CHAR_TOKENS = {
    ';':'T_SEMI', ',':'T_COMMA', '(':'T_LPAREN', ')':'T_RPAREN',
    '{':'T_LBRACE', '}':'T_RBRACE', '+':'T_OP_ARITH', '-':'T_OP_ARITH',
    '*':'T_OP_ARITH', '%':'T_OP_ARITH', '.':'T_DOT', ':':'T_COLON'
}

class Lexer:
    def __init__(self, source: str):
        self.src = source
        self.i = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Tuple[str,str,int,int]] = []
        self.symbols = {}  # identifier -> (line, col)
        self.errors: List[Tuple[str,int,int]] = []

    def peek(self, k=0) -> Optional[str]:
        idx = self.i + k
        if idx < len(self.src):
            return self.src[idx]
        return None

    def advance(self) -> Optional[str]:
        c = self.peek()
        if c is None:
            return None
        self.i += 1
        if c == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return c

    def add_token(self, ttype: str, lexeme: str, line: int, col: int):
        self.tokens.append((ttype, lexeme, line, col))
        if ttype == 'T_ID':
            if lexeme not in self.symbols:
                self.symbols[lexeme] = (line, col)

    def add_error(self, msg: str, line: int, col: int):
        self.errors.append((msg, line, col))

    def tokenize(self):
        while True:
            c = self.peek()
            if c is None:
                break

            # Skip whitespace
            if c.isspace():
                self.advance()
                continue

            start_line, start_col = self.line, self.col

            # IDENTIFIERS / RESERVED
            if c.isalpha() or c == '_':
                lex = ''
                while self.peek() is not None and (self.peek().isalnum() or self.peek() == '_'):
                    lex += self.advance()
                # reserved words check
                token_type = RESERVED.get(lex, 'T_ID')
                self.add_token(token_type, lex, start_line, start_col)
                continue

            # NUMBERS (int, float, exponent) - handles leading '.' if followed by digit
            if c.isdigit() or (c == '.' and self.peek(1) and self.peek(1).isdigit()):
                lex = ''
                saw_dot = False
                saw_exp = False

                # leading digits
                if c == '.':
                    saw_dot = True
                    lex += self.advance()  # consume '.'
                    # must have digits after '.' for a valid float starting with '.'
                    if not (self.peek() and self.peek().isdigit()):
                        # Single '.' as delimiter/token
                        self.add_token('T_DOT', '.', start_line, start_col)
                        continue
                    while self.peek() and self.peek().isdigit():
                        lex += self.advance()
                else:
                    while self.peek() and self.peek().isdigit():
                        lex += self.advance()
                    # fraction part
                    if self.peek() == '.':
                        saw_dot = True
                        lex += self.advance()
                        # allow zero or more digits after dot (accept "123." as float)
                        while self.peek() and self.peek().isdigit():
                            lex += self.advance()

                # exponent part
                if self.peek() and (self.peek() == 'e' or self.peek() == 'E'):
                    saw_exp = True
                    lex += self.advance()
                    if self.peek() and (self.peek() == '+' or self.peek() == '-'):
                        lex += self.advance()
                    # must have at least one digit after exponent
                    if not (self.peek() and self.peek().isdigit()):
                        self.add_error(f"Numero exponencial malformulado '{lex}'", start_line, start_col)
                        # consume until non-alnum to avoid infinite loop
                        while self.peek() and self.peek().isalnum():
                            self.advance()
                        continue
                    while self.peek() and self.peek().isdigit():
                        lex += self.advance()

                # decide token type
                if saw_dot or saw_exp:
                    self.add_token('T_FLOAT', lex, start_line, start_col)
                else:
                    self.add_token('T_INT', lex, start_line, start_col)
                continue

            # OPERATORS & DELIMITERS & COMMENTS
            # Two-char operators start: ==, !=, <=, >=, &&, ||
            if c in ('=', '!', '<', '>'):
                ch = self.advance()
                if self.peek() == '=':
                    ch2 = self.advance()
                    self.add_token('T_OP_REL', ch+ch2, start_line, start_col)
                else:
                    if ch == '=':
                        self.add_token('T_ATRIB', ch, start_line, start_col)
                    elif ch == '!':
                        self.add_token('T_OP_LOGIC', ch, start_line, start_col)
                    else:  # '<' or '>'
                        self.add_token('T_OP_REL', ch, start_line, start_col)
                continue

            if c in ('&', '|'):
                ch = self.advance()
                if self.peek() == ch:
                    ch2 = self.advance()
                    self.add_token('T_OP_LOGIC', ch+ch2, start_line, start_col)
                else:
                    self.add_error(f"Simbolo sozinho inesperado '{ch}' (esperando '{ch}{ch}')", start_line, start_col)
                continue

            if c == '/':
                self.advance()
                nxt = self.peek()
                if nxt == '/':
                    # line comment: consume to end of line
                    self.advance()
                    while self.peek() is not None and self.peek() != '\n':
                        self.advance()
                    continue
                elif nxt == '*':
                    # block comment: consume until */
                    self.advance()
                    closed = False
                    while True:
                        if self.peek() is None:
                            self.add_error("Bloco de comentario não terminado", start_line, start_col)
                            break
                        if self.peek() == '*' and self.peek(1) == '/':
                            self.advance(); self.advance()
                            closed = True
                            break
                        else:
                            self.advance()
                    continue
                else:
                    self.add_token('T_OP_ARITH', '/', start_line, start_col)
                    continue

            # single-char tokens (operators, delimiters)
            if c in SINGLE_CHAR_TOKENS:
                tok = SINGLE_CHAR_TOKENS[c]
                self.advance()
                self.add_token(tok, c, start_line, start_col)
                continue

            # other single-char arith ops that might not be in dict
            if c in '+-*/%':
                self.add_token('T_OP_ARITH', self.advance(), start_line, start_col)
                continue

            # unknown character
            self.add_error(f"Caractere desconhecido '{c}'", start_line, start_col)
            self.advance()

        return self.tokens, self.symbols, self.errors


def pretty_print(tokens, symbols, errors):
    print("\nTOKENS:")
    if not tokens:
        print("  (nenhum token reconhecido)")
    for t in tokens:
        ttype, lex, ln, col = t
        print(f"  {ttype:12} | {lex:25} | line {ln:3}, col {col:3}")

    print("\nTABELA DE SIMBOLOS (identificadores):")
    if not symbols:
        print("  (vazio)")
    for ident, pos in sorted(symbols.items()):
        ln,col = pos
        print(f"  {ident:20} visto pela primeira vez em lin {ln}, col {col}")

    print("\nERRORS:")
    if not errors:
        print("  (no errors)")
    for e in errors:
        msg, ln, col = e
        print(f"  {msg} (line {ln}, col {col})")
    print("\n" + "-"*60 + "\n")


# Quick demo if script is executed directly
if __name__ == "__main__":
    samples = {
        "test1": "if (x == 10) y = y + 1;",
        "test2": "while (a != b) { /* comment */ c = 3.14e-2; }",
        "test3": "x = .5; y = 123.; z = 5e; a && b || c; d = e <= f; // end",
        "test4_unclosed": "code /* unclosed comment\n x = 1;",
         "meu_teste_1": "int resultado = (100 * 2) / 4;",
        "teste_de_erro": "float val = 3.14&;",
        "teste_comentario_nao_fechado": "int x = 10; /* este comentario nao fecha",
    }

    for name, src in samples.items():
        print(f"Amostra: {name}")
        print(f"Fonte: {src}")
        lexer = Lexer(src)
        tokens, symbols, errors = lexer.tokenize()
        pretty_print(tokens, symbols, errors)
