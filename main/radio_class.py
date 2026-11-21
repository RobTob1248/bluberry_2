import json
from ST7735 import TFTColor

def color(r, g, b):
    return(TFTColor(b, r, g))

class BluberryApp:
    name = ""
    icon = [[(0, 0, 0) for _ in range(30)] for _ in range(30)]
    
    def begin():
        pass
        
    def notif():
        pass
    
    def main():
        pass
    
    def end():
        pass

class Message:
    def __init__(self, sender, kind, receiver, text, connected, inter, tim, ident, app):
        self.sender = sender
        self.kind = kind
        self.receiver = receiver
        self.text = text
        self.connected = connected
        self.inter = inter
        self.tim = tim
        self.ident = ident
        self.app = app

class Time:
    def __init__(self, tim):
        self.year = tim[0]
        self.mon = tim[1]
        self.day = tim[2]
        self.hour = tim[4]
        self.min = tim[5]
        self.sec = tim[6]
    
    def tup(self):
        return (self.year, self.mon, self.day, 0, self.hour, self.min, self.sec, 0)

class AppMessageOut:
    def __init__(self, receiver, text, kind):
        self.receiver = receiver
        self.text = text
        self.kind = kind

class AppMessageIn:
    def __init__(self, sender, text, tim):
        self.sender = sender
        self.text = text
        self.tim = tim

class SecondaryMessage:
    def __init__(self, receiver, text, tim, ident, app):
        self.receiver = receiver
        self.text = text
        self.tim = tim
        self.ident = ident
        self.app = app

def message_bytes(message: Message):
    bools = {True: "T", False: "F", None: "N"}
    
    total_len = len(message.text) + len(json.dumps(message.tim)) + len(message.app)
    
    if total_len > 126:
        message.text = message.text[:len(message.text)-(total_len-126)]
    
    new_text = ""
    new_text += message.sender
    new_text += message.kind
    new_text += message.receiver
    new_text += bools[message.connected]
    new_text += message.inter
    new_text += message.ident
    new_text += message.text
    new_text += "|"
    new_text += json.dumps(message.tim)
    new_text += "|"
    new_text += message.app
    
    return new_text.encode()

def bytes_message(old_text: bytes):
    bools = {"T": True, "F": False, "N": None}
    
    old_text = old_text.decode()
             
    message = {}
    
    message["sender"] = old_text[:2]
    message["kind"] = old_text[2]
    message["receiver"] = old_text[3:5]
    message["connected"] = bools[old_text[5]]
    message["inter"] = old_text[6:8]
    message["ident"] = old_text[8:16]
    
    rest = old_text[16:].split("|")
    
    message["text"] = rest[0]
    message["tim"] = json.loads(rest[1])
    message["app"] = rest[2]
    
    return Message(**message)
    
    

class KeypadButton:
    def __init__(self, keypad, key):
        self.keypad = keypad
        self.key = key
        self.pressed = False
        self.dont_skip = False
        self.last_pressed = False
    
    def update(self):
        if self.last_pressed:
            self.pressed = False
            self.last_pressed = False
        
        elif self.key in self.keypad.pressed_keys and not self.dont_skip:
            self.dont_skip = True
            self.pressed = True
            self.last_pressed = True
        
        elif self.key not in self.keypad.pressed_keys and self.dont_skip:
            self.dont_skip = False
        
        return self.pressed
            
class AppButton:
    def __init__(self, key):
        self.key = key
        self.pressed = False
        self.dont_skip = False
        self.last_pressed = False
    
    def update(self, pk):
        if self.last_pressed:
            self.pressed = False
            self.last_pressed = False
        
        elif self.key in pk and not self.dont_skip:
            self.dont_skip = True
            self.pressed = True
            self.last_pressed = True
        
        elif self.key not in pk and self.dont_skip:
            self.dont_skip = False
        
        return self.pressed

class AppButtons:
    def __init__(self, buttons):
        self.pressed_keys = buttons[0]
        self.screen_buttons = buttons[1]
        self.shift = buttons[2]

class AppReturn:
    def __init__(self, fb, messages, buzz):
        self.fb = fb
        self.messages = messages
        self.buzz = buzz
