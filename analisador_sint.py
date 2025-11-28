import sys
from analisador_lexer import AnalisadorLexico

class AnalisadorSintatico:
    def __init__(self, tokens):
        """
        Inicializa o analisador sintático.
        :param tokens: Lista de tokens gerada pelo analisador léxico.
        """
        # Adiciona o marcador de fim de arquivo ($)
        # O formato do token do seu léxico é (tipo, lexema, linha, coluna)
        self.tokens = tokens + [('EOF', '$', -1, -1)]
        self.posicao = 0
        self.pilha = ['$']  # Pilha inicializada apenas com $
        self.pilha.append('PROGRAMA') # Empilha o símbolo inicial
        self.erros =[]
        
        # Mapeamento: Token do Léxico -> Terminal da Gramática
        self.mapa_terminais = {
            'T_TIPO': 'tipo',
            'T_ID': 'id',
            'T_NUMERO_INT': 'numero',
            'T_NUMERO_FLOAT': 'numero',
            'IF': 'if', 'ELSE': 'else', 'WHILE': 'while', 
            'DO': 'do', 'FOR': 'for', 'RETURN': 'return', 
            'BREAK': 'break', 'CONTINUE': 'continue',
            'T_OP_ARIT': 'op_arit', 'T_OP_REL': 'op_rel', 
            'T_OP_LOGICO': 'op_logico',
            '=': '=', ';': ';', ',': ',', 
            '(': '(', ')': ')', '{': '{', '}': '}',
            'EOF': 'EOF'
        }

        # --- TABELA SINTÁTICA LL(1) COMPLETA COM MODO PÂNICO ---
        # Chave: Não-Terminal
        # Valor: Dicionário { Terminal: Ação }
        # Ações:
        #   ('p',): Produção (Empilha B, depois A)
        #   ('epsilon',): Produção Vazia (Não empilha nada)
        #   ('sync',): Erro recuperável (Desempilha o Não-Terminal atual)
        self.tabela_m = self._construir_tabela_m()

    def _obter_terminal(self, token):
        """Traduz o token do léxico para a linguagem da gramática."""
        tipo, lexema, _, _ = token
        
        # Tenta mapear pelo tipo
        if tipo in self.mapa_terminais:
            return self.mapa_terminais[tipo]
        
        # Se for um operador ou pontuação que o léxico identificou pelo lexema
        if lexema in self.mapa_terminais:
            return self.mapa_terminais[lexema]
            
        return None

    def analisar(self):
        print(f"\n{'='*20} INICIANDO ANÁLISE SINTÁTICA {'='*20}")
        
        while len(self.pilha) > 0:
            topo = self.pilha[-1]
            token_atual = self.tokens[self.posicao]
            tipo_atual, lexema_atual, linha, coluna = token_atual
            terminal_atual = self._obter_terminal(token_atual)

            # Se o token não for mapeado (ex: erro léxico), ignoramos
            if terminal_atual is None:
                print(f"Ignorando token desconhecido na análise sintática: {lexema_atual}")
                self.posicao += 1
                continue

            # --- CASO 1: Sucesso ---
            if topo == '$' and terminal_atual == 'EOF':
                print(f"\n Pilha vazia e fim de arquivo alcançado.")
                break

            # --- CASO 2: Topo é Terminal ---
            if topo == terminal_atual:
                # Match! Consome o token e desempilha
                # print(f"  MATCH: {topo} == {lexema_atual}")
                self.pilha.pop()
                self.posicao += 1
                continue
            
            # Se topo é terminal mas não casou (e não é $), é um erro grave de correspondência
            if topo in self.mapa_terminais.values() or topo == '$':
                self._registrar_erro(f"Esperado '{topo}', mas encontrado '{lexema_atual}'", linha, coluna)
                self.pilha.pop() # Tenta recuperar desempilhando o terminal esperado que faltou
                continue

            # --- CASO 3: Topo é Não-Terminal ---
            if topo in self.tabela_m:
              linha_tabela = self.tabela_m[topo]
                          
              if terminal_atual in linha_tabela:
                  acao = linha_tabela[terminal_atual]   
                  tipo_acao = acao[0] if isinstance(acao, (list, tuple)) and len(acao) > 0 else None

                  if tipo_acao == 'p':
                      # Aplicar produção: desempilha A, empilha XYZ (em ordem inversa)
                      # Verifica se a produção veio junto com o marcador 'p'
                      if len(acao) >= 2 and isinstance(acao[1], (list, tuple)):
                          producao = acao[1]
                      else:
                          # Produção não especificada na tabela: erro de configuração da tabela M
                          self._registrar_erro(f"Configuração inválida da tabela (produçao ausente) para regra '{topo}' e terminal '{terminal_atual}'", linha, coluna)
                          # Para tentar recuperar, apenas desempilha o não-terminal
                          self.pilha.pop()
                          continue

                      self.pilha.pop()
                      # Empilha os símbolos da produção em ordem inversa (se produção for epsilon, nada a empilhar)
                      for simbolo in reversed(producao):
                          if simbolo != 'epsilon':
                              self.pilha.append(simbolo)

                  elif tipo_acao == 'epsilon':
                      # Aplicar produção vazia
                      self.pilha.pop()

                  elif tipo_acao == 'sync':
                      msg = f"Token inesperado '{lexema_atual}'. Assumindo ausência de '{topo}' para sincronizar."
                      self._registrar_erro(msg, linha, coluna)
                      self.pilha.pop()

                  else:
                      # Ação desconhecida — relatório e recuperação simples
                      self._registrar_erro(f"Ação desconhecida na tabela M para '{topo}' e '{terminal_atual}': {acao}", linha, coluna)
                      self.posicao += 1

                  if self.erros:
                      print(f"\nAnálise finalizada com {len(self.erros)} erros.")
                      return False, self.erros
                  else:
                      print("\nAnálise finalizada sem erros!")
                      return True,

    def _registrar_erro(self, msg, linha, coluna):
        erro_fmt = f"ERRO SINTÁTICO (L{linha}, C{coluna}): {msg}"
        print(erro_fmt)
        self.erros.append(erro_fmt)

    def _construir_tabela_m(self):
        return {
            # PROGRAMA -> LISTA_DECL_EXTERNAS
            'PROGRAMA': {
                'tipo': ('p', ['LISTA_DECL_EXTERNAS']),
                'EOF': ('epsilon',)
            },

            # LISTA_DECL_EXTERNAS -> DECL_EXTERNA LISTA_DECL_EXTERNAS | epsilon
            'LISTA_DECL_EXTERNAS': {
                'tipo': ('p', ['DECL_EXTERNA', 'LISTA_DECL_EXTERNAS']),
                'EOF': ('epsilon',)
            },

            # DECL_EXTERNA -> tipo id DECL_RESTO
            'DECL_EXTERNA': {
                'tipo': ('p', ['tipo', 'id', 'DECL_RESTO'])
            },

            # DECL_RESTO -> ( PARAMS ) BLOCO
            #            -> INICIALIZACAO_OPCIONAL LISTA_IDS_RESTO ;
            'DECL_RESTO': {
                '(': ('p', ['(', 'PARAMS', ')', 'BLOCO']),   # função
                '=': ('p', ['INICIALIZACAO_OPCIONAL', 'LISTA_IDS_RESTO', ';']),
                ',': ('p', ['INICIALIZACAO_OPCIONAL', 'LISTA_IDS_RESTO', ';']),
                ';': ('p', ['INICIALIZACAO_OPCIONAL', 'LISTA_IDS_RESTO', ';'])
            },

            # PARAMS -> LISTA_PARAMS | epsilon
            'PARAMS': {
                'tipo': ('p', ['LISTA_PARAMS']),
                ')': ('epsilon',)
            },

            # LISTA_PARAMS -> PARAMETRO LISTA_PARAMS_RESTO
            'LISTA_PARAMS': {
                'tipo': ('p', ['PARAMETRO', 'LISTA_PARAMS_RESTO'])
            },

            # LISTA_PARAMS_RESTO -> , PARAMETRO LISTA_PARAMS_RESTO | epsilon
            'LISTA_PARAMS_RESTO': {
                ',': ('p', [',', 'PARAMETRO', 'LISTA_PARAMS_RESTO']),
                ')': ('epsilon',)
            },

            # PARAMETRO -> tipo id
            'PARAMETRO': {
                'tipo': ('p', ['tipo', 'id'])
            },

            # INICIALIZACAO_OPCIONAL -> = EXPRESSAO | epsilon
            'INICIALIZACAO_OPCIONAL': {
                '=': ('p', ['=', 'EXPRESSAO']),
                ',': ('epsilon',), ';': ('epsilon',)
            },

            # LISTA_IDS_RESTO -> , id INICIALIZACAO_OPCIONAL LISTA_IDS_RESTO | epsilon
            'LISTA_IDS_RESTO': {
                ',': ('p', [',', 'id', 'INICIALIZACAO_OPCIONAL', 'LISTA_IDS_RESTO']),
                ';': ('epsilon',)
            },

            # BLOCO -> { LISTA_COMANDOS }
            'BLOCO': {
                '{': ('p', ['{', 'LISTA_COMANDOS', '}'])
            },

            # LISTA_COMANDOS -> COMANDO LISTA_COMANDOS | epsilon
            'LISTA_COMANDOS': {
                'if': ('p', ['COMANDO', 'LISTA_COMANDOS']),
                'while': ('p', ['COMANDO', 'LISTA_COMANDOS']),
                'do': ('p', ['COMANDO', 'LISTA_COMANDOS']),
                'for': ('p', ['COMANDO', 'LISTA_COMANDOS']),
                'return': ('p', ['COMANDO', 'LISTA_COMANDOS']),
                'break': ('p', ['COMANDO', 'LISTA_COMANDOS']),
                'continue': ('p', ['COMANDO', 'LISTA_COMANDOS']),
                'id': ('p', ['COMANDO', 'LISTA_COMANDOS']),
                '{': ('p', ['COMANDO', 'LISTA_COMANDOS']),
                '}': ('epsilon',)
            },

            # COMANDO -> CMD_IF | CMD_WHILE | CMD_DO_WHILE | CMD_FOR | CMD_RETURN |
            #            CMD_BREAK | CMD_CONTINUE | CMD_ATRIBUICAO | BLOCO
            'COMANDO': {
                'if': ('p', ['CMD_IF']),
                'while': ('p', ['CMD_WHILE']),
                'do': ('p', ['CMD_DO_WHILE']),
                'for': ('p', ['CMD_FOR']),
                'return': ('p', ['CMD_RETURN']),
                'break': ('p', ['CMD_BREAK']),
                'continue': ('p', ['CMD_CONTINUE']),
                'id': ('p', ['ATRIBUICAO_SIMPLES', ';']),
                '{': ('p', ['BLOCO'])
            },

            # CMD_IF -> if ( EXPRESSAO ) COMANDO CMD_IF_RESTO
            'CMD_IF': {
                'if': ('p', ['if', '(', 'EXPRESSAO', ')', 'COMANDO', 'CMD_IF_RESTO'])
            },

            # CMD_IF_RESTO -> else COMANDO | epsilon
            'CMD_IF_RESTO': {
                'else': ('p', ['else', 'COMANDO']),
                # follow(COMD_IF_RESTO) -> begin tokens of COMANDO and '}' and EOF
                'if': ('epsilon',), 'while': ('epsilon',), 'do': ('epsilon',),
                'for': ('epsilon',), 'return': ('epsilon',), 'break': ('epsilon',),
                'continue': ('epsilon',), 'id': ('epsilon',), '{': ('epsilon',),
                '}': ('epsilon',), 'EOF': ('epsilon',)
            },

            # CMD_WHILE -> while ( EXPRESSAO ) COMANDO
            'CMD_WHILE': {
                'while': ('p', ['while', '(', 'EXPRESSAO', ')', 'COMANDO'])
            },

            # CMD_DO_WHILE -> do BLOCO while ( EXPRESSAO ) ;
            'CMD_DO_WHILE': {
                'do': ('p', ['do', 'BLOCO', 'while', '(', 'EXPRESSAO', ')', ';'])
            },

            # CMD_FOR -> for ( ATRIBUICAO_SIMPLES ; EXPRESSAO ; ATRIBUICAO_SIMPLES ) COMANDO
            'CMD_FOR': {
                'for': ('p', ['for', '(', 'ATRIBUICAO_SIMPLES', ';', 'EXPRESSAO', ';', 'ATRIBUICAO_SIMPLES', ')', 'COMANDO'])
            },

            # ATRIBUICAO_SIMPLES -> id = EXPRESSAO
            'ATRIBUICAO_SIMPLES': {
                'id': ('p', ['id', '=', 'EXPRESSAO'])
            },

            # CMD_RETURN -> return EXPRESSAO ;
            'CMD_RETURN': {
                'return': ('p', ['return', 'EXPRESSAO', ';'])
            },

            # CMD_BREAK -> break ;
            'CMD_BREAK': {
                'break': ('p', ['break', ';'])
            },

            # CMD_CONTINUE -> continue ;
            'CMD_CONTINUE': {
                'continue': ('p', ['continue', ';'])
            },

            # EXPRESSAO -> EXPR_RELACIONAL EXPR_LOGICA_LINHA
            'EXPRESSAO': {
                '(': ('p', ['EXPR_RELACIONAL', 'EXPR_LOGICA_LINHA']),
                'id': ('p', ['EXPR_RELACIONAL', 'EXPR_LOGICA_LINHA']),
                'numero': ('p', ['EXPR_RELACIONAL', 'EXPR_LOGICA_LINHA'])
            },

            # EXPR_LOGICA_LINHA -> op_logico EXPR_RELACIONAL EXPR_LOGICA_LINHA | epsilon
            'EXPR_LOGICA_LINHA': {
                'op_logico': ('p', ['op_logico', 'EXPR_RELACIONAL', 'EXPR_LOGICA_LINHA']),
                ')': ('epsilon',), ';': ('epsilon',), ',': ('epsilon',), '}': ('epsilon',),
                'else': ('epsilon',), 'EOF': ('epsilon',)
            },

            # EXPR_RELACIONAL -> EXPR_ARITMETICA EXPR_RELACIONAL_LINHA
            'EXPR_RELACIONAL': {
                '(': ('p', ['EXPR_ARITMETICA', 'EXPR_RELACIONAL_LINHA']),
                'id': ('p', ['EXPR_ARITMETICA', 'EXPR_RELACIONAL_LINHA']),
                'numero': ('p', ['EXPR_ARITMETICA', 'EXPR_RELACIONAL_LINHA'])
            },

            # EXPR_RELACIONAL_LINHA -> op_rel EXPR_ARITMETICA | epsilon
            'EXPR_RELACIONAL_LINHA': {
                'op_rel': ('p', ['op_rel', 'EXPR_ARITMETICA']),
                'op_logico': ('epsilon',), ')': ('epsilon',), ';': ('epsilon',), ',': ('epsilon',),
                '}': ('epsilon',), 'else': ('epsilon',), 'EOF': ('epsilon',)
            },

            # EXPR_ARITMETICA -> FATOR EXPR_ARITMETICA_LINHA
            'EXPR_ARITMETICA': {
                '(': ('p', ['FATOR', 'EXPR_ARITMETICA_LINHA']),
                'id': ('p', ['FATOR', 'EXPR_ARITMETICA_LINHA']),
                'numero': ('p', ['FATOR', 'EXPR_ARITMETICA_LINHA'])
            },

            # EXPR_ARITMETICA_LINHA -> op_arit FATOR EXPR_ARITMETICA_LINHA | epsilon
            'EXPR_ARITMETICA_LINHA': {
                'op_arit': ('p', ['op_arit', 'FATOR', 'EXPR_ARITMETICA_LINHA']),
                'op_rel': ('epsilon',), 'op_logico': ('epsilon',), ')': ('epsilon',), ';': ('epsilon',),
                ',': ('epsilon',), '}': ('epsilon',), 'else': ('epsilon',), 'EOF': ('epsilon',)
            },

            # FATOR -> ( EXPRESSAO ) | id | numero
            'FATOR': {
                '(': ('p', ['(', 'EXPRESSAO', ')']),
                'id': ('p', ['id']),
                'numero': ('p', ['numero']),
                # Em caso de sincronização em expressões
                'op_arit': ('sync',), 'op_rel': ('sync',), 'op_logico': ('sync',),
                ')': ('sync',), ';': ('sync',), ',': ('sync',)
            }
        }


# --- Integração e Teste ---
if __name__ == "__main__":
    # Coloque aqui a classe AnalisadorLexico que você forneceu
    # (Ou assuma que ela está definida acima)
    
    # Exemplo complexo para testar tudo (for, funções, if-else, expressoes)
    codigo_teste = """
    float calcular_soma(int limite) {
        float soma = 0.0;
        int i;
        for (i = 1; i < limite; i = i + 1) {
            if (soma > 1000.5) {
                break;
            } else {
                soma = soma + i;
            }
        }
        return soma;
    }
    """
    
    # Exemplo com erro para testar MODO PÂNICO
    codigo_erro = """
    int main() {
        int x = 10
        if (x > ) {  
            x = x + 1;
        }
    }
    """

    print("--- TESTE 1: Código Válido ---")
    # Instanciando seu léxico (assumindo que a classe AnalisadorLexico está disponível)
    lexico1 = AnalisadorLexico(codigo_teste) 
    tokens1, _, _ = lexico1.analisar()
    
    sintatico1 = AnalisadorSintatico(tokens1)
    sintatico1.analisar()

    print("\n--- TESTE 2: Código com Erros (Panic Mode) ---")
    lexico2 = AnalisadorLexico(codigo_erro)
    tokens2, _, _ = lexico2.analisar()
    
    sintatico2 = AnalisadorSintatico(tokens2)
    sintatico2.analisar()