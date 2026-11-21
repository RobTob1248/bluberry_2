import os
import json
import sys
import time
from main_radio_class import *
import urequests as urq
import json
from network import WLAN
import random

from ST7735 import TFT, TFTColor
from framebuf import FrameBuffer, RGB565
from sx1262 import SX1262
from machine import I2C, Pin, SPI, PWM, ADC, RTC, deepsleep
import mcp23017
import mcp_matrixkeypad
import esp32

#battery init
adc = ADC(Pin(1))
adc.width(ADC.WIDTH_12BIT)
adc.atten(ADC.ATTN_11DB)

def bat_volt():
    return (adc.read() / 4095.0) * 6.6

bat_level = min(round(round((((bat_volt()-3.2)/(4.0 - 3.2))*100)/5)*5), 100)

if bat_level <= 20:
    sleep()

#screen init
lit = Pin(12, Pin.OUT)
lit.value(1)

spi = SPI(1, baudrate=20000000, polarity=0, phase=0, sck=Pin(40), mosi=Pin(39), miso=Pin(41))
tft = TFT(spi,43,38,44)
tft.rotation(2)
tft.initr()
tft.rgb(True)
tft.fill(TFT.BLACK)
tft._setwindowloc((0,0),(127,159))
buf = bytearray(128*160*2)
fb = FrameBuffer(buf, 128, 160, RGB565)

#radio init
sx = SX1262(spi_bus=2, clk=5, mosi=6, miso=3, cs=7, irq=33, rst=8, gpio=34)
sx.begin(freq=915, bw=500.0, sf=12, cr=8, syncWord=0x12,
         power=20, currentLimit=60.0, preambleLength=8,
         implicit=False, implicitLen=0xFF,
         crcOn=True, txIq=False, rxIq=False,
         tcxoVoltage=1.7, useRegulatorLDO=False, blocking=True)

#gpio extender init
i2c = I2C(scl = Pin(48), sda = Pin(16))
mcp = mcp23017.MCP23017(i2c, 0x20)

#keypad init
rows = (5, 6, 7, 15)
cols = (2, 3, 4)
keys = (
    ("1", "2", "3"),
    ("4", "5", "6"),
    ("7", "8", "9"),
    ("*", "0", "#")
    )
keypad = mcp_matrixkeypad.Matrix_Keypad(mcp, rows, cols, keys)

new_keys = []
for i in keys:
    new_keys.extend(i)

fancy_keys = [KeypadButton(keypad, i) for i in new_keys]

#buttons init
buttons = [mcp[i] for i in range(9, 15)]
switches = {"wifi": mcp[0], "buzz": mcp[1], "notif": mcp[8]}
for i in [0, 1, 8, 9, 10, 11, 12, 13, 14]:
    mcp[i].input(pull=1)

specials = {"power": Pin(15, Pin.IN), "home": Pin(36, Pin.IN, Pin.PULL_UP), "shift": Pin(47, Pin.IN, Pin.PULL_UP)}

#buzzer init
buzzer = PWM(Pin(35), freq = 100, duty_u16 = 0)

#rtc init
rtc = RTC()

# wifi init
wlan = WLAN(WLAN.IF_STA) 
if switches["wifi"].value() == 0:
    wlan.active(True)
    wlan.config(pm=wlan.PM_NONE)
else:
    wlan.active(False)

#app init
sys.path.append("/apps")
app_names = []
apps = []
with open("app_list.json", "r") as app_list:
    app_names = json.loads(app_list.read())
for i in app_names:
    app_name = i + "_" + "main"
    app = __import__("/apps/" + app_name, [""])
    apps.append(app.get_class())
    
with open("/apps/settings_id.txt", "r") as file:
    DEVICE_ID = file.read()

APP_ORIGIN_CORDS = [(9, 18), (48, 18), (87, 18),
                    (9, 56), (48, 56), (87, 56),
                    (9, 94), (48, 94), (87, 94),
                             (48, 132)]

RICK_MODE = False
MSG_DIRECT = "0"
MSG_INTERNET = "1"
MSG_PING = "2"
MSG_CONFIRM = "3"

message_out_queue = []
message_in_queue = {i.name: [] for i in apps}
notif_queue = []
pings = {}

current_app = None
start_time = time.ticks_ms()

def connect_wifi():
    if not wlan.isconnected():
        with open("/apps/settings_passwords.json", "r") as file:
            passwords = json.loads(file.read())
        
        avail_networks = set([i[0].decode() for i in wlan.scan()])
        print("Availibe WiFi Networks:", avail_networks)

        for i in avail_networks:
            if i in passwords.keys():
                print("Connecting to:", i)
                wlan.connect(i, passwords[i])
                while not wlan.isconnected():
                    pass
                print("Connected to:", i)
                break
    
    return wlan.isconnected()

try:
    if switches["wifi"].value() == 0:
        connect_wifi()
except:
    pass

def new_time():
    try:
        if wlan.isconnected():
            with open("main_aio_key.txt", "r") as file:
                key = file.read()
            
            response = urq.get("https://io.adafruit.com/api/v2/Robert22G/integrations/time/struct", headers = {"tz": "America/New_York", "X-AIO-KEY": key})
            tim = json.loads(response.text)

            rtc.init((tim["year"], tim["mon"], tim["mday"], tim["hour"], tim["min"], tim["sec"], 0, 0))
    except:
        pass

new_time()

def wifi_symbol(color):
    fb = FrameBuffer(bytearray(7*7*2), 7, 7, RGB565)
    fb.pixel(3, 6, color)
    fb.line(2, 4, 4, 4, color)
    fb.line(2, 1, 4, 1, color)
    fb.pixel(1, 5, color)
    fb.pixel(5, 5, color)
    fb.pixel(0, 3, color)
    fb.pixel(1, 2, color)
    fb.pixel(5, 2, color)
    fb.pixel(6, 3, color)
    
    return(fb)
    
def color(r, g, b):
    return(TFTColor(b, r, g))

def top_bar():
    fb = FrameBuffer(bytearray(128*10*2), 128, 10, RGB565)
    time_list = list(rtc.datetime())
    time_list.pop(3)
    if len(str(time_list[3])) == 1: time_list[3] = "0" + str(time_list[3])
    if len(str(time_list[4])) == 1: time_list[4] = "0" + str(time_list[4])
    time_str = str(time_list[3]) + ":" + str(time_list[4])
    fb.text(time_str, 1, 1, TFT.WHITE)

    bat_level = min(round(round((((bat_volt()-3.2)/(4.0 - 3.2))*100)/5)*5), 100)
    
    fb.text(str(bat_level) + "%", 95, 1, TFT.WHITE)

    if wlan.isconnected(): color = TFT.BLUE
    else: color = TFT.GREEN
    
    fb.blit(wifi_symbol(color), 80, 1)
    
    return fb

def notif_bar(app, text):
    fb = FrameBuffer(bytearray(128*150*2), 128, 150, RGB565)
    
    app += ":"
    
    app_length = len(app)*8    
    fb.text(app, round(64-(app_length/2)), 1, TFT.WHITE)
    
    origin_cord = 11
    
    while len(text) > 14:
        text_length = len(text[:14])*8    
        fb.text(text[:14], round(64-(text_length/2)), origin_cord, TFT.WHITE)
        
        text = text[14:]
        origin_cord += 10
    
    
    text_length = len(text)*8    
    fb.text(text, round(64-(text_length/2)), origin_cord, TFT.WHITE)
    
    return fb

def cb(events):
    try:
        tim = Time(rtc.datetime())
        
        if events & SX1262.RX_DONE:
            msg, err = sx.recv()
            print(msg)
            message_in = bytes_message(msg)
            
            pings[message_in.sender] = message_in.connected
            
            if message_in.receiver in [DEVICE_ID, "00"]:
                if message_in.kind == MSG_DIRECT:
                    message_out = Message(DEVICE_ID, MSG_CONFIRM, message_in.sender, "", wlan.isconnected() and RICK_MODE, "00", tim.tup(), message_in.ident, "")
                    sx.send(message_bytes(message_out))
                    
                    message_in_queue[message_in.app].append(AppMessageIn(message_in.sender, message_in.text, message_in.tim))
                elif message_in.kind == MSG_INTERNET:
                    pass
                elif message_in.kind == MSG_PING:
                    message_out = Message(DEVICE_ID, MSG_CONFIRM, message_in.sender, "", wlan.isconnected() and RICK_MODE, "00", tim.tup(), message_in.ident, "")
                    sx.send(message_bytes(message_out))
                elif message_in.kind == MSG_CONFIRM:
                    for i in message_out_queue:
                        if message.ident == i.ident:
                            message_out_queue.remove(i)
                            break
    except:
        pass
sx.setBlockingCallback(False, cb)

def rand_id():
    return "".join([chr(random.randint(32, 127)) for _ in range(8)])

def info(text):
    notif_queue.append(["System", str(text)])

def sleep():
    if current_app is not None: current_app.end()
    print("going to sleep")
    lit.off()
    spi.deinit()
    i2c.deinit()
    sx.sleep(retainConfig=False)
    if wlan.active():
        wlan.disconnect()
        wlan.active(False)
    esp32.wake_on_ext0(pin = specials["power"], level = esp32.WAKEUP_ANY_HIGH)
    time.sleep(1)
    
    deepsleep()
    

print("Initializaation complete")

def front_end():
#     try:
    global current_app
    global fb
    
    tim = Time(rtc.datetime())
    
    fb.fill(TFT.BLACK)
    
    notifed = False
    
    #notif loop
    
    for i in apps:
        messages = message_in_queue[i.name]
        message_in_queue[i.name] = []
        notifs = i.notif(messages, tim)
        
        for notif in notifs:
            notif_queue.append([i.name, notif])
        
        if notifs != []: notifed = True
    
    if notifed and switches["buzz"].value() == 0:
        for i in range(2):
            buzzer.duty_u16(30000)
            time.sleep(.25)
            buzzer.duty_u16(0)
            time.sleep(.25)
        
    #show notifs
    
    if notif_queue != [] and switches["notif"].value() == 0:
        
        fb.blit(notif_bar(notif_queue[0][0], notif_queue[0][1]), 0, 10)
        
        pk = {i.key: i.update() for i in fancy_keys}
        
        if pk["*"]:
            notif_queue.append(notif_queue.pop(0))
        
        elif pk["#"]:
            notif_queue.pop(0)
    
    #home screen
    
    elif current_app == None:
        
        for index, value in enumerate(apps):
            fb.blit(value.icon, APP_ORIGIN_CORDS[index][0], APP_ORIGIN_CORDS[index][1])
        
        pk = {i.key: i.update() for i in fancy_keys}
        
        for key, value in pk.items():
            if key not in ["*", "#"]:
                if int(key) <= len(apps) and value == True:
                    current_app = apps[int(key)-1]
                    current_app.begin()
                    break
    
    #in-app              
    
    else:
        main_response = current_app.main(AppButtons([keypad.pressed_keys, buttons, specials["shift"]]), fb, tim)
        fb = main_response.fb
        
        messages = main_response.messages
        
        for i in messages:
            if i.kind == 0:
                message = Message(DEVICE_ID, MSG_DIRECT, i.receiver, i.text, wlan.isconnected() and RICK_MODE, "00", tim.tup(), rand_id(), current_app.name)
                sx.send(message_bytes(message))
            else:
                message_out_queue.append(SecondaryMessage(i.receiver, i.text, tim.tup(), rand_id(), current_app.name))
        
        if switches["buzz"].value() == 0:
            buzz = main_response.buzz
            buzzer.freq(buzz[1])
            buzzer.duty_u16(buzz[0])
        else:
            buzzer.duty_u16(0)
        
        if specials["home"].value() == 0:
            current_app.end()
            current_app = None
            fb.fill(TFT.BLACK)
    
    fb.blit(top_bar(), 0, 0)
    tft._writedata(buf)
#     except:
#         pass

def back_end():
    #try:
    global start_time
    global pings
    
    tim = Time(rtc.datetime())
    
    if time.ticks_diff(time.ticks_ms(), start_time) >= 5000:
        start_time = time.ticks_ms()
        
        #persistent messages
    
        for i in message_out_queue:
            if i.receiver in pings:
                message = Message(DEVICE_ID, MSG_DIRECT, i.receiver, i.text, wlan.isconnected() and RICK_MODE, "00", i.tim, i.ident, i.app)
                sx.send(message_bytes(message))
            else:
                for key, value in pings.items():
                    if value == True:
                        message = Message(DEVICE_ID, MSG_INTERNET, i.receiver, i.text, wlan.isconnected() and RICK_MODE, key, i.tim, i.ident, i.app)
                        sx.send(message_bytes(message))
                        break
        
        #pings
        pings = {}
        message = Message(DEVICE_ID, MSG_PING, "00", "", wlan.isconnected() and RICK_MODE, "00", tim.tup(), rand_id(), "")
        sx.send(message_bytes(message))
#     except:
#         pass

while True:
    try:
        if specials["power"].value() == 0:
            sleep()
        
        front_end()
        back_end()
        
        if switches["wifi"].value() == 0:
            wlan.active(True)
            wlan.config(pm=wlan.PM_NONE)
            connect_wifi()
        else:
            wlan.active(False)
            
        bat_level = min(round(round((((bat_volt()-3.2)/(4.0 - 3.2))*100)/5)*5), 100)
        
        if bat_level <= 20:
            sleep()
        
        time_list = Time(rtc.datetime())
        if time_list.min % 30 == 0 and time_list.sec in [0, 1, 2]:
            new_time()
            print("Time has been calibrated")
    
    except Exception as e:
        if current_app is not None: current_app.end()
        if e is not KeyboardInterrupt:
            sys.print_exception(e)
            sleep()




