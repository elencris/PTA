from socket import *
from pathlib import Path
import argparse

class PTAServer:
    """Implementa o servidor PTA para comunicação TCP e transferência de arquivos."""
    PORT = 11550
    FAMILY = AF_INET
    PROTOCOL = SOCK_STREAM
    BUFFER_SIZE = 2048

    # Inicialização
    def __init__(self, host="0.0.0.0", usersFile="users.txt", directory="files"):
        """Inicializa o servidor, carregando usuários, configurando diretório e socket.

        Args:
            host (str): Endereço IP no qual o servidor ficará disponível.
            usersFile (str): Caminho do arquivo contendo os usuários autorizados.
            directory (str): Diretório utilizado para armazenar os arquivos.
        """
        self.configureUsers(usersFile)
        self.configureDirectory(directory)
        self.configureSocket(host)

    def configureUsers(self, usersFile):
        """Carrega e valida os usuários autorizados a utilizar o servidor.

        Args:
            usersFile (str): Caminho do arquivo de usuários.

        Raises:
            RuntimeError: Caso ocorra algum erro na leitura ou validação do arquivo.
        """
        try:
            with open(usersFile, encoding="ascii") as archive:

                self.users = {
                    line.strip()
                    for line in archive
                    if line.strip()
                }

            if any(
                not user.isascii() or not user.isprintable()
                for user in self.users
            ):
                raise ValueError("Arquivo contém usuários inválidos.")

            print(f"[+] {len(self.users)} usuários carregados.")

        except (OSError, UnicodeError, ValueError) as error:
            raise RuntimeError(
                f"Erro ao carregar usuários: {error}"
            ) from error

    def configureDirectory(self, directory):
        """Configura e valida o diretório de armazenamento dos arquivos.

        Args:
            directory (str): Caminho do diretório de arquivos.

        Raises:
            RuntimeError: Caso o caminho seja inválido ou não possa ser criado.
        """
        try:
            self.directory = Path(directory)

            if self.directory.exists() and not self.directory.is_dir():
                raise ValueError("O caminho informado não é um diretório.")

            self.directory.mkdir(parents=True, exist_ok=True)

            print(f"[+] Diretório configurado: {self.directory.resolve()}")

        except (OSError, ValueError) as error:
            raise RuntimeError(f"Erro ao configurar diretório: {error}") from error

    def configureSocket(self, host):
        """Cria, configura e inicia o socket TCP do servidor.

        Args:
            host (str): Endereço IP utilizado para vincular o socket.

        Raises:
            RuntimeError: Caso ocorra um erro na configuração do socket.
        """
        try:
            self.server = socket(self.FAMILY,self.PROTOCOL)
            self.server.bind((host, self.PORT))
            self.server.listen(5)
            self.server.settimeout(1.0)

            print(f"[+] Servidor iniciado em {host}:{self.PORT}")

        except OSError as e:
            raise RuntimeError(f"Erro ao configurar socket: {e}") from e

    # Comandos    
    def listFiles(self):
        """Retorna os nomes dos arquivos presentes no diretório configurado.

        Returns:
            list[str]: Lista contendo os nomes dos arquivos.
        """
        files = [file.name for file in self.directory.iterdir() if file.is_file()]
        return files

    def getFile(self, filename):
        """Localiza, valida e lê um arquivo do diretório autorizado.

        Args:
            filename (str): Nome do arquivo solicitado pelo cliente.

        Returns:
            bytes | None: Conteúdo binário do arquivo ou None caso não seja válido
            ou não possa ser acessado.
        """
        try:
            filename = Path(filename)

            # Validar nome
            if (not filename.name or filename.name in (".", "..") or filename.name != str(filename)):
                return None

            # Resolver caminho completo
            file_path = self.directory / filename

            if file_path.is_symlink():
                return None

            file_path = file_path.resolve()

            # Garantir que permanece dentro do diretório autorizado
            if not file_path.is_relative_to(self.directory.resolve()):
                return None

            # Verificar existência e tipo
            if not file_path.is_file():
                return None

            # Ler arquivo
            with open(file_path, "rb") as file:
                return file.read()

        except (OSError, ValueError, RuntimeError) as e:
            print(f"Erro ao acessar arquivo: {e}")
            return None
    
    def close(self):
        """Encerra o socket principal e finaliza o servidor."""
        print("\n[!] Encerrando servidor...")
        self.server.shutdown(SHUT_RDWR)
        self.server.close()

        print("[+] Servidor encerrado.")

    # Loop principal do servidor
    def run(self):
        """Executa o loop principal de aceitação e atendimento das conexões TCP.

        Trata erros individuais de conexão e encerra o servidor mediante
        interrupção do teclado.
        """
        print(
            "[+] Servidor pronto para receber conexões. "
            "Pressione Ctrl+C para encerrar."
        )

        try:
            while True:
                try:
                    try:
                        connection, addr = self.server.accept()
                    except timeout:
                        continue

                    print(f"[+] Conexão estabelecida com {addr}")

                    try:
                        self.handleClient(connection)

                    except (ConnectionError, OSError) as e:
                        print(f"[!] Erro de conexão com {addr}: {e}")

                    except Exception as e:
                        print(f"[!] Erro ao tratar cliente {addr}: {e}")

                    finally:
                        connection.close()
                        print(f"[-] Conexão encerrada com {addr}")

                except OSError as e:
                    print(f"[!] Erro no servidor: {e}")
                    break

        except KeyboardInterrupt:
            print("\n[!] CTRL+C detectado.")

        finally:
            self.close()

    def recvMessage(self, client, ready):
        """Recebe e interpreta uma mensagem enviada pelo cliente.

        Args:
            client (socket): Socket da conexão com o cliente.
            ready (bool): Indica se a autenticação inicial já foi realizada.

        Returns:
            tuple: Número de sequência, comando identificado e argumentos.
        """
        seq = None
        command = None
        args = None
        message = b""
        message_ascii = ""

        client.settimeout(2.0)

        try:
            while True:
                data = client.recv(self.BUFFER_SIZE)

                if not data:
                    return (seq, command, args)

                message += data
                try:
                    message_ascii = message.decode("ascii")
                except UnicodeDecodeError:
                    return (seq, command, args)

                # Tenta coletar o seq
                if seq is None:
                    seq_part, _, remainder = message_ascii.partition(" ")
                    if len(remainder) < 4:
                        continue

                    if not seq_part.isdigit():
                        return (seq, command, args)
                    
                    seq = int(seq_part)
                    message_ascii = remainder
                    message = message_ascii.encode()

                # Tenta coletar o comando (4 primeiros bytes)
                if command is None:
                    command_part = message_ascii[:4]

                    if command_part == "CUMP":
                        if ready:
                            return (seq, command_part, None)

                        if len(message_ascii) < 6:
                            continue

                        if message_ascii[4] != " ":
                            return (seq, None, None)

                        arg = message_ascii[5:]

                        if arg in self.users:
                            return (seq, "CUMP", arg)

                        return (seq, "CUMP", None)
                    elif command_part not in ("CUMP", "LIST", "PEGA", "TERM"):
                        return (seq, command, args)
                    
                    elif command_part in ("CUMP", "PEGA"):
                        if len(message_ascii) < 6:
                            continue
                        elif message_ascii[4:5] != " ":
                            return (seq, command, args)
                        else:
                            arg = message_ascii[5:]
                                
                            if (command_part == "CUMP" and arg in self.users) or (command_part == "PEGA" and arg in self.listFiles()):
                                command = command_part
                                args = arg
                                continue
                            else:
                                valid_args = self.users if command_part == "CUMP" else set(self.listFiles())

                                if any(name.startswith(arg) for name in valid_args):
                                    continue
                                
                                else:
                                    return (seq, command, args)

                    else:
                        if message_ascii == command_part:
                            return (seq, command_part, None)
                        else:
                            return (seq, None, None)

                return (seq, command, args)
            
        except timeout:
            return (seq, command, args)

    def handleClient(self, client):
        """Gerencia a comunicação com um cliente conectado.

        Realiza a autenticação inicial, valida os números de sequência e
        processa os comandos LIST, PEGA e TERM.

        Args:
            client (socket): Socket da conexão estabelecida com o cliente.
        """
        ready = False
        expected_seq = None

        while True:

            seq, command, args = self.recvMessage(client, ready)
            if seq is None:
                client.sendall("err NOK")
                if command == "CUMP":
                    return

            if command == "CUMP":
                if args is not None:
                    client.sendall(f"{seq} OK".encode())
                    expected_seq = seq + 1
                    ready = True
                    continue
                else:
                    client.sendall(f"{seq} NOK".encode())
                    return
            
            if seq != expected_seq:
                client.sendall(f"{seq} NOK".encode())
                continue

            expected_seq += 1

            if command == "LIST":
                try:
                    args = self.listFiles()
                except OSError:
                    client.sendall(f"{seq} NOK".encode())
                    continue

                if args is None:
                    client.sendall(f"{seq} NOK".encode())
                    continue

                len_args = len(args)
                args_str = ",".join(name for name in args)
                client.sendall(f"{seq} ARQS {len_args} {args_str}".encode())

            elif command == "PEGA":
                if args is not None and (self.directory / args).is_symlink():
                    client.sendall(f"{seq} NOK".encode())
                    continue

                if args is None:
                    client.sendall(f"{seq} NOK".encode())
                    continue

                file = self.getFile(args)

                if file is None:
                    client.sendall(f"{seq} NOK".encode())
                    continue

                len_args = len(file)
                client.sendall(f"{seq} ARQ {len_args} ".encode() + file)

            elif command == "TERM":
                client.sendall(f"{seq} OK".encode())
                return

            else:
                client.sendall(f"{seq} NOK".encode())

if __name__ == "__main__":
    """Configura os argumentos de execução e inicia o servidor PTA."""
    parser = argparse.ArgumentParser(
        description="PTA Server"
    )

    parser.add_argument("-ip", "--host", default="0.0.0.0",
                        help="IP do servidor (padrão: 0.0.0.0)")

    parser.add_argument("-uf", "--usersFile", default="users.txt",
                        help="Arquivo de usuários (padrão: users.txt)")

    parser.add_argument("-d", "--directory", default="files",
                        help="Diretório de arquivos (padrão: files)")

    args = parser.parse_args()

    server = PTAServer(
        host=args.host,
        usersFile=args.usersFile,
        directory=args.directory
    )

    server.run()