# Autômato Finito Determinístico (AFD) – Analisador Léxico

## 1. Classes de entrada (alfabeto simplificado)
Reduzir a complexidade

- **L** → letras ou `_` → `[a-zA-Z_]`
- **D** → dígitos → `[0-9]`
- **.** → ponto literal
- **=, !, <, >** → símbolos relacionais/atribuição
- **& , |** → operadores lógicos (início de `&&` ou `||`)
- **/** → operador ou início de comentário
- **\*** → usado em comentários `/* ... */`
- **S** → espaço, tabulação, nova linha → `[ \t\r\n]`
- **O** → outros delimitadores e operadores simples → `; , ( ) { } + - %`
- **EOF** → fim do arquivo

---

## 2. Tokens reconhecidos
- **Identificadores**: `T_ID`  
  (verificados depois na tabela de símbolos para palavras reservadas como `if`, `for`, `while` etc.)
- **Números inteiros**: `T_INT`
- **Números reais**: `T_FLOAT`
- **Operadores aritméticos**: `+ - * / %`
- **Operadores relacionais**: `== != <= >= < >`
- **Operadores lógicos**: `&& || !`
- **Atribuição**: `=`
- **Delimitadores**: `; , ( ) { }`
- **Comentários**:
  - Linha: `// ... \n`
  - Bloco: `/* ... */`  
    (erro se não fechar antes do EOF)
- **Erros léxicos**: `ERR_LEX`

---

## 3. Expressões regulares de referência
- Identificador: `[a-zA-Z_][a-zA-Z0-9_]*`
- Inteiro: `[0-9]+`
- Float: `[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?`
- Comentário de linha: `//[^\n]*`
- Comentário de bloco: `/\*([^*]|\*+[^*/])*\*+/`

---

## 4. Diagrama do AFD (ASCII simplificado)

Legenda: `->` início, `(A)` = estado de aceitação

-> q0  
|-- L --> qId (A: T_ID ou palavra reservada)  
|-- D --> qInt (A: T_INT)  
|-- . --> qDotStart (só válido se vier dígito → float)  
|-- = --> qEq ( '=' ou '' )  
|-- ! --> qBang ( '!' ou '!=' )  
|-- < --> qLT ( '<' ou '<=' )  
|-- > --> qGT ( '>' ou '>=' )  
|-- & --> qAmp ( '&&' )  
|-- | --> qPipe ( '||' )  
|-- / --> qSlash ( '/' , //coment , /_coment_/ )  
|-- S --> q0 (ignora espaço/tab/nova linha)  
|-- O --> qDelim (A: delimitadores simples)  
|-- EOF --> fim


---

## 5. Tabela de transição (simplificada)

| Estado        | L                                                                           | D     | .         | =       | !       | <       | >       | &       | \|      | /       | *       | S       | O       | EOF     |     |     |
| ------------- | --------------------------------------------------------------------------- | ----- | --------- | ------- | ------- | ------- | ------- | ------- | ------- | ------- | ------- | ------- | ------- | ------- | --- | --- |
| **q0**        | qId                                                                         | qInt  | qDotStart | qEq     | qBang   | qLT     | qGT     | qAmp    | qPipe   | qSlash  | ERR     | q0      | qDelim  | aceitar |     |     |
| **qId (A)**   | qId                                                                         | qId   | aceitar   | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar |     |     |
| **qInt (A)**  | aceitar                                                                     | qInt  | qDot      | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar |     |     |
| **qDotStart** | ERR                                                                         | qFrac | ERR       | ERR     | ERR     | ERR     | ERR     | ERR     | ERR     | ERR     | ERR     | ERR     | ERR     | ERR     |     |     |
| **qFrac (A)** | qFrac                                                                       | qFrac | aceitar   | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar | aceitar |     |     |
| **qEq**       | aceitar (=) ou '=='                                                         | ...   |           |         |         |         |         |         |         |         |         |         |         |         |     |     |
| **qBang**     | '!' ou '!='                                                                 |       |           |         |         |         |         |         |         |         |         |         |         |         |     |     |
| **qLT**       | '<' ou '<='                                                                 |       |           |         |         |         |         |         |         |         |         |         |         |         |     |     |
| **qGT**       | '>' ou '>='                                                                 |       |           |         |         |         |         |         |         |         |         |         |         |         |     |     |
| **qAmp**      | aceitar `&&`                                                                | ERR   |           |         |         |         |         |         |         |         |         |         |         |         |     |     |
| **qPipe**     | aceitar `                                                                   |       | `         | ERR     |         |         |         |         |         |         |         |         |         |         |     |     |
| **qSlash**    | '/' → comentário linha<br>`*` → comentário bloco<br>senão `/` como operador |       |           |         |         |         |         |         |         |         |         |         |         |         |     |     |

---

## 6. Estados de aceitação
- **qId** → `T_ID` (ou palavra reservada)  
- **qInt** → `T_INT`  
- **qFrac**, `qExpNum` → `T_FLOAT`  
- **qEq** → `=` (atribuição) ou `==` (relacional)  
- **qBang** → `!` (lógico) ou `!=` (relacional)  
- **qLT/qGT** → `< , <= , > , >=`  
- **qAmp** → `&&`  
- **qPipe** → `||`  
- **qSlash** → `/` (operação aritmética)  
- **qDelim** → `; , ( ) { } + - %`

---

## 7. Observações importantes
- Comentários são **ignorados** (não geram tokens).  
- Erros são reportados quando:
  - Caracter não pertence ao alfabeto.  
  - Comentário de bloco não é fechado antes do EOF.  
- Identificadores devem ser checados na tabela de símbolos para detectar palavras reservadas.

---

## 8. Funcionamento do Autômato

O autômato finito determinístico (AFD) do analisador léxico funciona da seguinte forma:

1. **Estado inicial (q0)**  
   - A leitura do código fonte sempre começa em `q0`.  
   - Cada caractere lido é classificado em uma **classe de entrada** (letra, dígito, operador, espaço, etc.).  
   - Com base nessa classe, o autômato faz uma transição para outro estado.

2. **Reconhecimento de lexemas**  
   - Se o primeiro caractere for uma letra (`L`), o autômato vai para `qId` e permanece lá enquanto ler letras ou dígitos, formando um **identificador**.  
   - Se for um dígito (`D`), vai para `qInt` e continua consumindo dígitos, formando um **número inteiro**.  
   - Caso encontre um ponto (`.`) após números, pode ir para `qFrac` e reconhecer um **número real**.  
   - Operadores como `=`, `<`, `>` e `!` exigem **lookahead** para decidir se serão simples (`=`, `<`, `>`, `!`) ou compostos (`==`, `<=`, `>=`, `!=`).  
   - Os símbolos `&` e `|` só são válidos se repetidos, formando `&&` ou `||`.  
   - O caractere `/` pode ser tanto um operador de divisão quanto o início de um comentário (`//` ou `/* ... */`).  

3. **Espaços e comentários**  
   - Espaços, tabulações e quebras de linha (`S`) são **ignorados** e o autômato retorna ao estado inicial `q0`.  
   - Comentários de linha são consumidos até o final da linha.  
   - Comentários de bloco são consumidos até encontrar `*/`. Se o arquivo terminar antes de fechar o comentário, o autômato gera um **erro léxico**.

4. **Estados de aceitação**  
   - Quando o autômato atinge um estado de aceitação, significa que reconheceu um token completo.  
   - O lexema formado é então classificado como **identificador, número, operador, delimitador** etc.  
   - Após reconhecer o token, o autômato volta para o estado inicial (`q0`) para continuar o processo com o próximo lexema.

5. **Erros léxicos**  
   - Se o autômato ler um caractere inválido (fora do alfabeto definido) ou encontrar uma sequência impossível (por exemplo, `&` sem o segundo `&`), ele gera um **token de erro** (`ERR_LEX`) indicando a posição no código.

---

### Resumindo
O autômato percorre o código fonte caractere a caractere, sempre mudando de estado conforme a **função de transição δ**.  
Quando chega em um estado de aceitação, ele produz um **token válido**.  
Esse processo se repete até o fim do arquivo (EOF), construindo assim a **lista de tokens** que será usada nas próximas fases do compilador.
