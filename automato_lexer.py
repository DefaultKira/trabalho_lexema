# Importações necessárias para anotação de tipos e para o sistema
from typing import List, Tuple, Optional, Dict, Any
import sys

# Dicionário que mapeia lexemas de palavras reservadas para seus tipos de token
PALAVRAS_RESERVADAS = {
    'int': 'T_TIPO', 'float': 'T_TIPO', 'char': 'T_TIPO', 'void': 'T_TIPO', 'double': 'T_TIPO',
    'if': 'IF',
    'else': 'ELSE',
    'for': 'FOR',
    'while': 'WHILE',
    'do': 'DO',
    'return': 'RETURN',
    'break': 'BREAK',
    'continue': 'CONTINUE'
}

# Dicionário para tokens simples de um único caractere
TOKENS_DE_UM_CARACTERE = {
    ';': ';',
    ',': ',',
    '(': '(',
    ')': ')',
    '{': '{',
    '}': '}',
    '+': 'T_OP_ARIT',
    '-': 'T_OP_ARIT',
    '*': 'T_OP_ARIT',
    '%': 'T_OP_ARIT',
    '.': '.',
    ':': ':',
}

class AnalisadorLexico:
    def __init__(self, codigo_fonte: str):
        self.codigo_fonte = codigo_fonte
        self.posicao_atual = 0
        self.linha = 1
        self.coluna = 1
        self.tokens: List[Tuple[str, str, int, int]] = []
        # Tabela de símbolos aprimorada para guardar mais informações
        self.tabela_simbolos: Dict[str, Dict[str, Any]] = {}
        self.proximo_id_simbolo = 1
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
        """Adiciona um token à lista e gerencia a tabela de símbolos."""
        if tipo == 'T_ID':
            if lexema not in self.tabela_simbolos:
                self.tabela_simbolos[lexema] = {
                    'id': self.proximo_id_simbolo,
                    'linha': linha,
                    'coluna': coluna
                }
                self.proximo_id_simbolo += 1
            # Para o token, usamos o ID da tabela de símbolos como lexema
            indice = self.tabela_simbolos[lexema]['id']
            self.tokens.append((tipo, str(indice), linha, coluna))
        else:
            self.tokens.append((tipo, lexema, linha, coluna))

    def adicionar_erro(self, mensagem: str, linha: int, coluna: int):
        self.erros.append((mensagem, linha, coluna))

    def _analisar_identificador_ou_palavra_reservada(self, linha_inicio, coluna_inicio):
        lexema = ''
        while self.ver_proximo() is not None and (self.ver_proximo().isalnum() or self.ver_proximo() == '_'):
            lexema += self.avancar()

        tipo_token = PALAVRAS_RESERVADAS.get(lexema, 'T_ID')
        self.adicionar_token(tipo_token, lexema, linha_inicio, coluna_inicio)

    def _analisar_numero(self, linha_inicio, coluna_inicio):
        lexema = ""
        is_float = False

        # Parte inteira (se houver)
        while self.ver_proximo() and self.ver_proximo().isdigit():
            lexema += self.avancar()

        # Verifica a parte fracionária
        if self.ver_proximo() == '.':
            char_apos_ponto = self.ver_proximo(1)
            
            # Caso 1: Ponto seguido por dígito (float válido)
            if char_apos_ponto and char_apos_ponto.isdigit():
                is_float = True
                lexema += self.avancar()  # consome o '.'
                while self.ver_proximo() and self.ver_proximo().isdigit():
                    lexema += self.avancar()
            
            # Caso 2: Ponto seguido por letra (número malformado)
            elif char_apos_ponto and char_apos_ponto.isalpha():
                lexema += self.avancar() # consome o '.'
                # Continua consumindo para capturar todo o lexema inválido
                while self.ver_proximo() and self.ver_proximo().isalnum():
                    lexema += self.avancar()
                self.adicionar_erro(f"Número malformado '{lexema}'. Após o ponto decimal, esperava-se um dígito.", linha_inicio, coluna_inicio)
                
                return # Encerra a análise deste número aqui

            # Caso 3: Ponto seguido por espaço, operador, etc.
            # Neste caso, o número é considerado um inteiro e o ponto será
            # processado como um token separado no laço principal. Não fazemos nada aqui.

        # Parte do expoente (aceita 'e', 'E', ou '^')
        proximo_char = self.ver_proximo()
        if proximo_char and proximo_char.lower() in ('e', '^'):
            is_float = True
            lexema += self.avancar()
            if self.ver_proximo() in ('+', '-'):
                lexema += self.avancar()

            if not (self.ver_proximo() and self.ver_proximo().isdigit()):
                self.adicionar_erro(f"Expoente malformado no número '{lexema}'", linha_inicio, coluna_inicio)
                self.adicionar_token('T_ERRO', lexema, linha_inicio, coluna_inicio)
                return

            while self.ver_proximo() and self.ver_proximo().isdigit():
                lexema += self.avancar()
        
        # Decide o tipo do token se não houve erro
        if is_float:
            self.adicionar_token('T_NUMERO_FLOAT', lexema, linha_inicio, coluna_inicio)
        elif lexema: # Garante que não criamos tokens vazios se a entrada for apenas "."
            self.adicionar_token('T_NUMERO_INT', lexema, linha_inicio, coluna_inicio)


    def _analisar_comentario_ou_divisao(self, linha_inicio, coluna_inicio):
        self.avancar() # Consome a primeira '/'
        proximo_char = self.ver_proximo()
        
        if proximo_char == '/': # Comentário de linha
            self.avancar()
            while self.ver_proximo() is not None and self.ver_proximo() != '\n':
                self.avancar()
        elif proximo_char == '*': # Comentário de bloco
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
        else: # Operador de divisão
            self.adicionar_token('T_OP_ARIT', '/', linha_inicio, coluna_inicio)

    def analisar(self):
        """Método principal que percorre o código fonte e gera os tokens."""
        while self.ver_proximo() is not None:
            char_atual = self.ver_proximo()

            if char_atual.isspace():
                self.avancar()
                continue

            linha_inicio, coluna_inicio = self.linha, self.coluna

            # Identificadores e Palavras Reservadas
            if char_atual.isalpha() or char_atual == '_':
                self._analisar_identificador_ou_palavra_reservada(linha_inicio, coluna_inicio)
                continue

            # Números (Inteiros ou Floats)
            if char_atual.isdigit() or (char_atual == '.' and self.ver_proximo(1) and self.ver_proximo(1).isdigit()):
                self._analisar_numero(linha_inicio, coluna_inicio)
                continue
            
            # Operador de Divisão ou Comentários
            if char_atual == '/':
                self._analisar_comentario_ou_divisao(linha_inicio, coluna_inicio)
                continue

            # Operadores relacionais e de atribuição
            if char_atual in ('=', '!', '<', '>'):
                lexema = self.avancar()
                if self.ver_proximo() == '=':
                    lexema += self.avancar()
                    self.adicionar_token('T_OP_REL', lexema, linha_inicio, coluna_inicio)
                else:
                    if lexema == '=': self.adicionar_token('T_ATRIBUICAO', lexema, linha_inicio, coluna_inicio)
                    elif lexema == '!': self.adicionar_token('T_OP_LOGICO', lexema, linha_inicio, coluna_inicio)
                    else: self.adicionar_token('T_OP_REL', lexema, linha_inicio, coluna_inicio)
                continue

            # Operadores lógicos '&&' e '||'
            if char_atual in ('&', '|'):
                char1 = self.avancar()
                if self.ver_proximo() == char1:
                    char2 = self.avancar()
                    self.adicionar_token('T_OP_LOGICO', char1 + char2, linha_inicio, coluna_inicio)
                else:
                    self.adicionar_erro(f"Operador incompleto '{char1}'. Esperava-se '{char1}{char1}'", linha_inicio, coluna_inicio)
                continue
            
            # Tokens de um único caractere definidos no dicionário
            if char_atual in TOKENS_DE_UM_CARACTERE:
                lexema = self.avancar()
                tipo_token = TOKENS_DE_UM_CARACTERE[lexema]
                self.adicionar_token(tipo_token, lexema, linha_inicio, coluna_inicio)
                continue

            # Se chegou até aqui, o caractere é desconhecido
            lexema_erro = self.avancar()
            self.adicionar_erro(f"Caractere desconhecido '{lexema_erro}'", linha_inicio, coluna_inicio)

        return self.tokens, self.tabela_simbolos, self.erros


def imprimir_resultados(tokens, tabela_simbolos, erros):
    print("\n--- LISTA DE TOKENS ---")
    if not tokens:
        print("  (Nenhum token foi reconhecido)")
    for token in tokens:
        tipo, lexema, linha, coluna = token
        if tipo == 'T_ID':
            lexema = f"ID, {lexema}"
        print(f"  {tipo:20} | {lexema:25} | Linha {linha:3}, Coluna {coluna:3}")

    print("\n--- TABELA DE SÍMBOLOS (Identificadores) ---")
    if not tabela_simbolos:
        print("  (Vazia)")
    # Ordena pela ID para manter a ordem de aparição
    for identificador, data in sorted(tabela_simbolos.items(), key=lambda item: item[1]['id']):
        idx = data['id']
        linha = data['linha']
        coluna = data['coluna']
        print(f"  ID {idx:3} -> {identificador:20} | Visto em Linha {linha}, Coluna {coluna}")

    print("\n--- RELATÓRIO DE ERROS LÉXICOS ---")
    if not erros:
        print("  (Nenhum erro encontrado)")
    for erro in erros:
        msg, linha, coluna = erro
        print(f"  ERRO: {msg} (Linha {linha}, Coluna {coluna})")
    print("\n" + "="*80 + "\n")


# Seção principal para demonstrar o funcionamento do analisador
if __name__ == "__main__":
    amostras = {
        "teste_docx_ajustado": "int resultado = 10.d; if(resultado > 10) {resultado = resultado + 1;}",
        "teste_completo": "if (x_val >= 10.5) { y = y + 1; } // fim da linha",
        "teste_comentario_bloco": "while (a != b) { /* comentario de bloco */ c = 3.14e-2; }",
        "teste_numeros": "x = .5; y = 123.; z = 5e;",
        "teste_expoente": "x = 5^4; y = 1+y^2;",
        "teste_logico": "a && b || !c;",
        "erro_comentario_nao_fechado": "int var = 1; /* este comentario nao fecha",
        "erro_simbolo_solto": "float val = 3.14 & 5;",
        "erro_caractere_invalido": "int resultado @= 10;",
        "teste dois pontos": "int resultado : 10;",
        "teste_docx": "int resultado = 10.5; if(resultado > 10) {resultado = resultado + 1;} /*Fim do teste &*/ &",
        "teste_aritmetico": "int soma = 1 + 3; float divisao = 2/4; int multi = 2*2; int expo = 2^3; int mod = 2%2"
    }

    for nome_amostra, codigo in amostras.items():
        print(f"Analisando amostra: '{nome_amostra}'")
        print(f"Código Fonte: `{codigo}`")
        
        analisador = AnalisadorLexico(codigo)
        tokens, simbolos, erros = analisador.analisar()
        
        imprimir_resultados(tokens, simbolos, erros)