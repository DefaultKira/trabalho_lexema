from analisador_lexer import AnalisadorLexico
from analisador_sint import AnalisadorSintatico

def anexar_codigo(arquivo_txt: str, codigo_para_adicionar: str):
    with open(arquivo_txt, 'a', encoding='utf-8') as f:
        f.write('\n' + codigo_para_adicionar)

def ler_codigo(arquivo_txt: str) -> str:
    with open(arquivo_txt, 'r', encoding='utf-8') as f:
        return f.read()

def rodar_pipeline(arquivo_txt: str, anexar: str = None):
    # opcional: anexar código
    if anexar:
        anexar_codigo(arquivo_txt, anexar)
        print(f"[OK] Código anexado em '{arquivo_txt}'.")

    codigo = ler_codigo(arquivo_txt)
    print(f"[OK] Lido {len(codigo)} caracteres de '{arquivo_txt}'.\n")

    # 1) Léxico
    lexico = AnalisadorLexico(codigo)
    tokens, tabela_simbolos, erros_lex = lexico.analisar()

    print("=== ERROS LÉXICOS ===")
    if not erros_lex:
        print("Nenhum erro léxico.")
    else:
        for msg, ln, col in erros_lex:
            print(f"L{ln},C{col}: {msg}")

    # 2) Sintático (só roda se houver tokens; normalmente você roda mesmo com erros léxicos
    # mas o léxico pode deixar tokens inconsistentes)
    sint = AnalisadorSintatico(tokens)
    resultado = sint.analisar()
    print("\n=== ERROS SINTÁTICOS ===")
    # O analisador retorna (False, erros) ou (True,)
    if isinstance(resultado, tuple) and resultado[0] is False:
        erros_sint = resultado[1]
        if erros_sint:
            for e in erros_sint:
                print(e)
        else:
            print("Erro sintático reportado, mas lista vazia.")
    else:
        print("Nenhum erro sintático crítico (ou analisador retornou sucesso).")

if __name__ == "__main__":
    arquivo = "codigo.txt"
    codigo_para_adicionar = None
    # codigo_para_adicionar = "int x = 10.d;"  # exemplo que gera erro léxico

    rodar_pipeline(arquivo, anexar=codigo_para_adicionar)
