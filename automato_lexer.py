# Importações necessárias para anotação de tipos e para o sistema
from typing import List, Tuple, Optional
import sys

# Dicionário que mapeia lexemas de palavras reservadas para seus tipos de token
PALAVRAS_RESERVADAS = {
    'int': 'T_TIPO', 'float': 'T_TIPO', 'char': 'T_TIPO', 'void': 'T_TIPO', 'double': 'T_TIPO',
    'if': 'T_IF', 'else': 'T_ELSE', 'for': 'T_FOR', 'while': 'T_WHILE', 'do': 'T_DO',
    'return': 'T_RETURN', 'break': 'T_BREAK', 'continue': 'T_CONTINUE'
}

# Dicionário para tokens simples de um único caractere
TOKENS_DE_UM_CARACTERE = {
    ';': 'T_PONTO_VIRGULA', ',': 'T_VIRGULA', '(': 'T_PARENTESES_ESQ', ')': 'T_PARENTESES_DIR',
    '{': 'T_CHAVES_ESQ', '}': 'T_CHAVES_DIR', '+': 'T_OP_ARIT', '-': 'T_OP_ARIT',
    '*': 'T_OP_ARIT', '%': 'T_OP_ARIT', '.': 'T_PONTO', ':': 'T_DOIS_PONTOS'
}

class AnalisadorLexico:
    def __init__(self, codigo_fonte: str):
        self.codigo_fonte = codigo_fonte
        self.posicao_atual = 0
        self.linha = 1
        self.coluna = 1
        self.tokens: List[Tuple[str, str, int, int]] = []
        self.tabela_simbolos = {}  # Guarda identificadores: nome -> (linha, coluna)
        self.erros: List[Tuple[str, int, int]] = []

    def ver_proximo(self, k=0) -> Optional[str]:
        indice = self.posicao_atual + k
        if indice < len(self.codigo_fonte):
            return self.codigo_fonte[indice]
        return None

    def avancar(self) -> Optional[str]:
        char_atual = self.ver_proximo()
        if char_atual is None:
            return None
        
        self.posicao_atual += 1
        if char_atual == '\n':
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        return char_atual

    def adicionar_token(self, tipo: str, lexema: str, linha: int, coluna: int):
        self.tokens.append((tipo, lexema, linha, coluna))
        # Se o token for um identificador, adiciona à tabela de símbolos se for a primeira vez
        if tipo == 'T_ID':
            if lexema not in self.tabela_simbolos:
                self.tabela_simbolos[lexema] = (linha, coluna)

    def adicionar_erro(self, mensagem: str, linha: int, coluna: int):
        self.erros.append((mensagem, linha, coluna))

    def analisar(self):
        while True:
            char_atual = self.ver_proximo()
            if char_atual is None:
                # Fim do arquivo, encerra a análise
                break

            if char_atual.isspace():
                self.avancar()
                continue

            linha_inicio, coluna_inicio = self.linha, self.coluna

            # --- Etapa 2: Reconhecer Identificadores e Palavras Reservadas ---
            if char_atual.isalpha() or char_atual == '_':
                lexema = ''
                while self.ver_proximo() is not None and (self.ver_proximo().isalnum() or self.ver_proximo() == '_'):
                    lexema += self.avancar()
                
                # Verifica se o lexema é uma palavra reservada ou um identificador comum
                tipo_token = PALAVRAS_RESERVADAS.get(lexema, 'T_ID')
                self.adicionar_token(tipo_token, lexema, linha_inicio, coluna_inicio)
                continue

            if char_atual.isdigit() or (char_atual == '.' and self.ver_proximo(1) and self.ver_proximo(1).isdigit()):
                lexema = ''
                viu_ponto = False
                viu_expoente = False

                if char_atual == '.':
                    viu_ponto = True
                    lexema += self.avancar() # consome '.'
                    # Garante que um número começando com '.' seja seguido por dígitos
                    if not (self.ver_proximo() and self.ver_proximo().isdigit()):
                        self.adicionar_token('T_PONTO', '.', linha_inicio, coluna_inicio)
                        continue
                
                # Consome a parte inteira (se houver)
                while self.ver_proximo() and self.ver_proximo().isdigit():
                    lexema += self.avancar()
                
                # Consome a parte fracionária (se houver)
                if self.ver_proximo() == '.':
                    if viu_ponto: # Erro, dois pontos no mesmo número
                        self.adicionar_erro(f"Número malformado com múltiplos pontos: '{lexema}.'", linha_inicio, coluna_inicio)
                    else:
                        viu_ponto = True
                        lexema += self.avancar()
                        while self.ver_proximo() and self.ver_proximo().isdigit():
                            lexema += self.avancar()
                
                # Consome a parte do expoente (se houver)
                if self.ver_proximo() and self.ver_proximo().lower() == 'e':
                    viu_expoente = True
                    lexema += self.avancar()
                    if self.ver_proximo() and self.ver_proximo() in ('+', '-'):
                        lexema += self.avancar()
                    
                    if not (self.ver_proximo() and self.ver_proximo().isdigit()):
                        self.adicionar_erro(f"Número exponencial malformado '{lexema}'", linha_inicio, coluna_inicio)
                        continue
                    
                    while self.ver_proximo() and self.ver_proximo().isdigit():
                        lexema += self.avancar()

                # Decide o tipo do token numérico
                if viu_ponto or viu_expoente:
                    self.adicionar_token('T_NUMERO_FLOAT', lexema, linha_inicio, coluna_inicio)
                else:
                    self.adicionar_token('T_NUMERO_INT', lexema, linha_inicio, coluna_inicio)
                continue

            # Operadores que podem ter dois caracteres: ==, !=, <=, >=, &&, ||
            if char_atual in ('=', '!', '<', '>'):
                char1 = self.avancar()
                if self.ver_proximo() == '=':
                    char2 = self.avancar()
                    self.adicionar_token('T_OP_REL', char1 + char2, linha_inicio, coluna_inicio)
                else:
                    if char1 == '=':
                        self.adicionar_token('T_ATRIBUICAO', char1, linha_inicio, coluna_inicio)
                    elif char1 == '!':
                        self.adicionar_token('T_OP_LOGICO', char1, linha_inicio, coluna_inicio)
                    else:  # '<' ou '>'
                        self.adicionar_token('T_OP_REL', char1, linha_inicio, coluna_inicio)
                continue

            if char_atual in ('&', '|'):
                char1 = self.avancar()
                if self.ver_proximo() == char1:
                    char2 = self.avancar()
                    self.adicionar_token('T_OP_LOGICO', char1 + char2, linha_inicio, coluna_inicio)
                else:
                    self.adicionar_erro(f"Símbolo único inesperado '{char1}' (esperava-se '{char1}{char1}')", linha_inicio, coluna_inicio)
                continue

            # Divisão ou Comentários
            if char_atual == '/':
                self.avancar() # Consome a primeira '/'
                proximo_char = self.ver_proximo()
                if proximo_char == '/':
                    # Comentário de linha: consome até o final da linha
                    self.avancar()
                    while self.ver_proximo() is not None and self.ver_proximo() != '\n':
                        self.avancar()
                    continue
                elif proximo_char == '*':
                    # Comentário de bloco: consome até encontrar */
                    self.avancar()
                    while True:
                        if self.ver_proximo() is None:
                            self.adicionar_erro("Bloco de comentário não finalizado", linha_inicio, coluna_inicio)
                            break
                        if self.ver_proximo() == '*' and self.ver_proximo(1) == '/':
                            self.avancar(); self.avancar()
                            break
                        else:
                            self.avancar()
                    continue
                else:
                    # É apenas um operador de divisão
                    self.adicionar_token('T_OP_ARIT', '/', linha_inicio, coluna_inicio)
                    continue

            # Tokens de um único caractere
            if char_atual in TOKENS_DE_UM_CARACTERE:
                token_info = TOKENS_DE_UM_CARACTERE[char_atual]
                self.avancar()
                self.adicionar_token(token_info, char_atual, linha_inicio, coluna_inicio)
                continue

            # --- Etapa 5: Tratamento de Erros ---
            # Se chegou até aqui, o caractere é desconhecido
            self.adicionar_erro(f"Caractere desconhecido '{char_atual}'", linha_inicio, coluna_inicio)
            self.avancar()

        return self.tokens, self.tabela_simbolos, self.erros


def imprimir_resultados(tokens, tabela_simbolos, erros):
    print("\n--- LISTA DE TOKENS ---")
    if not tokens:
        print("  (Nenhum token foi reconhecido)")
    for token in tokens:
        tipo, lexema, linha, coluna = token
        print(f"  {tipo:20} | {lexema:25} | Linha {linha:3}, Coluna {coluna:3}")

    print("\n--- TABELA DE SÍMBOLOS (Identificadores) ---")
    if not tabela_simbolos:
        print("  (Vazia)")
    for identificador, pos in sorted(tabela_simbolos.items()):
        linha, coluna = pos
        print(f"  {identificador:20} | Visto pela primeira vez em Linha {linha}, Coluna {coluna}")

    print("\n--- RELATÓRIO DE ERROS LÉXICOS ---")
    if not erros:
        print("  (Nenhum erro encontrado)")
    for erro in erros:
        msg, linha, coluna = erro
        print(f"  ERRO: {msg} (Linha {linha}, Coluna {coluna})")
    print("\n" + "="*60 + "\n")


# Seção principal para demonstrar o funcionamento do analisador
if __name__ == "__main__":
    # Dicionário com códigos de exemplo para teste
    amostras_de_codigo = {
        "teste_completo": "if (x_val >= 10.5) { y = y + 1; } // fim da linha",
        "teste_comentario_bloco": "while (a != b) { /* comentario de bloco */ c = 3.14e-2; }",
        "teste_numeros": "x = .5; y = 123.; z = 5e;",
        "teste_logico": "a && b || !c;",
        "erro_comentario_nao_fechado": "int var = 1; /* este comentario nao fecha",
        "erro_simbolo_solto": "float val = 3.14 & 5;",
        "erro_caractere_invalido": "int resultado @= 10;",
        "teste dois pontos": "int resultado : 10;",
        "teste_docx": "int resultado = 10.5; if(resultado > 10) {resultado = resultado + 1;} /*Fim do teste &*/ &"
    }

    # Executa a análise para cada amostra de código
    for nome_amostra, codigo in amostras_de_codigo.items():
        print(f"Analisando amostra: '{nome_amostra}'")
        print(f"Código Fonte: {codigo}")
        
        analisador = AnalisadorLexico(codigo)
        tokens, simbolos, erros = analisador.analisar()
        
        imprimir_resultados(tokens, simbolos, erros)
