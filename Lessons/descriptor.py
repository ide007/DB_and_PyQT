from logs.server_log_config import server_logger as log

logger = log.debug('Server')


class PortDescriptor:
    def __set__(self, instance, value):

        if not 1023 < value < 65536:
            logger.critical(f'Попытка запуска севера с указанием некорректного'
                            f'номера порта: {value}. Допустимы порт в '
                            f'интервале от 1024 до 65535.')
            exit(1)

        instance.__dict__[self.port] = value

    def __set_name__(self, owner, port):

        self.port = port
