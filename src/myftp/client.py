# Author: Minh Tran and Angelo Reoligio
# Date: November 30, 2023
# Description: FTP client (both UDP and TCP implemented)


from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM
from typing import Pattern, Tuple, Optional
from argparse import ArgumentParser
import traceback
import os
import re


# patterns for command matchings
# compiled for extra performance
get_command_pattern: Pattern = re.compile(r"^get\s+[^\s]+$")
put_command_pattern: Pattern = re.compile(r"^put\s+[^\s]+$")
summary_command_pattern: Pattern = re.compile(r"^summary\s+[^\s]+$")
change_command_pattern: Pattern = re.compile(r"^change\s+[^\s]+\s+[^\s]+$")

# opcodes
put_request_opcode: int = 0b000
get_request_opcode: int = 0b001
change_request_opcode: int = 0b010
summary_request_opcode: int = 0b011
help_request_opcode: int = 0b100
unknown_request_opcode: int = 0b101

# Res-code dict
rescode_dict: dict[int, str] = {
    0b011: "File Not Found Error",
    0b100: "Unknown Request",
    0b101: "Change/Put Unsuccessful Error",
    0b000: "Put/Change Request Successful",
    0b001: "Get Request Successful",
    0b010: "Summary Request Successful",
    0b110: "Help",
}


# custome type to represent the hostname(server name) and the server port
Address = Tuple[str, int]


class Client:
    def __init__(
        self,
        server_name: str,
        server_port: int,
        directory_path: str,
        debug: bool,
        protocol: str,
    ):
        self.server_name: str = server_name
        self.server_port: int = server_port
        self.protocol: str = protocol
        self.directory_path = directory_path
        self.debug = debug

    def run(self):
        self.client_socket = socket(
            AF_INET, (SOCK_DGRAM if self.protocol == "UDP" else SOCK_STREAM)
        )
        self.client_socket.settimeout(10)

        # only if using TCP
        self.client_socket.connect(
            (self.server_name, self.server_port)
        ) if self.protocol == "TCP" else None

        try:
            while True:
                # get command from user
                command = input(f"myftp> - {self.protocol} - : ").strip().lower()

                # handling the "bye" command
                if command == "bye":
                    self.client_socket.close()
                    print(f"myftp> - {self.protocol} - Session is terminated")
                    break

                # help
                elif command == "help":
                    first_byte: int = help_request_opcode << 5
                    command_name = "help"

                    print(
                        f"myftp> - {self.protocol} - Asking for help from the server"
                    ) if self.debug else None

                # get command handling
                elif get_command_pattern.match(command):
                    command_name, filename = command.split(" ", 1)

                    first_byte = (get_request_opcode << 5) + len(filename)

                    second_byte_to_n_byte = filename.encode("ascii")

                    print(
                        f"myftp> - {self.protocol} - Getting file {filename} from the server"
                    ) if self.debug else None

                # put command handling
                elif put_command_pattern.match(command):
                    command_name, filename = command.split(" ", 1)

                    first_byte, second_byte_to_n_byte, data = self.put_payload_handling(
                        filename
                    )

                    print(
                        f"myftp> - {self.protocol} - Putting file {filename} into the server"
                    ) if self.debug else None

                # summary command handling
                elif summary_command_pattern.match(command):
                    command_name, filename = command.split(" ", 1)
                    print(
                        f"myftp> - {self.protocol} - Summary file {filename} from the server"
                    ) if self.debug else None

                    first_byte = (summary_request_opcode << 5) + len(filename)

                    second_byte_to_n_byte = filename.encode("ascii")

                # change command handling
                elif change_command_pattern.match(command):
                    command_name, old_filename, new_filename = command.split()

                    print(
                        f"myftp> - {self.protocol} - Changing file named {old_filename} into {new_filename} on the server"
                    ) if self.debug else None

                    first_byte = (change_request_opcode << 5) + len(old_filename)

                    second_byte_to_n_byte = (
                        old_filename.encode("ascii")
                        + len(new_filename).to_bytes(1, "big")
                        + new_filename.encode("ascii")
                    )

                # unknown request, assigned opcode is 0b101
                else:
                    command_name = None
                    first_byte: int = unknown_request_opcode << 5

                # get change put cases
                if (
                    command_name == "get"
                    or command_name == "summary"
                    or command_name == "change"
                ):
                    payload = first_byte.to_bytes(1, "big") + second_byte_to_n_byte  # type: ignore

                elif command_name == "put":
                    payload = (
                        first_byte.to_bytes(1, "big") + second_byte_to_n_byte + data  # type: ignore
                        if second_byte_to_n_byte is not None and data is not None  # type: ignore
                        else first_byte.to_bytes(1, "big")  # type: ignore
                    )

                # help case and unknown request
                else:
                    payload: bytes = first_byte.to_bytes(1, "big")  # type: ignore

                print(
                    f"myftp> - {self.protocol} - sent payload {bin(int.from_bytes(payload, byteorder='big'))[2:]} to the server"  # type: ignore
                ) if self.debug else None

                if self.protocol == "UDP":
                    self.client_socket.sendto(payload, (self.server_name, self.server_port))  # type: ignore
                else:
                    self.client_socket.sendall(payload)  # type: ignore

                response_payload = self.client_socket.recv(2048)

                self.parse_response_payload(response_payload)

        except ConnectionRefusedError:
            print(
                f"myftp> - {self.protocol} - ConnectionRefusedError happened. Please restart the client program, make sure the server is running and/or put a different server name and server port."
            )

        except TimeoutError:
            # Server did not respond within the specified timeout
            print(
                f"myftp> - {self.protocol} - Server at {self.server_name} did not respond within 5 seconds. Check the address or server status."
            )

        except Exception as error:
            traceback_info = traceback.format_exc()

            print(f"myftp> - {self.protocol} - {error} happened.")

            print(traceback_info)

        finally:
            self.client_socket.close()

    def parse_response_payload(self, response_payload: bytes):
        first_byte = bytes([response_payload[0]])
        first_byte_binary = int.from_bytes(first_byte, "big")
        rescode = first_byte_binary >> 5
        filename_length = first_byte_binary & 0b00011111
        response_data = response_payload[1:]
        response_data_length = len(response_data)

        print(
            f"myftp> - {self.protocol} - First_byte from server response: {first_byte}. Rescode: {rescode}. File name length: {filename_length}. Data length: {response_data_length}"
        ) if self.debug else None

        try:
            print(
                f"myftp> - {self.protocol} - Res-code meaning: {rescode_dict[rescode]}"
            ) if self.debug else None
        except KeyError:
            print(f"myftp> - {self.protocol} - Res-code does not have meaning")

        # error rescodes
        if rescode in [0b011, 0b100, 0b101]:
            print(f"myftp> - {self.protocol} - {rescode_dict[rescode]}")

        # successful rescodes
        else:
            # help rescode and successful change or put rescode
            if rescode == 0b110:
                print(f"myftp> - {self.protocol} - {response_data.decode('ascii')}")
            elif rescode == 0b000:
                print(f"myftp> - {self.protocol} - {rescode_dict[rescode]}")
            # get rescode
            elif rescode == 0b001:
                self.handle_get_response_from_server(filename_length, response_data)
            elif rescode == 0b010:
                self.handle_summary_response_from_server(filename_length, response_data)

    def put_payload_handling(
        self, filename: str
    ) -> Tuple[int, Optional[bytes], Optional[bytes]]:
        """
        Assemble the pay load to put the file onto server

        Return first_byte, second_byte_to_n_byte and data if successful
        Or (None, None, None) if file not found
        """
        try:
            with open(os.path.join(self.directory_path, filename), "rb") as file:
                content = file.read()
                content_length = len(content)

                first_byte = (put_request_opcode << 5) + len(filename)

                second_byte_to_n_byte = filename.encode(
                    "ascii"
                ) + content_length.to_bytes(4, "big")

                data = content

                return (first_byte, second_byte_to_n_byte, data)

        except FileNotFoundError:
            return ((put_request_opcode << 5), None, None)

    def handle_get_response_from_server(
        self, filename_length: int, response_data: bytes
    ):
        """
        Response_data is
        File name (filename_length bytes) +
        File size (4 bytes) +
        File content (rest of the bytes)
        """
        try:
            filename = response_data[:filename_length].decode("ascii")
            file_size = int.from_bytes(
                response_data[filename_length : filename_length + 4], "big"
            )
            file_content = response_data[
                filename_length + 4 : filename_length + 4 + file_size
            ]

            print(
                f"myftp> - {self.protocol} - Filename: {filename}, File_size: {file_size} bytes"
            )

            with open(os.path.join(self.directory_path, filename), "wb") as file:
                file.write(file_content)

            print(
                f"myftp> - {self.protocol} - File {filename} has been downloaded successfully"
            )

        except Exception:
            raise

    def handle_summary_response_from_server(
        self, filename_length: int, response_data: bytes
    ):
        """
        Response_data is
        File name (filename_length bytes) +
        File size (4 bytes) +
        File content (rest of the bytes)
        """
        try:
            filename = response_data[:filename_length].decode("ascii")
            file_size = int.from_bytes(
                response_data[filename_length : filename_length + 4], "big"
            )
            file_content = response_data[
                filename_length + 4 : filename_length + 4 + file_size
            ]

            print(
                f"myftp> - {self.protocol} - Filename: {filename}, File_size: {file_size} bytes"
            )

            with open(os.path.join(self.directory_path, filename), "wb") as file:
                file.write(file_content)

            print(
                f"myftp> - {self.protocol} - File {filename} has been downloaded successfully"
            )

        except Exception:
            raise


def get_address_input() -> Address:
    while True:
        try:
            # Get input as a space-separated string
            input_string = input("myftp>Provide IP address and Port number\n")

            # Split the input into parts
            input_parts = input_string.split()

            # Ensure there are exactly two parts
            if len(input_parts) != 2:
                raise ValueError

            # Extract the values and create the tuple
            string_part, int_part = input_parts
            address = (string_part, int(int_part))

            # Valid tuple, return it
            return address

        except ValueError:
            print(
                "Error: Invalid input. Please enter a servername/hostname/ip address as a string and the port number as an integer separated by a space."
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

    user_supplied_address = get_address_input()

    # UDP client selected here
    if protocol_selection == "2":
        udp_client = Client(
            user_supplied_address[0],
            user_supplied_address[1],
            args.directory,
            args.debug,
            "UDP",
        )

        udp_client.run()
    else:
        tcp_client = Client(
            user_supplied_address[0],
            user_supplied_address[1],
            args.directory,
            args.debug,
            "TCP",
        )

        tcp_client.run()


if __name__ == "__main__":
    init()
