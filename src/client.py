import socket
import threading

from src.settings import LANG


class Client(threading.Thread):  # Client object is type thread so that it can run simultaneously with the server
    def __init__(self, chat_app):  # Initialize with a reference to the Chat App
        super(Client, self).__init__()
        self.chat_app = chat_app
        self.is_connected = False
        self.socket = None

    # Start method called by threading module
    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)

    def conn(self, args):

        if self.chat_app.nickname == "":  # Check if a nickname is set and return False if not
            self.chat_app.system_message(LANG['nickNotSet'])
            return False

        host = args[0]  # IP of peer
        port = int(args[1])  # Port of peer
        self.chat_app.system_message(LANG['connectingToPeer'].format(host, port))

        try:
            self.socket.connect((host, port))
        except socket.error:
            self.chat_app.system_message(LANG['failedConnectingTimeout'])
            return False

        # Exchange initial information (nickname, ip, port)
        self.socket.send(f"\b/init {self.chat_app.nickname} {self.chat_app.hostname} {self.chat_app.port}".encode())
        self.chat_app.system_message(LANG['connected'])
        self.is_connected = True  # Set connection status to true

    # Method called by Chat App to reset client socket
    def stop(self):
        self.socket.close()

    # Method to send data to a peer
    def send(self, msg):
        if msg != '':
            try:
                self.socket.send(msg.encode())
                return True
            except socket.error as error:
                self.chat_app.system_message(LANG['failedSentData'])
                self.chat_app.system_message(error)
                self.is_connected = False
                return False
