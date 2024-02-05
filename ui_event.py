import socket
import win接口 as Ws

buffer_ip = ""


def _get_local_ip():
    global buffer_ip
    if buffer_ip != "":
        return buffer_ip
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    ip = s.getsockname()[0]
    s.close()
    buffer_ip = ip
    return buffer_ip


import ipaddress


def get_broadcast_ip():
    ip = _get_local_ip()
    ip_int = int(ipaddress.ip_address(ip))
    cnet_mask = int(ipaddress.ip_address("255.255.255.0"))
    mult_mask = int(ipaddress.ip_address("0.0.0.255"))
    return str(ipaddress.ip_address(ip_int & cnet_mask | mult_mask))


real_get_ip = False


def check_ip_but_event(next_func):
    def _():
        global real_get_ip
        real_get_ip = not real_get_ip
        if real_get_ip:
            next_func(_get_local_ip())
        else:
            next_func("查看ip")

    return _


def get_upload_file_but_event(next_func):
    def _():
        name = Ws.get_filename()
        next_func(name)

    return _


def get_download_path_but_event(next_func):
    def _():
        name = Ws.get_dir()
        next_func(name)

    return _


if __name__ == '__main__':
    for i in range(5):
        print(i)
    print(get_broadcast_ip())
