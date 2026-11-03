
# PTA Server — Protocolo de Transferência de Arquivos

Discente: Elen Cristina Rego Gomes - 202600470050

Implementação de um servidor TCP para o **Protocolo de Transferência de Arquivos (PTA)**, desenvolvido como parte de uma atividade prática de Computação em Nuvem.

O servidor permite que clientes autenticados consultem os arquivos disponíveis e solicitem sua transferência, seguindo as especificações do protocolo PTA.

## 1. Descrição do projeto

O PTA é um protocolo de aplicação didático cujo objetivo é permitir a transferência de arquivos armazenados no servidor para clientes conectados.

A comunicação é realizada utilizando TCP, com o servidor escutando na porta `11550`.

O servidor implementa quatro operações principais:

- **CUMP:** apresentação e autenticação do cliente.
- **LIST:** listagem dos arquivos disponíveis no servidor.
- **PEGA:** solicitação e transferência de um arquivo.
- **TERM:** encerramento da conexão.

As operações LIST e PEGA podem ser executadas em qualquer ordem após a autenticação, respeitando a sequência de mensagens estabelecida pelo protocolo.

## 2. Tecnologias utilizadas

- **Linguagem:** Python 3.
- **Comunicação:** TCP/IP utilizando sockets.
- **Bibliotecas:**
  - `socket`: implementação da comunicação TCP.
  - `pathlib`: manipulação e validação de caminhos e arquivos.
  - `argparse`: processamento de argumentos da linha de comando.

Todas as bibliotecas utilizadas pertencem à biblioteca padrão do Python, não sendo necessária a instalação de dependências externas.

## 3. Estrutura do projeto

```text
pta-server/
├── files/
│   └── arquivos disponibilizados pelo servidor
├── users.txt
├── pta-server.py
└── README.md
```

- `files/`: diretório contendo os arquivos disponibilizados para transferência.
- `users.txt`: arquivo contendo a lista de usuários autorizados.
- `pta-server.py`: implementação do servidor PTA.
- `README.md`: documentação do projeto.

Os diretórios `files/` e o arquivo `users.txt` devem ser mantidos conforme a configuração fornecida para a atividade.

## 4. Configuração

### 4.1. Lista de usuários

Os usuários autorizados são carregados a partir do arquivo `users.txt`.

Cada linha deve conter um nome de usuário.

Exemplo:

```text
usuario1
usuario2
usuario3
```

A autenticação diferencia letras maiúsculas de minúsculas e utiliza codificação ASCII.

### 4.2. Diretório de arquivos

Os arquivos disponibilizados pelo servidor devem estar no diretório `files/`.

O cliente poderá consultar os nomes dos arquivos disponíveis e solicitar a transferência de um arquivo por requisição.

O servidor valida os caminhos solicitados para impedir o acesso a arquivos externos ao diretório autorizado.

## 5. Protocolo de comunicação

Todas as mensagens seguem o formato:

```text
SEQ_NUM COMMAND ARGS
```

As respostas seguem o formato:

```text
SEQ_NUM REPLY ARGS
```

Os campos são separados por espaços.

### 5.1. Número de sequência

O campo `SEQ_NUM` identifica cada requisição enviada pelo cliente.

- O número inicial pode ser escolhido pelo cliente.
- A cada nova mensagem enviada, o número deve ser incrementado em uma unidade.
- A resposta do servidor utiliza o mesmo número de sequência da requisição correspondente.

### 5.2. Comando CUMP

Realiza a apresentação do cliente ao servidor.

Requisição:

```text
SEQ_NUM CUMP usuario
```

Respostas possíveis:

```text
SEQ_NUM OK
SEQ_NUM NOK
```

O servidor verifica se o usuário informado está presente em `users.txt`.

Caso o usuário seja válido, a conexão passa para o estado pronto.

Caso contrário, o servidor responde com NOK e encerra a conexão.

A apresentação deve ser obrigatoriamente a primeira operação do protocolo.

### 5.3. Comando LIST

Solicita a listagem dos arquivos disponíveis no servidor.

Requisição:

```text
SEQ_NUM LIST
```

Resposta:

```text
SEQ_NUM ARQS NUM_ARQUIVOS arquivo1,arquivo2,...,arquivoN
```

Caso não seja possível processar a solicitação, o servidor responde:

```text
SEQ_NUM NOK
```

Os nomes dos arquivos são separados por vírgulas, sem espaços entre eles.

### 5.4. Comando PEGA

Solicita a transferência de um arquivo específico.

Requisição:

```text
SEQ_NUM PEGA nome_do_arquivo
```

Resposta:

```text
SEQ_NUM ARQ TAMANHO arquivo_em_bytes
```

O campo `TAMANHO` representa o tamanho do arquivo em bytes.

O conteúdo é transmitido em formato binário, permitindo a transferência de diferentes tipos de arquivos.

Caso o arquivo não exista, não possa ser acessado ou a solicitação seja inválida, o servidor responde:

```text
SEQ_NUM NOK
```

O protocolo permite a solicitação de apenas um arquivo por requisição.

### 5.5. Comando TERM

Solicita o encerramento da conexão TCP.

Requisição:

```text
SEQ_NUM TERM
```

Resposta:

```text
SEQ_NUM OK
```

Após responder OK, o servidor encerra a conexão com o cliente.

## 6. Estados do servidor

O funcionamento do servidor pode ser dividido em dois estados principais:

### Estado de autenticação

- Aguarda obrigatoriamente uma mensagem CUMP.
- Verifica se o usuário está autorizado.
- Responde OK para usuários válidos.
- Responde NOK e encerra a conexão para usuários inválidos ou comandos diferentes de CUMP.

### Estado pronto

Após a autenticação, o servidor aceita os seguintes comandos:

- `LIST`: disponibiliza a listagem dos arquivos.
- `PEGA`: realiza a transferência de um arquivo.
- `TERM`: encerra a conexão.

Mensagens inválidas ou comandos não reconhecidos recebem uma resposta NOK.

O servidor também verifica a sequência das requisições para garantir a correspondência entre pedidos e respostas.

## 7. Instalação e execução

### 7.1. Requisitos

- Python 3 instalado.
- Sistema operacional com suporte a sockets TCP.
- Arquivo `users.txt` configurado.
- Diretório `files/` disponível.

Não é necessário instalar bibliotecas adicionais.

### 7.2. Verificar a instalação do Python

Execute:

```bash
python3 --version
```

### 7.3. Iniciar o servidor

A partir do diretório `pta-server`, execute:

```bash
python3 pta-server.py
```

Por padrão, o servidor será iniciado em:

```text
IP: 0.0.0.0
PORTA: 11550
```

O endereço `0.0.0.0` permite que o servidor aceite conexões pelas interfaces de rede disponíveis.

### 7.4. Configurar parâmetros de execução

O servidor também permite configurar o endereço IP (da família IPv4), o arquivo de usuários e o diretório de arquivos por meio de argumentos da linha de comando.

**Alterar o endereço IP:**

```bash
python3 pta-server.py --host 127.0.0.1
```

**Alterar o arquivo de usuários:**

```bash
python3 pta-server.py --usersFile usuarios.txt
```

**Alterar o diretório de arquivos:**

```bash
python3 pta-server.py --directory arquivos
```

**Configurar todos os parâmetros:**

```bash
python3 pta-server.py \
    --host 127.0.0.1 \
    --usersFile users.txt \
    --directory files
```

Também estão disponíveis os argumentos abreviados:

- `-ip`: endereço IP.
- `-uf`: arquivo de usuários.
- `-d`: diretório de arquivos.

## 8. Testes

Para testar o servidor, pode ser utilizado o cliente disponibilizado no projeto:

[pta-client.py](https://github.com/glaucogoncalves/pta/blob/master/pta-client.py)

Com o servidor em execução, abra outro terminal e execute o cliente:

```bash
python3 pta-client.py
```

O cliente realiza testes de comunicação com o servidor, incluindo autenticação, listagem e transferência de arquivos.

É importante executar o servidor antes de iniciar os testes do cliente.

## 9. Encerramento

Para encerrar o servidor manualmente, utilize:

```text
Ctrl + C
```

O servidor interromperá o loop principal e realizará o fechamento do socket de escuta.

## 10. Referências

- [Especificação do Protocolo PTA (pta.pdf)](https://github.com/glaucogoncalves/pta/blob/master/pta.pdf)
- [Repositório original do projeto](https://github.com/glaucogoncalves/pta)
- [Cliente de testes (pta-client.py)](https://github.com/glaucogoncalves/pta/blob/master/pta-client.py)
- [Documentação oficial do Python](https://docs.python.org/3/)

---