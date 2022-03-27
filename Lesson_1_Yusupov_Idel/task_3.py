"""
Написать функцию host_range_ping_tab(), возможности которой основаны на функции
из примера 2. Но в данном случае результат должен быть итоговым по всем
ip-адресам, представленным в табличном формате (использовать модуль tabulate).
Таблица должна состоять из двух колонок и выглядеть примерно так:
Reachable
10.0.0.1
10.0.0.2

Unreachable
10.0.0.3
10.0.0.4
"""
from tabulate import tabulate
from itertools import zip_longest

from task_2 import host_range_ping


def host_range_ping_tab(network):
    lst = host_range_ping(network)
    headers = [('Reachable', 'Unreachable')]
    result = [[], []]
    for i in lst:
        i = i.split()
        if len(i[0]) == 8:
            result[0].append(f'{i[1]}')
        else:
            result[1].append(f'{i[1]}')
    headers.extend(list(zip_longest(result[0], result[1])))

    print(tabulate(headers, headers='firstrow', stralign='center',
                   tablefmt='pipe'))


host_range_ping_tab('173.194.73.0/29')
