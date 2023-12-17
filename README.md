# MyFTP

A Python implementation of a FTP server. Supports both TCP and UDP protocols. Tested on Python 3.11 and Python 3.10.

## Dependencies

Zero. Only python standard libs were used. 

## Running

### Client

You can run `python3 src/myftp/client.py --directory <insert valid directory that you have read/write permissions>` to start the client.

To run with debug info: `python3 src/myftp/client.py --debug 1 --directory <insert valid directory that you have read/write permissions>`.

Some example test commands:

- `get file_server.txt`
- `summary numbers.txt`
- `put file_local.txt`
- `put image_local.png`
- `change file_server.txt file_server1.txt`
- `help`

### Server

By default, the server IP address or hostname or server name will be `0.0.0.0` or `localhost` (meaning it will bind to all interfaces). The `--port_number` flag, if not specified will be by default `12000`.

You can run `python3 src/myftp/server.py --directory <insert valid directory that you have read/write permissions>` to start the server.

Or run `python3 src/myftp/server.py --ip_addr <insert ip addr of the server> --port_number <insert port number here> --debug 1 --directory <insert valid directory that you have read/write permissions>` for debugging purposes.

## Localhost testing

Checkout this repo, go the root of the repo.

### Client

Run `python3 src/myftp/client.py --debug 1 --directory client_directory`

### Server

Run `python3 src/myftp/server.py --debug 1 --directory server_directory`

## Testing with Docker

### Dependencies

- `docker`
- `docker-compose`
- `make`

### Setup

- Make you are at the root of this repo.
- Build the system with `make build`.
- Wait 10 seconds.
- 2 containers will be created on the same network `mynetwork`. Their respective IP addresses will be printed to stdout.
- Open two terminal windows: one for each of server and client.
- Run the server with `make server` in a terminal.
- Run the client with `make client` in a terminal.
- For the client, when asked to put in the ip address and port number of the server, you can put in `ftp_server 12000` or adjust to your chosen port number. The IP address is resolved by Docker so ftp_server can not be changed.
- Go into the `client` docker container with `make docker-client`. The folder in which FTP is using to host client files is located at `/client_directory/`
- Or go into the `server` docker container with `make docker-server`. The folder in which FTP is using to host server files is located at `/server_directory/`
- Tear down everything with `make clean`.

#### Fast setup

- Require `tmuxinator` and `tmux`.
- Type `tmuxinator start .` at the root of this repo.
