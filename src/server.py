import socket
import threading
import time

from src.settings import LANG


class Server(threading.Thread):  # Server object is type thread so that it can run simultaneously with the client
    def __init__(self, chat_app):  # Initialize with a reference to the Chat App and initial vars
        super(Server, self).__init__()
        self.chat_app = chat_app
        self.port = self.chat_app.port  # Get the server port from the Chat App reference
        self.host = ""  # Accept all hostnames
        self.has_connection = False  # Connection status
        self.stop_socket = False  # Socket interrupt status

        # Information exchange commands used to communicate between peers
        self.commands = {
            "nick": [self.set_peer_nickname, 1],
            "quit": [self.peer_quit, 0],
            "syntaxErr": [self.chat_client_versions_out_of_sync, 0]
        }

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create new socket
        self.socket.bind((self.host, self.port))  # Bind the socket to host and port stored in the servers vars
        self.socket.listen()  # Set socket mode to listen

        self.chat_app.system_message(LANG['serverStarted'].format(self.port))

    # Method to handle information exchange commands
    def handle_command(self, command):
        command = command.decode().split(" ")
        if len(command) > 1:
            args = command[1:]
        command = command[0][2:]

        if self.commands.get(command) is not None:
            if self.commands[command][1] == 0:
                self.commands[command][0]()
            elif len(args) == self.commands[command][1]:
                self.commands[command][0](args)
            else:
                self.chat_app.system_message(LANG['peerInvalidSyntax'])
                self.chat_app.client.send("\b/syntaxErr")
        else:
            self.chat_app.system_message(LANG['peerInvalidCommand'])
            self.chat_app.client.send("\b/syntaxErr")

    # Method called by threading on start
    def run(self):
        conn, addr = self.socket.accept()  # Accept a connection
        if self.stop_socket:  # Stop the socket if interrupt is set to true
            exit(1)
        init = conn.recv(1024)  # Wait for initial information from client
        self.has_connection = True  # Set connection status to true

        self.handle_init(init)

        while True:  # Receive loop
            if len(self.chat_app.form.feed.values) > self.chat_app.form.y - 10:
                self.chat_app.clear_chat()

            data = conn.recv(1024)  # Wait for data
            if not data:
                # If data is empty throw an error
                self.chat_app.system_message(LANG['receivedEmptyMessage'])
                self.chat_app.system_message(LANG['disconnectSockets'])
                break

            if data.decode().startswith('\b/'):
                # If data is command for information exchange call the command handler
                self.handle_command(data)
                if data.decode() == '\b/quit':
                    break
            else:
                # Else display the message in chat feed and append it to chat log
                self.chat_app.message_log.append("{0} >  {1}".format(self.chat_app.peer, data.decode()))
                self.chat_app.form.feed.values.append("{0} >  {1}".format(self.chat_app.peer, data.decode()))
                self.chat_app.form.feed.display()

    def handle_init(self, init):
        if not init:  # If initial information is empty, set peer vars to unknown
            self.chat_app.peer = "Unknown"
            self.chat_app.peer_port = "unknown"
            self.chat_app.peer_ip = 'unknown'
        else:  # Decode initial information and set peer vars to values send by peer
            init = init.decode()
            if init.startswith("\b/init"):
                init = init[2:].split(' ')
                self.chat_app.peer = init[1]
                self.chat_app.peer_ip = init[2]
                self.chat_app.peer_port = init[3]
            else:  # If initial information is not sent correctly
                self.chat_app.peer = "Unknown"
                self.chat_app.peer_port = "unknown"
                self.chat_app.peer_ip = 'unknown'

        if not self.chat_app.client.is_connected:
            # Send message to inform about connectBack if client socket is not connected
            if self.chat_app.peer_ip == "unknown" or self.chat_app.peer_port == "unknown":
                self.chat_app.system_message(LANG['failedConnbackPeerUnknown'])
            else:
                self.chat_app.system_message(LANG['connbackInfo'])
                self.chat_app.system_message(
                    LANG['connbackHostInfo'].format(self.chat_app.peer_ip, self.chat_app.peer_port)
                )

        self.chat_app.system_message(LANG['peerConnected'].format(self.chat_app.peer))  # Inform user about peer

    # Method called by Chat App to reset server socket
    def stop(self):
        if self.has_connection:
            self.socket.close()
        else:
            self.stop_socket = True
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('localhost', self.port))
            time.sleep(0.2)
            self.socket.close()

        self.socket = None

    # Method called if command for nickname change was received
    def set_peer_nickname(self, nick):
        old_nick = self.chat_app.peer
        self.chat_app.peer = nick[0]
        self.chat_app.system_message(LANG['peerChangedName'].format(old_nick, nick[0]))

    # Method called if connected peer quit
    def peer_quit(self):
        self.chat_app.system_message(LANG['peerDisconnected'].format(self.chat_app.peer))
        self.chat_app.client.is_connected = False
        self.chat_app.restart()

    # Method called if connected peer uses an invalid information exchange command syntax
    def chat_client_versions_out_of_sync(self):
        self.chat_app.system_message(LANG['versionOutOfSync'])
