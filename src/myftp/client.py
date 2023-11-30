# Author: Minh Tran and Angelo Reoligio
# Date: November 30, 2023
# Description: FTP client (both UDP and TCP implemented)


from socket import socket, AF_INET, SOCK_DGRAM
from typing import Pattern, Tuple
from argparse import ArgumentParser
import os
import pickle
import re

# patterns for command matchings
# compiled for extra performance
get_command_pattern: Pattern = re.compile(r"^get\s+[^\s]+$")
put_command_pattern: Pattern = re.compile(r"^put\s+[^\s]+$")
summary_command_pattern: Pattern = re.compile(r"^summary\s+[^\s]+$")
change_command_pattern: Pattern = re.compile(r"^change\s+[^\s]+\s+[^\s]+$")

# custome type to represent the hostname(server name) and the server port
Address = Tuple[str, int]


class UDPClient:
    def __init__(self, server_name: str, server_port: int, debug: bool):
        self.server_name: str = server_name
        self.server_port: int = server_port
        self.mode: str = "UDP"
        self.pong_received: bool = False
        self.debug = debug

    def run(self):

        # server cannot be reached, stop the client immediately
        if not self.pong_received:
            return

        while True:
            try:
                client_socket = socket(AF_INET, SOCK_DGRAM)
                client_socket.connect((self.server_name, self.server_port))

                # get command from user
                command = input(f"myftp> - {self.mode} - : ").strip().lower()

                # handling the "bye" command
                if command == "bye":
                    client_socket.close()
                    print(f"myftp> - {self.mode} - Session is terminated")
                    break

                # list files available on the server
                elif command == "list":
                    self.get_files_list_from_server(client_socket)
                    continue

                # help
                elif command == "help":
                    continue

                # get command handling
                elif get_command_pattern.match(command):
                    _, filename = command.split(" ", 1)
                    print(
                        f"myftp> - {self.mode} - : getting file {filename} from the server"
                    ) if self.debug else None

                # put command handling
                elif put_command_pattern.match(command):
                    _, filename = command.split(" ", 1)
                    print(
                        f"myftp> - {self.mode} - : putting file {filename} into the server"
                    ) if self.debug else None

                # summary command handling
                elif summary_command_pattern.match(command):
                    _, filename = command.split(" ", 1)
                    print(
                        f"myftp> - {self.mode} - : summary file {filename} from the server"
                    ) if self.debug else None

                # summary command handling
                elif change_command_pattern.match(command):
                    _, old_filename, new_filename = command.split()
                    print(
                        f"myftp> - {self.mode} - : changing file named {old_filename} into {new_filename} on the server"
                    ) if self.debug else None

                else:
                    print(
                        f"myftp> - {self.mode} - : Invalid command. Supported commands are put, get, summary, change, list and help. Type help for detailed usage."
                    )
                    continue

                client_socket.send(command.encode())
                modified_message = client_socket.recv(2048)
                print(modified_message.decode())

            except ConnectionRefusedError:
                print(
                    f"myftp> - {self.mode} - ConnectionRefusedError happened. Please restart the client program, make sure the server is running and/or put a different server name and server port."
                )
            except Exception as error:
                print(
                    f"myftp> - {self.mode} - {error} happened."
                )
            finally:
                client_socket.close() # type: ignore

    # ping pong UDP
    def check_udp_server(self):
        # Create a UDP socket
        client_socket = socket(AF_INET, SOCK_DGRAM)
        # will time out after 5 seconds
        client_socket.settimeout(5)

        try:
            # Send a test message to the server
            message = b"ping"
            client_socket.sendto(message, (self.server_name, self.server_port))

            # Receive the response
            data, _ = client_socket.recvfrom(1024)

            # If the server responds, consider the address valid
            print(
                f"myftp> - {self.mode} - Server at {self.server_name}:{self.server_port} is valid. Response received: {data.decode('utf-8')}"
            )

            # code reached here meaning no problem with the connection
            self.pong_received = True

        except TimeoutError:
            # Server did not respond within the specified timeout
            print(
                f"myftp> - {self.mode} - Server at {self.server_name} did not respond within 5 seconds. Check the address or server status."
            )

        finally:
            # Close the socket
            client_socket.close()

    # get list of files currently on the server
    def get_files_list_from_server(self, client_socket: socket) -> list[str]:
        client_socket.send("list".encode())
        encoded_message, server_address = client_socket.recvfrom(4096)
        file_list = pickle.loads(encoded_message)
        print(f"Received file list from {server_address}: {file_list}")
        client_socket.close()

        return file_list


def get_address_input() -> Address:
    while True:
        try:
            # Get input as a space-separated string
            input_string = input("myftp>Provide IP address and Port number\n")

            # Split the input into parts
            input_parts = input_string.split()

            # Ensure there are exactly two parts
            if len(input_parts) != 2:
                raise ValueError(
                    "myftp>Invalid input. Please enter a servername/hostname/ip address as a string and the port number as an integer separated by a space."
                )

            # Extract the values and create the tuple
            string_part, int_part = input_parts
            address = (string_part, int(int_part))

            # Valid tuple, return it
            return address

        except ValueError as e:
            print(
                f"Error: {e}. Invalid input. Please enter a servername/hostname/ip address as a string and the port number as an integer separated by a space."
            )


def check_directory(path):
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
    arg_parser = ArgumentParser(description="A FTP client written in Python")

    arg_parser.add_argument(
        "--debug",
        type=int,
        choices=[0, 1],
        default=0,
        required=False,
        help="Enable or disable the flag (0 or 1)",
    )

    arg_parser.add_argument(
        "--directory", required=True, type=str, help="Path to the client directory"
    )

    args = arg_parser.parse_args()

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
        user_supplied_address = get_address_input()

        udp_client = UDPClient(
            user_supplied_address[0], user_supplied_address[1], args.debug
        )

        udp_client.check_udp_server()

        udp_client.run()
    else:
        # tcp client here
        pass


if __name__ == "__main__":
    init()
