# PTA Server — Protocolo de Transferência de Arquivos

**Discente:** Elen Cristina Rego Gomes — 202600470050

Implementação de um servidor TCP para o **Protocolo de Transferência de Arquivos (PTA)**, desenvolvida como parte de uma atividade prática de Computação em Nuvem.

## 1. Tecnologias e ambiente

- **Linguagem:** Python 3.
- **Sistema operacional utilizado:** Ubuntu 22.04.5 LTS.
- **Comunicação:** TCP/IP, utilizando sockets IPv4.
- **Bibliotecas:** `socket`, `pathlib` e `argparse`, todas pertencentes à biblioteca padrão do Python.

Não são necessárias dependências externas.

A implementação foi desenvolvida e testada no Ubuntu 22.04.5 LTS. Não há garantia de funcionamento em outros sistemas operacionais ou ambientes.

## 2. Estrutura do projeto

```text
PTA/
├── pta-server/
│   ├── files/
│   ├── users.txt
│   └── pta-server.py
├── pta-client.py
├── pta.pdf
└── README.md
```

- `pta-server/files/`: arquivos disponibilizados para transferência.
- `pta-server/users.txt`: lista de usuários autorizados.
- `pta-server/pta-server.py`: implementação do servidor.
- `pta-client.py`: cliente de testes fornecido.
- `pta.pdf`: especificação original do protocolo.

## 3. Configuração

### 3.1. Usuários

Os usuários autorizados são carregados de `users.txt`, com um nome por linha.

Exemplo:

```text
user1
user2
user3
```

A autenticação utiliza ASCII, diferencia letras maiúsculas de minúsculas e ignora linhas vazias.

### 3.2. Arquivos

Os arquivos disponibilizados devem ser armazenados em `files/`.

O servidor permite listar e transferir arquivos individuais. Os nomes não devem conter espaços, pois o protocolo utiliza espaços como separadores dos campos das mensagens.

São rejeitados caminhos externos ao diretório autorizado e links simbólicos.

## 4. Protocolo de comunicação

O servidor utiliza TCP na porta `11550`.

As requisições seguem o formato:

```text
SEQ_NUM COMMAND ARGS
```

As respostas seguem o formato:

```text
SEQ_NUM REPLY ARGS
```

Os campos textuais são separados por espaços. O conteúdo dos arquivos é transmitido em bytes, permitindo arquivos binários.

### 4.1. Comandos

| Comando | Requisição | Resposta de sucesso |
|---|---|---|
| `CUMP` | `SEQ_NUM CUMP usuario` | `SEQ_NUM OK` |
| `LIST` | `SEQ_NUM LIST` | `SEQ_NUM ARQS quantidade arquivos` |
| `PEGA` | `SEQ_NUM PEGA arquivo` | `SEQ_NUM ARQ tamanho bytes` |
| `TERM` | `SEQ_NUM TERM` | `SEQ_NUM OK` |

- **CUMP:** autentica o cliente. Deve ser obrigatoriamente a primeira operação. Usuários não cadastrados recebem `NOK` e têm a conexão encerrada.
- **LIST:** retorna a quantidade de arquivos disponíveis e seus nomes separados por vírgulas, sem espaços. Em caso de falha, retorna `NOK`.
- **PEGA:** solicita um único arquivo e retorna seu tamanho em bytes seguido de seu conteúdo binário. Arquivos inexistentes ou inválidos recebem `NOK`.
- **TERM:** responde `OK` e encerra a conexão.

### 4.2. Sequenciamento

O cliente escolhe o número de sequência inicial, que deve ser incrementado em uma unidade a cada nova requisição.

O servidor verifica se cada número recebido corresponde ao próximo esperado. As respostas utilizam o número da requisição correspondente.

- Sequência identificada, mas incorreta: `SEQ_NUM NOK`.
- Sequência não identificável: `err NOK`.

Uma sequência inválida não altera o número esperado pelo servidor.

## 5. Restrições e particularidades da implementação

### 5.1. Autenticação e comandos

- A primeira mensagem deve ser obrigatoriamente `CUMP`.
- Antes da autenticação, nenhum outro comando é permitido.
- Somente usuários presentes em `users.txt` são aceitos.
- Após a autenticação, são permitidos `LIST`, `PEGA` e `TERM`.
- `CUMP` e `PEGA` recebem um argumento; `LIST` e `TERM` não recebem argumentos.
- Apenas um arquivo pode ser solicitado por operação.
- Comandos desconhecidos ou malformados recebem `NOK`.
- Após a autenticação, erros de comando não implicam necessariamente o encerramento da conexão.
- Após `TERM`, a conexão é encerrada.

### 5.2. Recebimento de mensagens e timeout

Como o TCP não preserva os limites das mensagens, uma requisição pode chegar dividida em vários segmentos.

Para determinar o término das mensagens textuais, o servidor utiliza um timeout de **2 segundos** no recebimento:

1. Os segmentos recebidos são acumulados.
2. Enquanto novos dados chegam, a mensagem continua sendo processada.
3. Se nenhum dado adicional chegar durante 2 segundos, o servidor considera que a mensagem foi completamente recebida.
4. A mensagem acumulada é então interpretada.

Não existe um delimitador explícito de término para as mensagens textuais. Portanto, o timeout é utilizado como critério de conclusão, e uma mensagem incompleta também pode ser interpretada como completa.

### 5.3. Validação por prefixo

Durante a recepção de `CUMP` e `PEGA`, o servidor admite que o argumento recebido ainda possa estar incompleto.

Assim, uma substring pode ser considerada válida quando corresponde ao início de um usuário ou nome de arquivo cadastrado.

Por exemplo, considerando os usuários:

```text
user1
user2
```

O recebimento de:

```text
1 CUMP user1
```

pode ser aceito como usuário válido mesmo que o cliente pretendesse enviar `user13`, caso o caractere adicional não chegue antes da conclusão da mensagem.

A validação definitiva depende, portanto, dos dados recebidos e do timeout de 2 segundos.

### 5.4. Arquivos

- A transferência é realizada em formato binário.
- O tamanho informado corresponde à quantidade de bytes do arquivo.
- A listagem considera somente arquivos regulares.
- Caminhos externos ao diretório configurado e links simbólicos são rejeitados.
- Os nomes dos arquivos não devem conter espaços.

## 6. Instalação e execução

### 6.1. Requisitos

- Ubuntu 22.04.5 LTS (ambiente utilizado no desenvolvimento e nos testes).
- Python 3.
- Arquivo `users.txt` configurado.
- Diretório `files/` disponível.

Não é necessária a instalação de bibliotecas adicionais.

Verifique a instalação do Python:

```bash
python3 --version
```

### 6.2. Iniciar o servidor

A partir do diretório `pta-server`, execute:

```bash
python3 pta-server.py
```

Configuração padrão:

```text
IP: 0.0.0.0
PORTA: 11550
```

O endereço `0.0.0.0` permite receber conexões pelas interfaces IPv4 disponíveis.

### 6.3. Argumentos opcionais

| Argumento | Descrição | Padrão |
|---|---|---|
| `--host` ou `-ip` | Endereço IPv4 de escuta | `0.0.0.0` |
| `--usersFile` ou `-uf` | Arquivo de usuários | `users.txt` |
| `--directory` ou `-d` | Diretório de arquivos | `files` |

Exemplo:

```bash
python3 pta-server.py \
    --host 127.0.0.1 \
    --usersFile users.txt \
    --directory files
```

## 7. Testes

Para testar o servidor, utilize o cliente exemplo: [pta-client.py](https://github.com/elencris/PTA/blob/main/pta-client.py).

Com o servidor em execução, abra outro terminal e execute:

```bash
python3 pta-client.py
```

O cliente realiza testes de autenticação, listagem e transferência de arquivos. Esses testes não são abrangentes.

## 8. Encerramento

Para interromper o servidor manualmente, pressione `Ctrl + C`.

## 9. Referências

- [Especificação do Protocolo PTA (pta.pdf)](https://github.com/elencris/PTA/blob/main/pta.pdf)
- [Repositório original do projeto](https://github.com/glaucogoncalves/pta)
- [Documentação oficial do Python](https://docs.python.org/3/)