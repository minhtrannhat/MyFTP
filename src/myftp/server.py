from socket import socket, AF_INET, SOCK_DGRAM
from argparse import ArgumentParser


class UDPServer:
    def __init__(self, server_name: str, server_port: int, debug: bool) -> None:
        self.server_name = server_name
        self.server_port = server_port
        self.mode: str = "UDP"
        self.debug = debug

    def run(self):
        self.server_socket = socket(AF_INET, SOCK_DGRAM)
        self.server_socket.bind((self.server_name, self.server_port))

        print(
            f"myftp> - {self.mode} - server is ready to receive at {self.server_name}:{self.server_port}"
        ) if self.debug else None

        shut_down = False

        try:
            while not shut_down:
                message, clientAddress = self.server_socket.recvfrom(2048)
                message_in_utf8 = message.decode()

                print(
                    f"myftp> - {self.mode} - received message from client at {clientAddress}: {message_in_utf8}"
                ) if self.debug else None

                if message_in_utf8 == "ping":
                    response_message = "pong"
                else:
                    response_message = message_in_utf8.upper()

                print(
                    f"myftp> - {self.mode} - sent message to client at {clientAddress}: {response_message}"
                ) if self.debug else None

                self.server_socket.sendto(response_message.encode(), clientAddress)

        except KeyboardInterrupt:
            shut_down = True
            self.server_socket.close()
            print(f"myftp> - {self.mode} - Server shutting down\n")

        finally:
            print(f"myftp> - {self.mode} - Closed the server socket\n")


def init():
    parser = ArgumentParser(description="A FTP server written in Python")

    parser.add_argument(
        "--port_number",
        default=12000,
        required=False,
        type=int,
        help="Port number for the server. Default = 12000",
    )

    parser.add_argument(
        "--debug",
        type=int,
        choices=[0, 1],
        default=0,
        help="Enable or disable the flag (0 or 1)",
    )

    args = parser.parse_args()

    while (
        protocol_selection := input("myftp>Press 1 for TCP, Press 2 for UDP\n")
    ) not in {"1", "2"}:
        print("myftp>Invalid choice. Press 1 for TCP, Press 2 for UDP")

    # UDP client selected here
    if protocol_selection == "2":
        udp_server = UDPServer("127.0.0.1", args.port_number, args.debug)

        udp_server.run()

    else:
        # tcp client here
        pass


if __name__ == "__main__":
    init()
