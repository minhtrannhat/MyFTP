# MyFTP

## Dependencies

Zero. Only python standard libs were used.

## Running

### Client

You can run `python3 src/myftp/client.py` to start the client or `python3 src/myftp/client.py --debug 1` for debugging purposes.

### Server

By default, the server IP address or hostname or server name will be `127.0.0.1` (also known as `localhost`). The `--port_number` flag, if not specified will be by default `12000`.

You can run `python3 src/myftp/server.py` to start the server or `python3 src/myftp/server.py --port_number <insert port number here> --debug 1` for debugging purposes and to specify the port number.
