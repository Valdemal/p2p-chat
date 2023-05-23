import datetime
import os
import socket
import sys
import time
from io import StringIO

import npyscreen
import pyperclip

from src.client import Client
from src.server import Server
from src.form import ChatForm
from src.settings import LANG, change_lang, change_settings
from src.utils import get_public_ip


# noinspection PyAttributeOutsideInit
class ChatApp(npyscreen.NPSAppManaged):

    # Method called at start by npyscreen
    def onStart(self):

        # Add ChatForm as the main form of npyscreen
        self.form = self.addForm('MAIN', ChatForm, name=LANG['interface']['title'])

        # Get these PCs public IP and catch errors
        try:
            self.hostname = get_public_ip()
        except socket.error:
            self.system_message(LANG['noInternetAccess'])
            self.system_message(LANG['failedFetchPublicIP'])
            self.hostname = "0.0.0.0"

        # Define initial variables
        self.port = 3333  # Port the server runs on
        self.nickname = os.getlogin()
        self.peer = ""  # Peer nickname
        self.peer_ip = "0"  # IP of peer
        self.peer_port = "0"  # Port of peer
        self.history_log = []  # Array for message log
        self.message_log = []  # Array for chat log
        self.history_pos = 0  # Int for current position in message history

        self.start_threads()

        self.system_message(LANG['nicknameInfo'].format(self.nickname))

        # Dictionary for commands. Includes function to call and number of needed arguments
        self.commands = {
            "connect": [self.client.conn, 2],
            "disconnect": [self.restart, 0],
            "nickname": [self.set_nickname, 1],
            "quit": [self.exit, 0],
            "port": [self.restart, 1],
            "connectback": [self.connect_back, 0],
            "clear": [self.clear_chat, 0],
            "eval": [self.eval_code, -1],
            "status": [self.get_status, 0],
            "log": [self.log_chat, 0],
            "help": [self.help_command, 0],
            "lang": [self.change_lang, 1]
        }

        # Dictionary for command aliases
        self.commands_alias = {
            "nick": "nickname",
            "conn": "connect",
            "q": "quit",
            "connback": "connectback"
        }

        if os.name == "nt":
            os.system(LANG['interface']['title'])  # Set window title on windows

    # Start Server and Client threads
    def start_threads(self):
        self.server = Server(self)
        self.server.daemon = True
        self.client = Client(self)
        self.server.start()
        self.client.start()

    # Method to change interface language. Files need to be located in lang/
    def change_lang(self, args):
        self.system_message(LANG['changingLang'].format(args[0]))

        try:
            change_lang(args[0])
        except Exception as e:
            self.system_message(LANG['failedChangingLang'])
            self.system_message(e)
            return False

        change_settings('language', args[0])

    # Method to reset server and client sockets
    def restart(self, args=None):
        self.system_message(LANG['restarting'])

        if args is not None and args[0] != self.port:
            self.port = int(args[0])

        if self.client.is_connected:
            self.client.send("\b/quit")
            time.sleep(0.2)

        self.client.stop()
        self.server.stop()

        self.start_threads()

    # Method to scroll back in the history of sent messages
    def history_back(self, _input):
        if not self.history_log or self.history_pos == 0:
            return False
        self.history_pos -= 1
        self.form.input.value = self.history_log[len(self.history_log) - 1 - self.history_pos]

    # Method to scroll forward in the history of sent messages
    def history_forward(self, _input):
        if not self.history_log:
            return False
        if self.history_pos == len(self.history_log) - 1:
            self.form.input.value = ""
            return True
        self.history_pos += 1
        self.form.input.value = self.history_log[len(self.history_log) - 1 - self.history_pos]

    # Method to set nickname of client | Nickname will be sent to peer for identification
    def set_nickname(self, args):
        self.nickname = args[0]
        self.system_message("{0}".format(LANG['setNickname'].format(args[0])))
        if self.client.is_connected:
            self.client.send("\b/nick {0}".format(args[0]))

    # Method to render system info on chat feed
    def system_message(self, msg):
        system_prefix = f"[{LANG['interface']['system']}] "
        self.message_log.append(system_prefix + str(msg))
        if len(self.form.feed.values) > self.form.y - 10:
            self.clear_chat()
        if len(str(msg)) > self.form.x - 20:
            self.form.feed.values.append(system_prefix + str(msg[:self.form.x - 20]))
            self.form.feed.values.append(str(msg[self.form.x - 20:]))
        else:
            self.form.feed.values.append(system_prefix + str(msg))
        self.form.feed.display()

    # Method to send a message to a connected peer
    def send_message(self, _input):
        msg = self.form.input.value
        if msg == "":
            return False

        if len(self.form.feed.values) > self.form.y - 11:
            self.clear_chat()

        self.message_log.append(LANG['you'] + " > " + msg)
        self.history_log.append(msg)
        self.history_pos = len(self.history_log)
        self.form.input.value = ""
        self.form.input.display()

        if msg.startswith('/'):
            self.handle_command(msg)
        else:
            if self.client.is_connected:
                if self.client.send(msg):
                    self.form.feed.values.append(LANG['you'] + " > " + msg)
                    self.form.feed.display()
            else:
                self.system_message(LANG['notConnected'])

    # Method to connect to a peer that connected to the server
    def connect_back(self):
        if self.server.has_connection and not self.client.is_connected:
            if self.peer_ip == "unknown" or self.peer_port == "unknown":
                self.system_message(LANG['failedConnectPeerUnknown'])
                return False
            self.client.conn([self.peer_ip, int(self.peer_port)])
        else:
            self.system_message(LANG['alreadyConnected'])

    # Method to log the chat to a file | Files can be found in root directory
    def log_chat(self):
        try:
            date = datetime.datetime.now().strftime("%m-%d-%Y")
            log = open("p2p-chat-log_{0}.log".format(date), "a")
            for msg in self.message_log:
                log.write(msg + "\n")
        except FileNotFoundError:
            self.system_message(LANG['failedSaveLog'])
            return False

        log.close()
        self.message_log = []
        self.system_message(LANG['savedLog'].format(date))

    # Method to clear the chat feed
    def clear_chat(self):
        self.form.feed.values = []
        self.form.feed.display()

    # Method to run python code inside the app | Useful to print app vars
    def eval_code(self, code):
        default_std_out = sys.stdout
        redirected_std_out = sys.stdout = StringIO()
        try:
            exec(code)
        except Exception as e:
            self.system_message(e)
        finally:
            sys.stdout = default_std_out
        self.form.feed.values.append('> ' + redirected_std_out.getvalue())
        self.form.feed.display()

    # Method to exit the app | Exit command will be sent to a connected peer so that they can disconnect their sockets
    def exit(self):
        self.system_message(LANG['exitApp'])
        if self.client.is_connected:
            self.client.send("\b/quit")
        self.client.stop()
        self.server.stop()
        exit(1)

    # Method to paste text from clipboard to the chat input
    def paste_from_clipboard(self, _input):
        self.form.input.value = pyperclip.paste()
        self.form.input.display()

    # Method to handle commands
    def handle_command(self, msg):
        if msg.startswith("/eval"):
            args = msg[6:]
            self.eval_code(args)
            return True

        msg = msg.split(' ')
        command = msg[0][1:]
        args = msg[1:]
        if command in self.commands_alias:
            command = self.commands_alias[command]

        if self.commands.get(command) is not None:
            if self.commands[command][1] == 0:
                self.commands[command][0]()
            elif len(args) == self.commands[command][1]:
                self.commands[command][0](args)
            else:
                self.system_message(LANG['commandWrongSyntax'].format(command, self.commands[command][1], len(args)))
        else:
            self.system_message(LANG['commandNotFound'])

    # Method to print a list of all commands
    def help_command(self):
        if len(self.form.feed.values) + len(self.commands) + 1 > self.form.y - 10:
            self.clear_chat()

        self.system_message(LANG['commandList'])

        for command in self.commands:
            if not LANG['commands'][command] == "":
                self.system_message(LANG['commands'][command])

    # Method to print the status of server and client
    def get_status(self):
        self.system_message("STATUS:")
        server_status = bool(self.server)
        client_status = bool(self.client)

        self.system_message(
            LANG['serverStatusMessage'].format(server_status, self.port, self.server.has_connection))
        self.system_message(LANG['clientStatusMessage'].format(client_status, self.client.is_connected))

        if not self.nickname == "":
            self.system_message(LANG['nicknameStatusMessage'].format(self.nickname))


if __name__ == '__main__':
    chatApp = ChatApp().run()  # Start the app if chat.py is executed
