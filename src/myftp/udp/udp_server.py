from socket import socket, AF_INET, SOCK_DGRAM
from argparse import ArgumentParser


class UDPServer:
    def __init__(self, server_name: str, server_port: int, debug: bool) -> None:
        self.server_name = server_name
        self.server_port = server_port
        self.debug = debug

    def run(self):
        self.server_socket = socket(AF_INET, SOCK_DGRAM)
        self.server_socket.bind((self.server_name, self.server_port))

        print(
            f"server is ready to receive at {self.server_name}:{self.server_port}"
        ) if self.debug else None

        shut_down = False

        try:
            while not shut_down:
                message, clientAddress = self.server_socket.recvfrom(2048)
                message_in_utf8 = message.decode()

                print(
                    f"received message from client at {clientAddress}: {message_in_utf8}"
                ) if self.debug else None

                modified_message = message_in_utf8.upper()
                self.server_socket.sendto(modified_message.encode(), clientAddress)

        except KeyboardInterrupt:
            shut_down = True
            self.server_socket.close()
            print("Server shutting down\n")

        finally:
            print("Closed the server socket\n")


def init():
    parser = ArgumentParser(description="A FTP server written in Python. UDP version")

    parser.add_argument(
        "port_number", type=int, help="Port number for the server. Default = 12000"
    )

    parser.add_argument(
        "--debug",
        type=int,
        choices=[0, 1],
        default=0,
        help="Enable or disable the flag (0 or 1)",
    )

    args = parser.parse_args()

    udp_server = UDPServer("127.0.0.1", args.port_number, args.debug)

    udp_server.run()


if __name__ == "__main__":
    init()
