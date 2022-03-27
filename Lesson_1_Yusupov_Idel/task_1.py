"""
Написать функцию host_ping(), в которой с помощью утилиты ping будет
проверяться доступность сетевых узлов. Аргументом функции является список, в
котором каждый сетевой узел должен быть представлен именем хоста или
ip-адресом. В функции необходимо перебирать ip-адреса и проверять их
доступность с выводом соответствующего сообщения («Узел доступен», «Узел
недоступен»). При этом ip-адрес сетевого узла должен создаваться с помощью
функции ip_address().
"""
from ipaddress import ip_address
from socket import gethostbyname, gaierror
from subprocess import call, PIPE
from pprint import pprint


def to_ip(host):
    try:
        if type(host) in (str, int):
            ip = str(ip_address(host))
        else:
            return False
    except ValueError:
        try:
            ip = gethostbyname(host)
        except gaierror:
            return False
    return ip


def host_ping(lst):
    result = []
    for host in lst:
        ip_addr = to_ip(host)
        if ip_addr:
            response = call(['ping', '-n', '2', ip_addr], stdout=PIPE)
            if response == 0:
                result.append(('Доступен', str(host), f'[{ip_addr}]'))
                continue
        result.append(('Недоступен', str(host),
                      f'[{ip_addr if ip_addr else "Не определён"}]'))

    return result


if __name__ == '__main__':
    pprint(host_ping(['8.8.8.8', '9.9.9.9', 'yandex.ru', 'youtube.com', 'tt']))
