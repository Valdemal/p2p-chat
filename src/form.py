import npyscreen
import curses

from .settings import LANG


class ChatForm(npyscreen.FormBaseNew):
    def create(self):
        self.y, self.x = self.useable_space()
        self.feed = self.add(npyscreen.BoxTitle, name=LANG['interface']['feed'], editable=False,
                             max_height=self.y - 7)
        self.input = self.add(ChatInput, name=LANG['interface']['input'], footer=LANG['interface']['footer'],
                              rely=self.y - 5)
        self.input.entry_widget.handlers.update({curses.ascii.CR: self.parentApp.send_message})
        self.input.entry_widget.handlers.update({curses.ascii.NL: self.parentApp.send_message})
        self.input.entry_widget.handlers.update({curses.KEY_UP: self.parentApp.history_back})
        self.input.entry_widget.handlers.update({curses.KEY_DOWN: self.parentApp.history_forward})
        self.input.entry_widget.handlers.update({curses.KEY_DOWN: self.parentApp.history_forward})

        handlers = {
            "^V": self.parentApp.paste_from_clipboard
        }
        self.add_handlers(handlers)


class ChatInput(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEdit
