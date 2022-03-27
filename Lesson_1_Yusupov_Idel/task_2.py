"""
Написать функцию host_range_ping() для перебора ip-адресов из заданного
диапазона. Меняться должен только последний октет каждого адреса. По
результатам проверки должно выводиться соответствующее сообщение.
"""
from pprint import pprint
from ipaddress import ip_network

from task_1 import host_ping


def host_range_ping(network):
    result = []
    try:
        hosts = list(map(str, ip_network(network).hosts()))
    except ValueError as err:
        print(err)
    else:
        count = 255
        for host in host_ping(hosts):
            if not count:
                break
            count -= 1
            result.append(f'{host[0].ljust(12)} {host[1].ljust(15)} {host[2]}')
    return result


if __name__ == '__main__':
    pprint(host_range_ping('173.194.73.0/31'))
