# Author: Minh Tran and Angelo Reoligio
# Date: November 30, 2023
# Description: FTP server (both UDP and TCP implemented)


from socket import socket, AF_INET, SOCK_DGRAM
from argparse import ArgumentParser
import os
import pickle

# Res-code
correct_put_and_change_request_rescode: str = "000"
correct_get_request_rescode: str = "001"
correct_summary_request_rescode: str = "010"
file_not_error_rescode: str = "011"
unknown_request_rescode: str = "100"
unsuccessful_change_rescode: str = "101"
help_rescode: str = "110"


class UDPServer:
    def __init__(
        self, server_name: str, server_port: int, directory_path: str, debug: bool
    ) -> None:
        self.server_name = server_name
        self.server_port = server_port
        self.mode: str = "UDP"
        self.directory_path = directory_path
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

                # check for connectivity
                if message_in_utf8 == "ping":
                    response_message = "pong"

                # list files available on server
                elif message_in_utf8 == "list":
                    encoded_message = pickle.dumps(
                        get_files_in_directory(self.directory_path)
                    )
                    self.server_socket.sendto(encoded_message, clientAddress)
                    continue

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


def get_files_in_directory(directory_path: str) -> list[str]:
    file_list = []
    for _, _, files in os.walk(directory_path):
        for file in files:
            file_list.append(file)
    return file_list


def check_directory(path: str) -> bool:
    if os.path.exists(path):
        if os.path.isdir(path):
            if os.access(path, os.R_OK) and os.access(path, os.W_OK):
                return True
            else:
                print(f"Error: The directory '{path}' is not readable or writable.")
        else:
            print(f"Error: '{path}' is not a directory.")
    else:
        print(f"Error: The directory '{path}' does not exist.")
    return False


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
        "--directory", required=True, type=str, help="Path to the server directory"
    )

    parser.add_argument(
        "--ip_addr",
        default="0.0.0.0",
        required=False,
        type=str,
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

    if not check_directory(args.directory):
        print(
            f"The directory '{args.directory}' does not exists or is not readable/writable."
        )
        return

    # UDP client selected here
    if protocol_selection == "2":
        udp_server = UDPServer(
            args.ip_addr, args.port_number, args.directory, args.debug
        )

        udp_server.run()

    else:
        # tcp client here
        pass


if __name__ == "__main__":
    init()
