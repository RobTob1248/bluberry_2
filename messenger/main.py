from main_radio_class import *
from framebuf import FrameBuffer, RGB565
from ST7735 import TFT
import json
import time

keypad = {i: AppButton(i) for i in "123456789*0#"}

class Sending:
    last_send = None
    @classmethod
    def send(cls):
        cls.last_send = time.ticks_ms()
    @classmethod
    def sent(cls):
        if cls.last_send is not None:
            return time.ticks_diff(time.ticks_ms(), cls.last_send) <= 1500
        else:
            return False
def convert(old_text):
    keys = {
    "1": "1", 
    "2": "2abc", 
    "3": "3def",
    "4": "4ghi",
    "5": "5jkl",
    "6": "6mno",
    "7": "7prs",
    "8": "8tuv",
    "9": "9wxy",
    "0": "0 .,"
    }
    
    #print(old_text)
    
    try:
        if old_text[-1] == "*":
            delete = True
            old_text = old_text[:-1]
        else:
            delete = False
    except:
        delete = False
        
    #print(old_text)
    
    old = old_text.split("#")
    
    #print(old)
    
    if delete:
        old.pop()
        try:
            for i in range(2):
                if old[-1] == "":
                    old.pop()
            
            old.pop()
        except:
            pass

    #print(old)
    
    new = ""
    try:
        if old[-2] == "" and old[-1] == "":
            done = True
        else:
            done = False
    except:
        done = False
    
    for i in old:
        if len(i) > 0:
            key = i[-1]
            index = len(i) % len(keys[key]) - 1
            new += keys[key][index]
    
    old_text = "#".join(old)
    if delete and len(old_text) > 0:
        old_text += "#"
    
    if delete and len(old_text) == 0:
        back = True
    else:
        back = False
    
    return [new, old_text, done, back]

menu = ["", ""]
option = 0
options = ["Send to:", "Text:"]


class Messenger:
    name = "Messenger"
    icon = FrameBuffer(bytearray(30*30*2), 30, 30, RGB565)
    icon.rect(0, 0, 30, 30, color(255, 255, 2555))
    icon.fill_rect(1, 1, 28, 28, color(255, 0, 0))
    
    def begin():
        pass
    
    def notif(messages, time):
        notifs = []
        
        for i in messages:
            notifs.append(f"{i.sender} sent: {i.text}")
        
        return notifs
    
    def main(buttons, fb, time):
        global menu
        global option
        
        [i.update(buttons.pressed_keys) for i in keypad.values()]
        messages = []
        buzz = (0, 2000)
        
        pressed = []
        for key, value in keypad.items():
            if value.pressed:
                pressed.append(key)
        
        if pressed:
            new, old, done, back = convert(menu[option] + pressed[0])
            menu[option] = old
            
            #print(menu, option, done, back)
            
            if option == 0:
                if done:
                    option += 1
            
            elif option == 1:
                if done:
                    option += 1
                
                if back:
                    option -= 1
            
        if option == 2:
            receiver = convert(menu[0])[0]
            text = convert(menu[1])[0]
            
            messages.append(AppMessageOut(receiver, text, 1))
            
            Sending.send()
            menu = ["", ""]
            option = 0
            
            print(f"Sent {text} to {receiver}")
        
        fb.fill(TFT.BLACK)
        fb.text("Messenger", 64 - 4*len("Messenger"), 20, TFT.WHITE)
        fb.text(options[option], 64 - 4*len(options[option]), 30, TFT.WHITE)
        fb.text(convert(menu[option])[0], 64 - 4*len(convert(menu[option])[0]), 40, TFT.WHITE)
        
        if Sending.sent():
            fb.fill_rect(0, 30, 128, 128, TFT.BLACK)
            fb.text("Sent!", 64 - 4*len("Sent!"), 30, TFT.WHITE)
        
        return AppReturn(fb, messages, buzz)
    
    def end():
        pass


def get_class():
    return Messenger






