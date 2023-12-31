# Author: Minh Tran and Angelo Reoligio
# Date: November 30, 2023
# Description: FTP server (both UDP and TCP implemented)


from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM
from argparse import ArgumentParser
from typing import Optional, Tuple
import traceback
import os

# Res-codes
rescode_success_dict: dict[str, int] = {
    "correct_put_and_change_request_rescode": 0b000,
    "correct_get_request_rescode": 0b001,
    "correct_summary_request_rescode": 0b010,
    "help_rescode": 0b110,
}

rescode_fail_dict: dict[str, int] = {
    "file_not_error_rescode": 0b011,
    "unknown_request_rescode": 0b100,
    "unsuccessful_change_rescode": 0b101,
}

# opcodes
op_codes_dict: dict[int, str] = {
    0b000: "put",
    0b001: "get",
    0b010: "change",
    0b011: "summary",
    0b100: "help",
    0b101: "unknown",
}


class Server:
    def __init__(
        self,
        server_name: str,
        server_port: int,
        directory_path: str,
        debug: bool,
        protocol: str,
    ) -> None:
        self.server_name = server_name
        self.server_port = server_port
        self.protocol: str = protocol
        self.directory_path = directory_path
        self.debug = debug

    def run(self):
        server_socket = socket(
            AF_INET, (SOCK_DGRAM if self.protocol == "UDP" else SOCK_STREAM)
        )

        server_socket.bind((self.server_name, self.server_port))

        # only needed for TCP
        server_socket.listen(5) if self.protocol == "TCP" else None

        print(
            f"myftp> - {self.protocol} - Server is ready to receive at {self.server_name}:{self.server_port}"
        ) if self.debug else None

        shut_down = False

        try:
            if self.protocol == "TCP":
                client_socket, clientAddress = server_socket.accept()

                print(
                    f"myftp> - {self.protocol} - Connected to TCP client at {clientAddress}"
                ) if self.debug else None

            while not shut_down:
                print(
                    f"myftp> - {self.protocol} ------------------------------------------------------------------"
                ) if self.debug else None

                if self.protocol == "UDP":
                    req_payload, clientAddress = server_socket.recvfrom(2048)
                else:
                    req_payload = client_socket.recv(2048)  # type: ignore

                    # TCP client disconnected
                    if not req_payload:
                        client_socket.close()  # type: ignore
                        return

                first_byte = bytes([req_payload[0]])

                request_type, filename_length_in_bytes = self.decode_first_byte(
                    first_byte
                )

                print(
                    f"myftp> - {self.protocol} - Received message from client at {clientAddress}: {req_payload}. Payload length is {len(req_payload)}"  # type: ignore
                ) if self.debug else None

                # help request handling
                if request_type == "help":
                    print(
                        f"myftp> - {self.protocol} - Client message parsed. Received help request"
                    ) if self.debug else None

                    rescode = rescode_success_dict["help_rescode"]
                    response_data = "get,put,summary,change,help,bye".encode("ascii")
                    filename = None
                    filename_length_in_bytes = None

                elif request_type == "get":
                    pre_payload = self.process_get_req(req_payload[1:])

                    if (
                        pre_payload[0] is not None
                        and pre_payload[1] is not None
                        and pre_payload[2] is not None
                    ):
                        rescode = rescode_success_dict["correct_get_request_rescode"]
                        filename = pre_payload[0]
                        filename_length_in_bytes = pre_payload[2]
                        response_data = pre_payload[1]

                    else:
                        rescode = rescode_fail_dict["file_not_error_rescode"]
                        filename_length_in_bytes = None
                        filename = None
                        response_data = None

                elif request_type == "put":
                    # put request failed since there wasnt a file sent from client
                    if filename_length_in_bytes == 0:
                        rescode = rescode_fail_dict["unsuccessful_change_rescode"]
                        filename_length_in_bytes = None
                        filename = None
                        response_data = None

                    # put request success
                    else:
                        rescode = self.process_put_req(
                            filename_length_in_bytes, req_payload[1:]
                        )
                        filename_length_in_bytes = None
                        filename = None
                        response_data = None

                elif request_type == "summary":
                    # empty filename error
                    if filename_length_in_bytes <= 0:
                        rescode = rescode_fail_dict["file_not_error_rescode"]
                    else:
                        (
                            rescode,
                            filename,  # "summary.txt"
                            filename_length_in_bytes,  # of the summary file
                            response_data,  # summary.txt file content
                        ) = self.process_summary_req(
                            filename_length_in_bytes, req_payload[1:]
                        )

                elif request_type == "change":
                    rescode = self.process_change_req(
                        filename_length_in_bytes, req_payload[1:]
                    )
                    filename_length_in_bytes = None
                    filename = None
                    response_data = None

                elif request_type == "unknown":
                    rescode = rescode_fail_dict["unknown_request_rescode"]
                    filename_length_in_bytes = None
                    filename = None
                    response_data = None

                res_payload: bytes = self.build_res_payload(
                    rescode=rescode,  # type: ignore
                    filename_length=filename_length_in_bytes,
                    filename=filename,  # type: ignore
                    response_data=response_data,  # type:ignore
                )

                if self.protocol == "UDP":
                    server_socket.sendto(res_payload, clientAddress)  # type: ignore
                else:
                    client_socket.sendall(res_payload)  # type: ignore

                print(
                    f"myftp> - {self.protocol} - Sent message to client at {clientAddress}: {res_payload}. Payload length is {len(res_payload)}"  # type: ignore
                ) if self.debug else None

        except KeyboardInterrupt:
            shut_down = True
            if self.protocol == "UDP":
                server_socket.close()
            else:
                client_socket.close()  # type: ignore

            print(f"myftp> - {self.protocol} - Server shutting down")

        finally:
            print(f"myftp> - {self.protocol} - Closed the server socket")

    def decode_first_byte(self, first_byte: bytes) -> Tuple[str, int]:
        """
        Retrieve the request_type from first byte
        """
        if len(first_byte) != 1:
            raise ValueError("Input is not 1 byte")

        first_byte_to_binary = int.from_bytes(first_byte, "big")

        try:
            request_type = op_codes_dict[first_byte_to_binary >> 5]

            filename_length_in_bytes = first_byte_to_binary & 0b00011111

            print(
                f"myftp> - {self.protocol} - First byte parsed. Request type: {request_type}. Filename length in bytes: {filename_length_in_bytes}"
            )

        except KeyError:
            raise KeyError("Cant not find the request type")

        return request_type, filename_length_in_bytes

    def process_change_req(
        self, old_filename_length_in_bytes: int, req_payload: bytes
    ) -> int:
        """
        Process change request from client
        """
        old_filename = req_payload[:old_filename_length_in_bytes].decode("ascii")
        new_filename_length = int.from_bytes(
            req_payload[
                old_filename_length_in_bytes : old_filename_length_in_bytes + 1
            ],
            "big",
        )
        new_filename = req_payload[old_filename_length_in_bytes + 1 :].decode("ascii")

        actual_new_filename_length = len(new_filename)

        try:
            if new_filename_length <= 31 or actual_new_filename_length <= 31:
                old_filename_full_path = os.path.normpath(
                    os.path.join(self.directory_path, old_filename)
                )
                new_filename_full_path = os.path.normpath(
                    os.path.join(self.directory_path, new_filename)
                )

                print(
                    f"myftp> - {self.protocol} - Changing file named {old_filename_full_path} to new file {new_filename_full_path}"
                )

                os.rename(old_filename_full_path, new_filename_full_path)

                return rescode_success_dict["correct_put_and_change_request_rescode"]

            else:
                print(
                    f"myftp> - {self.protocol} - New file name longer than 31 characters error"
                )
                return rescode_fail_dict["unsuccessful_change_rescode"]

        except Exception as error:
            traceback_info = traceback.format_exc()

            print(f"myftp> - {self.protocol} - {error} happened.")

            print(traceback_info)
            return rescode_fail_dict["unsuccessful_change_rescode"]

    def process_summary_req(
        self, filename_length: int, req_payload: bytes
    ) -> Tuple[int, Optional[str], Optional[int], Optional[bytes]]:
        """
        Find the filename mentioned
        Calculate the min,max,avg
        Put those numbers into a file called summary.txt
        """
        filename = req_payload[:filename_length].decode("ascii")

        print(
            f"myftp> - {self.protocol} - Summarizing the file named {filename} on the server"
        )

        try:
            with open(os.path.join(self.directory_path, filename), "r") as file:
                numbers = [int(line.strip()) for line in file if line.strip().isdigit()]

                # Find the largest, smallest, and calculate the average
                largest_number = max(numbers)
                smallest_number = min(numbers)
                average_value = sum(numbers) / len(numbers) if numbers else 0

                print(
                    f"myftp> - {self.protocol} - File {filename} summarized successfully. The max is {largest_number}, the min is {smallest_number}, the average is {average_value}"
                )

                with open(
                    os.path.join(self.directory_path, "summary.txt"), "w"
                ) as summary_file:
                    summary_file.write(f"min: {smallest_number}\n")
                    summary_file.write(f"max: {largest_number}\n")
                    summary_file.write(f"avg: {average_value}\n")

                print(
                    f"myftp> - {self.protocol} - Created file summary.txt summarized successfully. Sending it back to the client"
                )

                with open(
                    os.path.join(self.directory_path, "summary.txt"), "rb"
                ) as summary_file:
                    binary_content = summary_file.read()

                return (
                    rescode_success_dict["correct_summary_request_rescode"],
                    "summary.txt",
                    11,
                    binary_content,
                )

        except Exception as error:
            traceback_info = traceback.format_exc()

            print(f"myftp> - {self.protocol} - {error} happened.")

            print(traceback_info)
            return rescode_fail_dict["file_not_error_rescode"], None, None, None

    def process_put_req(self, filename_length: int, req_payload: bytes) -> int:
        """
        Reconstruct file put by client
        """
        filename = req_payload[:filename_length].decode("ascii")
        filesize = int.from_bytes(
            req_payload[filename_length : filename_length + 4], "big"
        )
        file_content = req_payload[filename_length + 4 :]

        print(
            f"myftp> - {self.protocol} - Reconstructing the file {filename} of size {filesize} bytes on the server after the client finished sending"
        )

        try:
            with open(os.path.join(self.directory_path, filename), "wb") as file:
                file.write(file_content)

                print(
                    f"myftp> - {self.protocol} - File {filename} uploaded successfully"
                )

                return rescode_success_dict["correct_put_and_change_request_rescode"]

        except Exception as error:
            traceback_info = traceback.format_exc()

            print(f"myftp> - {self.protocol} - {error} happened.")

            print(traceback_info)
            return rescode_fail_dict["unsuccessful_change_rescode"]

    def process_get_req(
        self, second_byte_to_byte_n: bytes
    ) -> Tuple[Optional[str], Optional[bytes], Optional[int]]:
        """
        Process the get request

        If successful, return the filename, content and the content_length

        If not, return None, None, None tuple
        """
        filename = second_byte_to_byte_n.decode("ascii")
        print(f"myftp> - {self.protocol} - trying to find file {filename}")

        try:
            with open(os.path.join(self.directory_path, filename), "rb") as file:
                content = file.read()
                content_length = len(content)

                return filename, content, content_length

        except FileNotFoundError:
            print(f"myftp> - {self.protocol} - file {filename} not found")
            return (None, None, None)

        except IsADirectoryError:
            print(f"myftp> - {self.protocol} - filename is blank")
            return (None, None, None)

    # assembling the payload to send back to the client
    def build_res_payload(
        self,
        rescode: int,
        filename_length: Optional[int] = None,
        filename: Optional[str] = None,
        response_data: Optional[bytes] = None,
    ) -> bytes:
        print(
            f"myftp> - {self.protocol} - Assembling response payload to be sent back to the client"
        )

        data_len = len(response_data) if response_data is not None else None

        print(
            f"myftp> - {self.protocol} - Rescode {format(rescode, '03b')}"
        ) if self.debug else None

        print(
            f"myftp> - {self.protocol} - Length of data {data_len}"
        ) if self.debug else None

        print(
            f"myftp> - {self.protocol} - Data {response_data}"
        ) if self.debug else None

        # convert to binary
        try:
            # get case
            if filename is not None:
                first_byte = ((rescode << 5) + len(filename)).to_bytes(1, "big")
            # help case
            elif filename is None and response_data is not None:
                first_byte = ((rescode << 5) + len(response_data)).to_bytes(1, "big")
            # other cases
            else:
                first_byte = (rescode << 5).to_bytes(1, "big")

            # we only need the firstbyte
            if filename is None:
                second_byte_to_FL_plus_five = None
            # second byte and more are needed
            else:
                # get case
                second_byte_to_FL_plus_five = (
                    filename.encode() + len(response_data).to_bytes(4, "big")
                    if response_data is not None
                    else None
                )

            print(
                f"myftp> - {self.protocol} - First byte assembled for rescode {format(rescode, '03b')}: {bin(int.from_bytes(first_byte, byteorder='big'))[2:]}"
            ) if self.debug else None

            # get/summary case
            if second_byte_to_FL_plus_five is not None and response_data is not None:
                res_payload = first_byte + second_byte_to_FL_plus_five + response_data
            # help case
            elif second_byte_to_FL_plus_five is None and response_data is not None:
                res_payload = first_byte + response_data
            # change/put case
            else:
                res_payload = first_byte

            return res_payload

        except Exception:
            raise


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

    # start the server
    server = Server(
        args.ip_addr,
        args.port_number,
        args.directory,
        args.debug,
        ("UDP" if protocol_selection == "2" else "TCP"),
    )

    server.run()


if __name__ == "__main__":
    init()
