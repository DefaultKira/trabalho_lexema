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
        """Retorna a Tabela M baseada na Gramática de 30 regras."""
        return {
            'PROGRAMA': {
                'tipo': ('p',),
                'EOF': ('p',)
            },
            'LISTA_DECL_EXTERNAS': {
                'tipo': ('p',),
                'EOF': ('epsilon',)
            },
            'DECL_EXTERNA': {
                'tipo': ('p',)
            },
            'DECL_RESTO': {
                '(': ('p',),
                '=': ('p',),
                ',': ('p',),
                ';': ('p',)
            },
            'PARAMS': {
                'tipo': ('p',),
                ')': ('epsilon',)
            },
            'LISTA_PARAMS': {
                'tipo': ('p',)
            },
            'LISTA_PARAMS_RESTO': {
                ',': ('p',),
                ')': ('epsilon',)
            },
            'PARAMETRO': {
                'tipo': ('p', ['tipo', 'id'])
            },
            'INICIALIZACAO_OPCIONAL': {
                '=': ('p',),
                ',': ('epsilon',),
                ';': ('epsilon',)
            },
            'LISTA_IDS_RESTO': {
                ',': ('p',),
                ';': ('epsilon',)
            },
            'BLOCO': {
                '{': ('p',),
                # SYNC (Follow)
                'if': ('sync',), 'while': ('sync',), 'do': ('sync',), 'for': ('sync',),
                'return': ('sync',), 'break': ('sync',), 'continue': ('sync',), 
                'id': ('sync',), 'else': ('sync',), 'tipo': ('sync',), 'EOF': ('sync',)
            },
            'LISTA_COMANDOS': {
                'if': ('p',),
                'while': ('p',),
                'do': ('p',),
                'for': ('p',),
                'return': ('p',),
                'break': ('p',),
                'continue': ('p',),
                'id': ('p',),
                '{': ('p',),
                '}': ('epsilon',)
            },
            'COMANDO': {
                'if': ('p',),
                'while': ('p',),
                'do': ('p',),
                'for': ('p',),
                'return': ('p',),
                'break': ('p',),
                'continue': ('p',),
                'id': ('p',),
                '{': ('p',),
                # SYNC (Follow)
                'else': ('sync',), '}': ('sync',), 'EOF': ('sync',)
            },
            'CMD_IF': {
                'if': ('p',)
            },
            'CMD_IF_RESTO': {
                'else': ('p',),
                # Epsilon para Follow(CMD_IF_RESTO) -> Follow(COMANDO)
                'if': ('epsilon',), 'while': ('epsilon',), 'do': ('epsilon',),
                'for': ('epsilon',), 'return': ('epsilon',), 'break': ('epsilon',),
                'continue': ('epsilon',), 'id': ('epsilon',), '{': ('epsilon',),
                '}': ('epsilon',), 'EOF': ('epsilon',)
            },
            'CMD_WHILE': {
                'while': ('p',)
            },
            'CMD_DO_WHILE': {
                'do': ('p',)
            },
            'CMD_FOR': {
                'for': ('p',)
            },
            'ATRIBUICAO_SIMPLES': {
                'id': ('p',)
            },
            'CMD_RETURN': {
                'return': ('p',)
            },
            'CMD_BREAK': {
                'break': ('p', ['break', ';'])
            },
            'CMD_CONTINUE': {
                'continue': ('p', ['continue', ';'])
            },
            'CMD_ATRIBUICAO': {
                'id': ('p',)
            },
            # --- EXPRESSÕES ---
            'EXPRESSAO': {
                '(': ('p',),
                'id': ('p',),
                'numero': ('p',),
                # SYNC
                ')': ('sync',), ';': ('sync',), ',': ('sync',)
            },
            'EXPR_LOGICA_LINHA': {
                'op_logico': ('p',),
                ')': ('epsilon',), ';': ('epsilon',), ',': ('epsilon',)
            },
            'EXPR_RELACIONAL': {
                '(': ('p',),
                'id': ('p',),
                'numero': ('p',),
                # SYNC
                'op_logico': ('sync',), ')': ('sync',), ';': ('sync',), ',': ('sync',)
            },
            'EXPR_RELACIONAL_LINHA': {
                'op_rel': ('p',),
                'op_logico': ('epsilon',), ')': ('epsilon',), ';': ('epsilon',), ',': ('epsilon',)
            },
            'EXPR_ARITMETICA': {
                '(': ('p',),
                'id': ('p',),
                'numero': ('p',),
                # SYNC
                'op_rel': ('sync',), 'op_logico': ('sync',), ')': ('sync',), ';': ('sync',), ',': ('sync',)
            },
            'EXPR_ARITMETICA_LINHA': {
                'op_arit': ('p',),
                'op_rel': ('epsilon',), 'op_logico': ('epsilon',), 
                ')': ('epsilon',), ';': ('epsilon',), ',': ('epsilon',)
            },
            'FATOR': {
                '(': ('p',),
                'id': ('p', ['id']),
                'numero': ('p', ['numero']),
                # SYNC
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