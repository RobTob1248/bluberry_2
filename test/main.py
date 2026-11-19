from main_radio_class import *
from framebuf import FrameBuffer, RGB565
from ST7735 import TFT
import json

showed = False

class test:
    name = "Test"
    icon = FrameBuffer(bytearray(30*30*2), 30, 30, RGB565)
    icon.rect(0, 0, 30, 30, TFT.WHITE)
    icon.fill_rect(1, 1, 28, 28, TFT.RED)
    
    def begin():
        pass
    
    def notif(messages, time):
        notifs = []
        
        for i in messages:
            notifs.append(f"{i.sender} sent: {i.text}")
        
        return notifs
    
    def main(buttons, fb, time):
        pk = buttons.pressed_keys
        things = " ".join([str(i) for i in pk])
        fb.fill(TFT.BLACK)
        fb.text(things, 50, 50, TFT.WHITE)
        if pk != []: buzz = (30000, 200)
        else: buzz = (0, 200)
        messages = []
        
        return AppReturn(fb, messages, buzz)
    
    def end():
        pass


def get_class():
    return(test)





