from main_radio_class import *
from framebuf import FrameBuffer, RGB565
from ST7735 import TFT
import json

keypad = {i: KeypadButton(i) for i in "123456789*0#"}

class test:
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
        [i.update(buttons.pressed_keys) for i in keypad.values()]
        pk = buttons.pressed_keys
        fb.fill(TFT.BLACK)
        fb.text("Messenger", 64 - 4*, 20, TFT.WHITE)
        messages = []
        
        return AppReturn(fb, messages, buzz)
    
    def end():
        pass


def get_class():
    return(test)






