import socket
import time

server_ip = "192.168.2.102"

tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

tcp_client_socket.bind(("", 8081))

tcp_client_socket.connect((server_ip, 3587))

file_name = "黑板模型.zip"

try:
    with open(file_name, "wb") as file:
        while True:
            file_date = tcp_client_socket.recv(8388608)
            if file_date:
                file.write(file_date)
            else:
                break
except Exception as e:
    print("下载异常", e)
else:
    print(file_name, "下载成功")
tcp_client_socket.close()
