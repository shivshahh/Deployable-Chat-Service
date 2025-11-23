# Message types
NORMAL_MSG = 0x00
HISTORY_MSG = 0x01
HISTORY_END_MSG = 0x02

class Message:
    def __init__(self, username, msg_type, message):
        self.username = username
        self.msg_type = msg_type
        self.messsage = message

    def __str__(self):
        return "Username: " + self.username + "\nType: " + self.msg_type + "\nMessage: " + self.messsage