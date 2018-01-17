"""
Main program
"""
import os
import socket
import threading

from lib.connection import Connection
from lib.receiver import ReceiverThread
from lib.repository.repositories import Repositories
from lib.supervisor import SupervisorThread


class Main(object):
    """
    Main class
    """
    def __init__(self, socket_port, db_file):
        self.__socket_port = socket_port
        self.__event = threading.Event()
        self.__db_file = db_file
        self.__repositories = Main.get_repositories(db_file)
        self.__socket = None
        self.__prepare_socket()

        gpio_repository = self.__repositories.get_gpio_repository()
        gpios = gpio_repository.get_all_gpio()
        ReceiverThread.gpios = gpios
        self.__supervisor = SupervisorThread(gpios, self.__event)
        Main.prepare_gpios(gpios)
        self.__supervisor.start()

    def listen_new_connection(self):
        # Wait for a connection
        conn, client_address = self.__socket.accept()
        connection = Connection(conn, (client_address[0], self.__socket_port), self.__event, self.__db_file)
        connection.start()

    def close_socket_connection(self):
        self.__socket.close()

    def __prepare_socket(self):
        if not self.__socket:
            # Create a TCP/IP socket
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind the socket to the port
        server_address = ('', self.__socket_port)
        self.__socket.bind(server_address)
        # Listen for incoming connections
        self.__socket.listen(1)

    @staticmethod
    def get_repositories(db_file):
        repositories = Repositories(db_file)
        gpio_repo = repositories.get_gpio_repository()
        gpio_repo.create_table()
        return repositories

    @staticmethod
    def prepare_gpios(gpios):
        """
        Prepare the gpio port to be used
        """
        for gpio in gpios:
            service_path = os.path.dirname(os.path.realpath(__file__))
            script_path = os.path.join(service_path, 'lib', 'gpio_setup.sh')
            os.system("sh " + script_path + " " + str(gpio.get_port()))
