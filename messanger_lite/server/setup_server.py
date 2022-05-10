from setuptools import setup, find_packages

setup(
    name='messanger_lite_server',
    version='1.0.1',
    description='messanger_lite_server',
    author='Idel Yusupov',
    author_email='idel@mail.ru',
    packages=find_packages(),
    install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
)
