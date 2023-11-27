# MyFTP

## Dependencies

Zero. Only python standard libs were used.

## Running

### Client

You can run `python3 src/myftp/client.py` to start the client or `python3 src/myftp/client.py --debug 1` for debugging purposes.

### Server

By default, the server IP address or hostname or server name will be `0.0.0.0` (meaning it will bind to all interfaces). The `--port_number` flag, if not specified will be by default `12000`.

You can run `python3 src/myftp/server.py` to start the server or `python3 src/myftp/server.py --ip_addr <insert ip addr of the server> --port_number <insert port number here> --debug 1` for debugging purposes and to specify the port number.

## Testing with Docker

### Dependencies

`docker` and `docker-compose`

### Setup

- Make you are at the root of this repo.
- Build the system with `docker-compose up --build --remove-orphans`.
- Wait 10 seconds.
- 2 containers will be created on the same network `mynetwork`. Their respective IP addresses will be printed to stdout.
- Open two terminal windows: one for each of server and client.
- Run the server with `docker exec -it project-ftp_server_1 python server.py <insert any flags here>`.
- Run the client with `docker exec -it project-ftp_client_1 python client.py <insert any flags here>`.
- For the client, when asked to put in the ip address and port number of the server, you can put in `ftp_server 12000` or adjust to your chosen port number. The IP address is resolved by Docker so ftp_server can not be changed.
- Tear down everything with `docker-compose down`.
