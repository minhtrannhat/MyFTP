from socket import socket, AF_INET, SOCK_DGRAM
from argparse import ArgumentParser


class UDPClient:
    def __init__(self, server_name: str, server_port: int, debug: bool):
        self.server_name = server_name
        self.server_port = server_port
        self.debug = debug

        print(f"New UDP connection created to server at {server_name}:{server_port}")

    def run(self):
        client_socket = socket(AF_INET, SOCK_DGRAM)

        try:
            client_socket.connect((self.server_name, self.server_port))
        except Exception:
            print(
                f"Error with the server IP address {self.server_name} or with the server port number {self.server_port}"
            )

        message = input("input lowercase sentence: ")

        client_socket.send(message.encode())

        modified_message = client_socket.recv(2048)

        print(modified_message.decode())

        client_socket.close()


def init():
    parser = ArgumentParser(description="A FTP server written in Python. UDP version")

    parser.add_argument(
        "server_name",
        type=str,
        default="127.0.0.1",
        help="IP address or hostname for the server. Default = localhost",
    )

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

    udp_server = UDPClient(args.server_name, args.port_number, args.debug)

    udp_server.run()


if __name__ == "__main__":
    init()
