import json
import os
import socket
import time
from ui_event import get_broadcast_ip
import Decorators as Dec

ORDER_READ_FILE_NAME = "准备好的文件名".encode()
ORDER_DOWNLOAD_FILE = "要求下载文件".encode()
ORDER_PING_SERVER = "PING ORDER".encode()

REPLY_PONG_CLIENT = "PONG REPLY".encode()

max_recv_data = 8388608
tcp_port = 8001
udp_port = 8002


def encode_data_with_process(file_data, max_size, completed_size):
    j = {
        "file_data": file_data,
        "max_size": max_size,
        "completed_size": completed_size
    }

    return json.dumps(j).encode()


def decode_data_with_process(data):
    j = data.decode()
    dic = json.loads(j)
    return dic["file_data"], dic["max_size"], dic["completed_size"]


def encode_hello_data(server_id, filename):
    j = {
        "server_id": server_id,
        "filename": filename
    }
    return json.dumps(j).encode()


def decode_hello_data(data_byte):
    j = json.loads(data_byte.decode())
    return j["server_id"], j["filename"]


class Client:

    @Dec.thread_dec
    def check_active_server(self, timeout=10, process_func=None, max_times=10, empty_func=None, effective_func=None):
        active_server_ip_list = []
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.sendto(ORDER_PING_SERVER, (get_broadcast_ip(), udp_port))
        udp_socket.settimeout(timeout)
        for i in range(max_times):
            try:
                msg, addr = udp_socket.recvfrom(1024)
            except TimeoutError as _e:
                break
            else:
                if addr[0] not in active_server_ip_list:
                    active_server_ip_list.append(addr[0])
                    if process_func is not None:
                        process_func(*decode_hello_data(msg), addr[0])
        udp_socket.close()
        if len(active_server_ip_list) == 0:
            empty_func()
        else:
            effective_func()

    def connect_server(self, server_ip):
        tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_client.connect((server_ip, tcp_port))
        return tcp_client

    @Dec.thread_dec
    def ask_wait_file(self, server_ip, next_func, timeout_func, timeout=30):
        try:
            tcp_client = self.connect_server(server_ip)
            tcp_client.settimeout(timeout)
            tcp_client.send(ORDER_READ_FILE_NAME)
            text = tcp_client.recv(max_recv_data).decode()
            next_func(text)
            tcp_client.close()
        except TimeoutError as e:
            timeout_func()
        except Exception as e:
            print("ask_wait_file error:", e)

    @Dec.thread_dec
    def download_file(self, server_ip, filename, process_func, timeout_func, final_func):
        try:
            tcp_client = self.connect_server(server_ip)
        except TimeoutError as e:
            timeout_func()
        except Exception as e:
            print("download_file error:", e)
        else:
            print("下载目录：",filename)
            try:
                tcp_client.send(ORDER_DOWNLOAD_FILE)
                max_size = int(tcp_client.recv(1024).decode())
                completed_size = 0
                with open(filename, "wb") as file:
                    while True:
                        begin_time = time.time()
                        file_date = tcp_client.recv(8388608)
                        if file_date:
                            file.write(file_date)
                            now_size = len(file_date)
                            completed_size += now_size
                            speed_time = time.time() - begin_time
                            if speed_time <= 0:
                                speed = "-"
                            else:
                                speed = format_ispeed(now_size / speed_time)
                            process_func(completed_size, max_size, speed)
                        else:
                            break
            except Exception as e:
                print("下载异常", e)
            else:
                final_func()
            finally:
                tcp_client.close()


def format_ispeed(num, is_speed=True):
    if is_speed:
        type_list = ['B/s', 'KB/s', 'MB/s', 'GB/s']
    else:
        type_list = ['B', 'KB', 'MB', 'GB']
    i = 0
    while num >= 1024:
        num = num / 1024
        i += 1
        if i == len(type_list) - 1:
            break
    return "{:.2f} {}".format(num, type_list[i])


class Server:
    def __init__(self, read_filename_func=None, client_download_func=None,read_server_id_func=None):
        self.read_server_id_func = read_server_id_func
        self.client_download_func = client_download_func
        self.read_filename_func = read_filename_func
        self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server.bind(("", tcp_port))
        self.tcp_server.listen(10)
        self.udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_server.bind(("0.0.0.0", udp_port))
        self.wait_connect_tcp()
        self.wait_connect_udp()

    def close(self):
        self.tcp_server.close()
        self.udp_server.close()

    @Dec.thread_dec
    def wait_connect_udp(self):
        while True:
            try:
                msg, addr = self.udp_server.recvfrom(1024)
            except OSError:
                break
            else:
                if msg == ORDER_PING_SERVER:
                    filename = os.path.basename(self.read_filename_func())
                    server_id = self.read_server_id_func()
                    self.udp_server.sendto(encode_hello_data(server_id, filename), addr)


    @Dec.thread_dec
    def wait_connect_tcp(self):
        while True:
            try:
                client_socket, client_ip = self.tcp_server.accept()
            except OSError:
                break
            else:
                self.deal_order(client_socket, client_ip)

    @Dec.thread_dec
    def deal_order(self, client_socket, client_ip):
        while True:
            order = client_socket.recv(max_recv_data)
            if order == ORDER_READ_FILE_NAME:
                client_socket.send(os.path.basename(self.read_filename_func()).encode())
            elif order == ORDER_DOWNLOAD_FILE:
                try:
                    if self.read_filename_func is None:
                        raise ValueError("read_filename_func is None")
                    filename = self.read_filename_func()
                    base_name = os.path.basename(filename)
                    with open(filename, 'rb') as file:
                        send_size = 0
                        file.seek(0, os.SEEK_END)
                        max_size = file.tell()
                        client_socket.send("{}".format(max_size).encode())
                        file.seek(0, 0)
                        while True:
                            file_data = file.read(8388608)
                            send_size += len(file_data)
                            if file_data:
                                client_socket.send(file_data)
                                self.client_download_func(client_ip, send_size / max_size * 100, base_name)
                            else:
                                break
                except Exception as e:
                    print("传输异常:", e)
                finally:
                    break

            else:
                # 异常数据，或者客户端close
                break

        try:
            client_socket.close()
        except UnboundLocalError as e:
            print("UnboundLocalError:", e)
        except Exception as e:
            print("deal_order error:", e)


if __name__ == "__main__":
    s = Server(None, None)
    c = Client()
    c.check_active_server(process_func=lambda x: print(x))
