.PHONY: build client server clean

build:
	docker-compose up --build --remove-orphans

server:
	docker exec -it project-ftp_server-1 python server.py --port_number 12000 --debug 1 --directory /server_directory

client:
	docker exec -it project-ftp_client-1 python client.py --directory /client_directory --debug 1
	
client-no-debug:
	docker exec -it project-ftp_client-1 python client.py --directory /client_directory

clean:
	docker-compose down --volumes

docker-client:
	docker exec -it project-ftp_client-1 bash

docker-server:
	docker exec -it project-ftp_server-1 bash
