
# PTA Server — Protocolo de Transferência de Arquivos

**Discente:** Elen Cristina Rego Gomes — 202600470050

Implementação de um servidor TCP para o **Protocolo de Transferência de Arquivos (PTA)**, desenvolvida como parte de uma atividade prática de Computação em Nuvem.

O servidor permite que clientes autenticados consultem os arquivos disponíveis e solicitem sua transferência, seguindo as regras do protocolo PTA.

## 1. Tecnologias utilizadas

- **Linguagem:** Python 3.
- **Comunicação:** TCP/IP, utilizando sockets IPv4.
- **Bibliotecas:**
  - `socket`: comunicação TCP.
  - `pathlib`: manipulação e validação de caminhos e arquivos.
  - `argparse`: processamento de argumentos da linha de comando.

Todas as bibliotecas utilizadas pertencem à biblioteca padrão do Python. Portanto, não é necessária a instalação de dependências externas.

## 2. Estrutura do projeto

```text
pta-server/
├── files/
│   └── arquivos disponibilizados pelo servidor
├── users.txt
├── pta-server.py
└── README.md
```

- `files/`: diretório dos arquivos disponibilizados para transferência.
- `users.txt`: lista de usuários autorizados.
- `pta-server.py`: implementação do servidor.
- `README.md`: documentação do projeto.

Os arquivos e diretórios fornecidos originalmente para a atividade devem ser preservados.

## 3. Configuração

### 3.1. Usuários autorizados

Os usuários são carregados a partir de `users.txt`, com um nome por linha.

Exemplo:

```text
usuario1
usuario2
usuario3
```

A autenticação utiliza codificação ASCII e diferencia letras maiúsculas de minúsculas.

Nomes vazios são ignorados durante o carregamento.

### 3.2. Arquivos disponíveis

Os arquivos devem ser armazenados no diretório `files/`.

O servidor permite listar os arquivos disponíveis e solicitar sua transferência individual.

A validação dos caminhos impede a solicitação de arquivos localizados fora do diretório autorizado, além de rejeitar links simbólicos.

## 4. Protocolo de comunicação

A comunicação utiliza TCP na porta `11550`.

As mensagens seguem os formatos:

**Requisição:**

```text
SEQ_NUM COMMAND ARGS
```

**Resposta:**

```text
SEQ_NUM REPLY ARGS
```

Os campos textuais são separados por espaços. O conteúdo de arquivos, entretanto, é transmitido em bytes, podendo conter qualquer valor binário.

### 4.1. Número de sequência

O número de sequência identifica cada requisição do cliente.

- O valor inicial pode ser escolhido livremente pelo cliente.
- Cada nova requisição deve incrementar o número anterior em uma unidade.
- A resposta utiliza o mesmo número da requisição correspondente.
- O servidor verifica se o número recebido corresponde ao próximo número esperado.

Quando não é possível identificar um número de sequência válido, o servidor utiliza o identificador especial `err` na resposta:

```text
err NOK
```

Quando o número é identificado, mas não corresponde ao esperado, também é enviada uma resposta de erro com o identificador `err`, conforme a política de validação desta implementação.

### 4.2. Comandos disponíveis

| Comando | Requisição | Resposta de sucesso |
|---|---|---|
| `CUMP` | `SEQ_NUM CUMP usuario` | `SEQ_NUM OK` |
| `LIST` | `SEQ_NUM LIST` | `SEQ_NUM ARQS quantidade arquivos` |
| `PEGA` | `SEQ_NUM PEGA arquivo` | `SEQ_NUM ARQ tamanho bytes` |
| `TERM` | `SEQ_NUM TERM` | `SEQ_NUM OK` |

**CUMP — Apresentação**

É obrigatoriamente a primeira operação da conexão. O servidor verifica se o usuário informado pertence à lista de usuários autorizados.

- Usuário válido: responde `OK` e libera as demais operações.
- Usuário inválido: responde `NOK` e encerra a conexão.

**LIST — Listagem**

Retorna a quantidade de arquivos disponíveis e seus respectivos nomes, separados por vírgulas e sem espaços entre eles.

Exemplo:

```text
2 ARQS 3 arquivo1.txt,imagem.png,dados.pdf
```

Caso a operação não possa ser processada, retorna `NOK`.

**PEGA — Transferência**

Solicita um único arquivo por requisição. A resposta contém o tamanho do arquivo em bytes e seu conteúdo binário.

Exemplo:

```text
3 ARQ 1024 [conteúdo binário]
```

Caso o arquivo não exista, seja inválido ou não possa ser acessado, retorna `NOK`.

**TERM — Encerramento**

Encerra a comunicação após responder `OK`. Nenhuma outra operação deve ser realizada naquela conexão.

## 5. Restrições e particularidades da implementação

### 5.1. Autenticação

- A primeira mensagem deve obrigatoriamente ser `CUMP`.
- Não é permitido executar `LIST`, `PEGA` ou `TERM` antes da autenticação.
- Somente usuários cadastrados em `users.txt` são aceitos.
- A comparação dos nomes é sensível a maiúsculas e minúsculas.
- Usuários são representados em ASCII.

### 5.2. Comandos e argumentos

- Somente `CUMP`, `LIST`, `PEGA` e `TERM` são reconhecidos.
- `CUMP` e `PEGA` exigem exatamente um argumento.
- `LIST` e `TERM` não recebem argumentos.
- `PEGA` permite solicitar apenas um arquivo por vez.
- Os nomes dos arquivos devem corresponder a arquivos existentes no diretório autorizado.
- Não são aceitos caminhos que permitam acessar arquivos externos ao diretório configurado.
- Links simbólicos são rejeitados durante a solicitação de arquivos.
- Comandos inválidos recebem `NOK`. Após a autenticação, esses erros não implicam necessariamente o encerramento da conexão.

### 5.3. Recebimento das mensagens e timeout

A comunicação utiliza sockets TCP, que não preservam os limites das mensagens enviadas. Portanto, uma requisição pode chegar ao servidor dividida em vários segmentos.

Para determinar o término de uma mensagem textual, esta implementação utiliza um timeout de **2 segundos** no recebimento de dados.

O funcionamento é o seguinte:

1. O servidor recebe os dados enviados pelo cliente e acumula os segmentos recebidos.
2. Enquanto novos dados chegam, a mensagem continua sendo processada.
3. Se nenhum novo dado chegar durante 2 segundos, o servidor considera que a mensagem recebida está completa.
4. A mensagem acumulada é então interpretada e validada.

Essa estratégia possui uma particularidade: como não existe um delimitador explícito de término para os comandos textuais, uma mensagem pode ser considerada completa mesmo que o cliente tenha enviado apenas parte de seu conteúdo.

### 5.4. Validação por prefixo

Durante a interpretação de `CUMP` e `PEGA`, o servidor considera que um argumento pode ainda estar incompleto enquanto os dados continuam chegando.

Assim, uma substring pode ser aceita como válida quando corresponde ao início de um usuário ou nome de arquivo cadastrado.

Por exemplo, se o servidor possui os usuários:

```text
usuario1
usuario2
```

O recebimento de:

```text
1 CUMP usuario
```

pode ser considerado uma mensagem ainda incompleta, pois `usuario` é prefixo de usuários válidos.

A validação é concluída quando os dados adicionais chegam ou quando ocorre o timeout de 2 segundos.

Essa abordagem permite receber mensagens fragmentadas, mas também significa que a aceitação de argumentos depende do tempo de chegada dos dados.

### 5.5. Sequenciamento

- O primeiro número de sequência é definido pelo cliente.
- As requisições seguintes devem utilizar números consecutivos.
- O servidor mantém o próximo número esperado durante toda a conexão.
- Uma sequência incorreta recebe uma resposta de erro identificada por `err`.
- O servidor não altera a sequência esperada em caso de número inválido.

### 5.6. Transferência de arquivos

- Os arquivos são transmitidos em formato binário.
- O tamanho informado corresponde à quantidade de bytes do arquivo.
- Apenas um arquivo pode ser solicitado por operação.
- A listagem contém somente arquivos regulares encontrados no diretório configurado.
- Arquivos externos ao diretório autorizado não podem ser acessados.

## 6. Instalação e execução

### 6.1. Requisitos

- Python 3.
- Sistema operacional com suporte a sockets TCP.
- Arquivo `users.txt` configurado.
- Diretório `files/` disponível.

Não é necessária a instalação de pacotes adicionais.

### 6.2. Verificar a versão do Python

```bash
python3 --version
```

### 6.3. Iniciar o servidor

A partir do diretório `pta-server`, execute:

```bash
python3 pta-server.py
```

A configuração padrão utiliza:

```text
IP: 0.0.0.0
PORTA: 11550
```

O endereço `0.0.0.0` permite que o servidor aceite conexões pelas interfaces IPv4 disponíveis.

### 6.4. Argumentos de execução

O servidor permite personalizar os parâmetros por meio da linha de comando:

| Argumento | Descrição | Padrão |
|---|---|---|
| `--host` ou `-ip` | Endereço IPv4 de escuta | `0.0.0.0` |
| `--usersFile` ou `-uf` | Arquivo de usuários | `users.txt` |
| `--directory` ou `-d` | Diretório de arquivos | `files` |

Exemplo de configuração personalizada:

```bash
python3 pta-server.py \
    --host 127.0.0.1 \
    --usersFile users.txt \
    --directory files
```

## 7. Testes

O servidor pode ser testado utilizando o cliente disponibilizado no repositório original:

[pta-client.py](https://github.com/glaucogoncalves/pta/blob/master/pta-client.py)

Com o servidor em execução, abra outro terminal e execute:

```bash
python3 pta-client.py
```

O cliente realiza testes de comunicação, incluindo autenticação, listagem e transferência de arquivos.

## 8. Encerramento

Para interromper o servidor manualmente, utilize `Ctrl + C`.

O servidor interrompe o loop de atendimento e fecha seu socket de escuta.

## 9. Referências

- [Especificação do Protocolo PTA (pta.pdf)](https://github.com/glaucogoncalves/pta/blob/master/pta.pdf)
- [Repositório original do projeto](https://github.com/glaucogoncalves/pta)
- [Cliente de testes (pta-client.py)](https://github.com/glaucogoncalves/pta/blob/master/pta-client.py)
- [Documentação oficial do Python](https://docs.python.org/3/)

---

**Projeto desenvolvido para fins acadêmicos**, como exercício de implementação de protocolos de aplicação, comunicação TCP, sockets e transferência de arquivos.

