import socket
import os
import time
from 工具箱.局域网传输.QT工具 import win接口 as win

file_name = win.get_filename()

tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

tcp_server_socket.bind(("", 8080))

tcp_server_socket.listen(2)


def print_process(up_size, now_size, max_size, begin_time):
    spend = time.time() - begin_time
    n = int(now_size / max_size * 100)
    if n == int(now_size - up_size / max_size * 100):
        return
    m = 100 - n
    print(">" * n + "=" * m + "   " + format_ispeed(up_size / spend))


def format_ispeed(num):
    type_list = ['b/s', 'kb/s', 'mb/s', 'gb/s']
    i = 0
    while num >= 1024:
        num = num / 1024
        i += 1
        if i == len(type_list) - 1:
            break
    return "{:.2f} {}".format(num, type_list[i])


while True:
    print("等待连接")
    client_socket, client_ip = tcp_server_socket.accept()
    print("客户端：", client_ip, "连接")

    try:
        with open(file_name, 'rb') as file:
            send_size = 0
            file.seek(0, os.SEEK_END)
            max_size = file.tell()
            print("文件大小:", max_size)
            file.seek(0, 0)
            while True:
                a = time.time()
                file_data = file.read(8388608)
                send_size += 8388608
                if file_data:
                    client_socket.send(file_data)
                    print_process(8388608, send_size, max_size, a)
                else:
                    print("传输完成")
                    break
    except Exception as e:
        print("传输异常:", e)
    client_socket.close()
