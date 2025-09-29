# Autômato Finito Determinístico (AFD) – Análise Léxica

Este documento descreve o projeto teórico do Analisador Léxico, detalhando desde a categorização dos caracteres de entrada até o funcionamento completo do autômato.

## 1. Classes de Entrada (Alfabeto Simplificado)

Para reduzir a complexidade do autômato, os caracteres do código-fonte são agrupados em classes de entrada.

- **L** → Letras ou `_` → `[a-zA-Z_]`
- **D** → Dígitos → `[0-9]`
- **.** → Ponto literal
- **=, !, <, >** → Símbolos que iniciam operadores relacionais ou de atribuição
- **& , |** → Símbolos que iniciam operadores lógicos (`&&` ou `||`)
- **/** → Símbolo de operador aritmético ou início de comentário
- **\*** → Caractere usado para finalizar comentários de bloco `/* ... */`
- **S** → Espaços, tabulação, nova linha → `[ \t\r\n]`
- **O** → Outros delimitadores e operadores simples → `; , ( ) { } + - %`
- **EOF** → Marcador de Fim de Arquivo (End of File)

---

## 2. Tokens Reconhecidos

O analisador léxico é responsável por identificar os seguintes tokens na linguagem:

- **Identificadores**: `T_ID`
  (Após o reconhecimento, são verificados na tabela de símbolos para identificar se são palavras reservadas como `if`, `for`, `while`, etc.)
- **Números Inteiros**: `T_NUMERO_INT`
- **Números de Ponto Flutuante**: `T_NUMERO_FLOAT`
- **Operadores Aritméticos**: `+ - * / %`
- **Operadores Relacionais**: `== != <= >= < >`
- **Operadores Lógicos**: `&& || !`
- **Atribuição**: `T_ATRIBUICAO` (`=`)
- **Delimitadores**: `; , ( ) { }`
- **Comentários**:
  - **Linha**: `// ... \n` (Ignorado, não gera token)
  - **Bloco**: `/* ... */` (Ignorado, não gera token)
- **Erros Léxicos**: `T_ERRO_LEX`
  (Gerado para caracteres ou sequências inválidas)

---

## 3. Expressões Regulares de Referência

As expressões regulares a seguir definem formalmente os padrões para os principais tokens:

- **Identificador**: `[a-zA-Z_][a-zA-Z0-9_]*`
- **Número Inteiro**: `[0-9]+`
- **Número Float**: `[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?`
- **Comentário de Linha**: `//[^\n]*`
- **Comentário de Bloco**: `/\*([^*]|\*+[^*/])*\*+/`

---

## 4. Diagrama do AFD (Simplificado)

**Legenda:** `->` Estado Inicial, `(A)` = Estado de Aceitação (Final)

-> q0 (Inicial)
|-- L --> q_Id (A: T_ID ou Palavra Reservada)
|-- D --> q_Int (A: T_NUMERO_INT)
|-- . --> q_Ponto (Válido apenas se seguido por dígito → T_NUMERO_FLOAT)
|-- = --> q_Igual (Pode ser '=' ou '==')
|-- ! --> q_Exclamacao (Pode ser '!' ou '!=')
|-- < --> q_Menor (Pode ser '<' ou '<=')
|-- > --> q_Maior (Pode ser '>' ou '>=')
|-- & --> q_EComercial (Deve formar '&&')
|-- | --> q_BarraVertical (Deve formar '||')
|-- / --> q_Barra (Pode ser '/', '//' ou '/\*')
|-- S --> q0 (Ignora espaço, tabulação ou nova linha)
|-- O --> q_Delimitador (A: Delimitadores simples como ';', '(', etc.)
|-- EOF --> Fim da Análise

---

## 5. Tabela de Transição (Simplificada)

A tabela de transição descreve para qual estado o autômato se move a partir de um estado atual e um caractere de entrada.

| Estado           | Entrada: L         | Entrada: D         | Entrada: .         | Entrada: =                   | Entrada: /                                                                          | Entrada: S | Entrada: O         |
| ---------------- | ------------------ | ------------------ | ------------------ | ---------------------------- | ----------------------------------------------------------------------------------- | ---------- | ------------------ |
| **q0**           | q_Id               | q_Int              | q_Ponto            | q_Igual                      | q_Barra                                                                             | q0         | q_Delimitador      |
| **q_Id (A)**     | q_Id               | q_Id               | _Finaliza Token_   | _Finaliza Token_             | _Finaliza Token_                                                                    | _Finaliza_ | _Finaliza Token_   |
| **q_Int (A)**    | _Finaliza Token_   | q_Int              | q_Fracao           | _Finaliza Token_             | _Finaliza Token_                                                                    | _Finaliza_ | _Finaliza Token_   |
| **q_Ponto**      | _ERRO_             | q_Fracao           | _ERRO_             | _ERRO_                       | _ERRO_                                                                              | _ERRO_     | _ERRO_             |
| **q_Fracao (A)** | _Finaliza Token_   | q_Fracao           | _Finaliza Token_   | _Finaliza Token_             | _Finaliza Token_                                                                    | _Finaliza_ | _Finaliza Token_   |
| **q_Igual**      | _Finaliza com '='_ | _Finaliza com '='_ | _Finaliza com '='_ | _Transita para q_IgualIgual_ | _Finaliza com '='_                                                                  | _Finaliza_ | _Finaliza com '='_ |
| **q_Barra**      | _Finaliza com '/'_ | _Finaliza com '/'_ | _Finaliza com '/'_ | _Finaliza com '/'_           | _Inicia Comentário de Linha_ <br/> Se próximo for `*`: _Inicia Comentário de Bloco_ | _Finaliza_ | _Finaliza com '/'_ |

---

## 6. Estados de Aceitação

Quando o autômato para em um estado de aceitação, um token é gerado:

- **q_Id**: `T_ID` (ou Palavra Reservada após consulta à tabela)
- **q_Int**: `T_NUMERO_INT`
- **q_Fracao**: `T_NUMERO_FLOAT`
- **q_Igual**: `T_ATRIBUICAO` (`=`) ou `T_OP_REL` (`==`)
- **q_Exclamacao**: `T_OP_LOGICO` (`!`) ou `T_OP_REL` (`!=`)
- **q_Menor/q_Maior**: `T_OP_REL` (`<`, `<=`, `>`, `>=`)
- **q_EComercial**: `T_OP_LOGICO` (`&&`)
- **q_BarraVertical**: `T_OP_LOGICO` (`||`)
- **q_Barra**: `T_OP_ARIT` (`/`)
- **q_Delimitador**: Tokens como `T_PONTO_VIRGULA`, `T_PARENTESES_ESQ`, etc.

---

## 7. Observações Importantes

- **Comentários**: São completamente **ignorados** e não geram tokens.
- **Erros**: São reportados quando um caractere não pertence ao alfabeto da linguagem ou uma sequência inválida é formada (ex: um `&` sozinho).
- **Identificadores vs. Palavras Reservadas**: Todo lexema que corresponde ao padrão de `T_ID` é primeiro reconhecido como tal. Em seguida, o analisador consulta uma lista de palavras reservadas. Se o lexema estiver nessa lista, seu token é especializado (ex: de `T_ID` para `T_IF`).

---

## 8. Funcionamento do Autômato

O processo de análise léxica segue um fluxo contínuo:

1.  **Estado Inicial (`q0`)**: A análise sempre começa aqui.
2.  **Transição de Estado**: A cada caractere lido, o autômato transita para um novo estado. Espaços em branco simplesmente retornam o autômato para `q0`.
3.  **Reconhecimento de Lexemas**: O autômato continua consumindo caracteres e transitando entre estados até não poder mais formar um lexema válido (ex: um espaço após um número).
4.  **Lookahead (Olhar à Frente)**: Para operadores como `=`, `<`, `>` e `!`, o autômato precisa "espiar" o próximo caractere para decidir se forma um token simples (`=`) ou composto (`==`).
5.  **Geração de Token**: Ao finalizar o reconhecimento de um lexema, o autômato atinge um estado de aceitação, gera o token correspondente e retorna ao estado inicial (`q0`) para processar o restante do código.
6.  **Detecção de Erros**: Se o autômato está em um estado e lê um caractere para o qual não há transição válida, um erro léxico é registrado com a linha e coluna.

### Resumo do Processo

O autômato percorre o código-fonte caractere a caractere, mudando de estado conforme a **função de transição**. Ao chegar a um estado de aceitação, ele emite um **token válido**. Esse ciclo se repete até o fim do arquivo (EOF), gerando a **lista de tokens** que alimentará a próxima fase do compilador: a análise sintática.
