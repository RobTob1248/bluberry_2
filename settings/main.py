from main_radio_class import *
from framebuf import FrameBuffer, RGB565
from ST7735 import TFT
import tcp_udp
import json
import random
import requests as urq
import sys
import os

def generate_key():
    key = ""
    
    for i in range(8):
        key += str(random.randint(0, 9))
    
    return key

def parse_input(response):
    start = len("GET /?")
    end = response.find(" HTTP/1.1")
    
    parts = response[start:end].split("&")
    
    info = {}
    
    for i in parts:
        part = i.split("=")
        
        for key, value in http_chars.items():
            part[1] = part[1].replace(key, value)
            
        info[part[0]] = part[1]
    
    return info

def parse_link(response):
    start = len("GET /")
    end = response.find(" HTTP/1.1")
    
    link = response[start:end]
    
    return link

def change_file(app, file, directory = "/"):
    new_file = urq.get(f"https://raw.githubusercontent.com/RobTob1248/bluberry_2/refs/heads/main/{app}/{file}")
    
    with open(directory + app + "_" + file, "w") as file:
        file.write(new_file.text)
    
    new_file.close()

def install_app(app):
    try:
        response = urq.get(f"https://raw.githubusercontent.com/RobTob1248/bluberry_2/refs/heads/main/{app}/info.json")
        info = json.loads(response.text)
        response.close()
        
        change_file(app, "info.json", "/apps/")
        change_file(app, "main.py", "/apps/")
        
        for i in info["supp_get"]:
            change_file(app, i, "/apps/")
        
        with open("app_list.json", "r") as file:
            old_apps = json.loads(file.read())
            old_apps.append(app)
        
        with open("app_list.json", "w") as file:
            file.write(json.dumps(old_apps))
    except:
        pass
    
class AppManager:
    def get_apps():
        with open("app_list.json", "r") as file:
            return json.loads(file.read())
    
    @classmethod
    def get_apps_pretty(cls):
        old_text = json.dumps(cls.get_apps())
        for i in "[]{}()'\"":
            old_text = old_text.replace(i, "")
        
        old_text = old_text.replace(", ", "<br>")
        
        return old_text
    
    @classmethod
    def install_app(cls, app):
        try:
            if app == "settings":
                raise Exception("You can't install settings!")
            
            response = urq.get(f"https://raw.githubusercontent.com/RobTob1248/bluberry_2/refs/heads/main/{app}/info.json")
            info = json.loads(response.text)
            response.close()
            
            print("Installing info.json")
            change_file(app, "info.json", "/apps/")
            print("Installed info.json")
            
            print("Installing main.py")
            change_file(app, "main.py", "/apps/")
            print("Installed main.py")
            
            for i in info["supp_get"]:
                print(f"Installing {i}")
                change_file(app, i, "/apps/")
                print(f"Installed {i}")
    
            old_apps = cls.get_apps()
            old_apps.append(app)
            
            with open("app_list.json", "w") as file:
                file.write(json.dumps(old_apps))
            
            print(f"Successfuly installed {app}")
        except Exception as e:
            print(f"Installation of {app} failed")
            sys.print_exception(e)
    
    @classmethod
    def delete_app(cls, app):
        try:
            if app == "settings":
                raise Exception("You can't delete settings!")
            
            all_files = os.listdir("/apps/")
            app_files = []
            
            for i in all_files:
                if i[:len(app + "_")] == app + "_":
                    print(f"Deleting {i[len(app + "_"):]}")
                    os.remove("/apps/" + i)
                    print(f"Deleted {i[len(app + "_"):]}")
            
            old_apps = cls.get_apps()
            old_apps.remove(app)
            
            with open("app_list.json", "w") as file:
                file.write(json.dumps(old_apps))
            
            print(f"Successfuly deleted {app}")
        except Exception as e:
            print(f"Deletion of {app} failed")
            sys.print_exception(e)

class WifiManager:
    def get_networks():
        with open("/apps/settings_passwords.json", "r") as file:
            return json.loads(file.read())
    
    @classmethod
    def get_networks_pretty(cls):
        old_text = json.dumps(cls.get_networks())
        for i in "[]{}()'\"":
            old_text = old_text.replace(i, "")
        
        old_text = old_text.replace(", ", "<br>")
        
        return old_text
    
    @classmethod
    def set_network(cls, ssid, password):
        all_networks = cls.get_networks()
        all_networks[ssid] = password
        new = json.dumps(all_networks)
        
        with open("/apps/settings_passwords.json", "w") as file:
            file.write(new)
    
    @classmethod
    def del_network(cls, ssid):
        all_networks = cls.get_networks()
        try:
            all_networks.pop(ssid)
        except:
            pass
        new = json.dumps(all_networks)
        
        with open("/apps/settings_passwords.json", "w") as file:
            file.write(new)

class html:
    def app_html():
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Bluberry Settings</title></head>
        <body>
        <center>
            <a href="/"><h1>Bluberry Settings</h1></a>
            
            <a href="/apps"><h2>App Settings</h2></a>
            <h3>New App</h3>
                <form action="/" method="GET">
                    <input type="text" name="app_name" placeholder="Type your app name.">
                    <input type="submit" value="Send">
                </form>
                
            <br>
            
            <h3>Current Apps</h3>
                <p>{AppManager.get_apps_pretty()}</p>
            
            <br>
            
            <h3>Delete App</h3>    
                <form action="/" method="GET">
                    <input type="text" name="old_app" placeholder="Type your wifi ssid.">
                    <input type="submit" value="Send">
                </form>
        </center>
        </body>
        </html>
        """
        
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            f"Content-Length: {len(html)}\r\n"
            "Connection: close\r\n\r\n"
            + html
            )
        
        return response
    
    def wifi_html():
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Bluberry Settings</title></head>
        <body>
        <center>
            <a href="/"><h1>Bluberry Settings</h1></a>
            
            <a href="/wifi"><h2>Wifi Settings</h2></a>
            
            <h3>New Network</h3>
                <form action="/" method="GET">
                    <input type="text" name="wifi_ssid" placeholder="Type your wifi ssid.">
                    <input type="text" name="wifi_pass" placeholder="Type your wifi password.">
                    <input type="submit" value="Send">
                </form>
                
            <br>
            
            <h3>All Networks</h3>
                <p>{WifiManager.get_networks_pretty()}</p>
            
            <br>
            
            <h3>Delete Network</h3>    
                <form action="/" method="GET">
                    <input type="text" name="old_ssid" placeholder="Type your wifi ssid.">
                    <input type="submit" value="Send">
                </form>
        </center>
        </body>
        </html>
        """
        
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            f"Content-Length: {len(html)}\r\n"
            "Connection: close\r\n\r\n"
            + html
            )
        
        return response
    
    def home_html():
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Bluberry Settings</title></head>
        <body>
        <center>
            <a href="/"><h1>Bluberry Settings</h1></a>
            
            <a href="/wifi"><h2>Wifi Settings</h2></a>
            
            <a href="/apps"><h2>App Settings</h2></a>
        </center>
        </body>
        </html>
        """
        
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            f"Content-Length: {len(html)}\r\n"
            "Connection: close\r\n\r\n"
            + html
            )
        
        return response
    
    def not_found_html():
        response = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
        
        return response

wifi_info = {"wifi_ssid": "", "wifi_pass": ""}

http_chars = {
    "%3A": ":",
    "%2F": "/",
    "%3F": "?",
    "%23": "#",
    "%5B": "[",
    "%5D": "]",
    "%40": "@",
    "%21": "!",
    "%24": "$",
    "%26": "&",
    "%27": "'",
    "%28": "(",
    "%29": ")",
    "%2A": "*",
    "%2B": "+",
    "%2C": ",",
    "%3B": ";",
    "%3D": "=",
    "+": " ",
    "%22": '"',
    "%25": "%",
    "%3C": "<",
    "%3E": ">",
    "%5C": "\\",
    "%5E": "^",
    "%60": "`",
    "%7B": "{",
    "%7C": "|",
    "%7D": "}",
    "%7E": "~",
}


class Settings:
    name = "Settings"
    icon = FrameBuffer(bytearray(30*30*2), 30, 30, RGB565)
    icon.rect(0, 0, 30, 30, TFT.WHITE)
    icon.fill_rect(1, 1, 28, 28, color(0, 255, 0))
    
    @classmethod
    def begin(cls):
        with open("/apps/settings_id.txt", "r") as file:
            cls.DEVICE_ID = file.read()
        
        cls.ssid = f"blueberry_{cls.DEVICE_ID}"
        cls.password = generate_key()
        cls.s = tcp_udp.TCPServer(cls.ssid, cls.password, False, 80, .01)
    
    def notif(messages, time):
        notifs = []
        return notifs
    
    @classmethod
    def main(cls, buttons, fb, time):
        fb.fill(TFT.BLACK)
        buzz = (0, 2000)
        messages = []
        
        fb.text("Settings", 64 - 4*len("Settings"), 20, TFT.WHITE)
        fb.text("Wifi SSID:", 64 - 4*len("Wifi SSID:"), 30, TFT.WHITE)
        fb.text(cls.ssid, 64 - 4*len(cls.ssid), 40, TFT.WHITE)
        fb.text("Wifi Password:", 64 - 4*len("Wifi Password:"), 50, TFT.WHITE)
        fb.text(cls.password, 64 - 4*len(cls.password), 60, TFT.WHITE)
        fb.text("Connect to:", 64 - 4*len("Connect to:"), 70, TFT.WHITE)
        fb.text(cls.s.addr[0], 64 - 4*len(cls.s.addr[0]), 80, TFT.WHITE)
        
        client = cls.s.accept()
        
        if client is not None:
            try:
                response = cls.s.recv()
                
                print("Client connected from", client[0])
                
                if response is not None:
                    if "GET /?" in response:
                        info = parse_input(response)
                        print(info)
                        
                        if "wifi_ssid" in info.keys():
                            WifiManager.set_network(info["wifi_ssid"], info["wifi_pass"])
                            cls.s.sendall(html.wifi_html())
                        
                        if "old_ssid" in info.keys():
                            WifiManager.del_network(info["old_ssid"])
                            cls.s.sendall(html.wifi_html())
                        
                        if "app_name" in info.keys():
                            AppManager.install_app(info["app_name"])
                            cls.s.sendall(html.app_html())
                        
                        if "old_app" in info.keys():
                            AppManager.delete_app(info["old_app"])
                            cls.s.sendall(html.app_html())
                    
                    elif "GET /favicon.ico" in response:
                        with open("favicon.ico", "rb") as f:
                            icon_data = f.read()
                        
                        cls.s.send("HTTP/1.1 200 OK\r\n")
                        cls.s.send("Content-Type: image/x-icon\r\n")
                        cls.s.send(f"Content-Length: {len(icon_data)}\r\n")
                        cls.s.send("Connection: close\r\n\r\n")
                        cls.s.sendall(icon_data, True)
                    
                    else:
                        link = parse_link(response)
                        print(link)
                        
                        if link == "":
                            cls.s.sendall(html.home_html())
                        
                        elif link == "wifi":
                            cls.s.sendall(html.wifi_html())
                        
                        elif link == "apps":
                            cls.s.sendall(html.app_html())
                
#                 else:
#                     cls.s.sendall(html.home_html())
            
            finally:
                cls.s.close()
        
        return AppReturn(fb, messages, buzz)
    
    @classmethod
    def end(cls):
        cls.s.wlan.active(False)
        cls.s.end()


def get_class():
    return(Settings)
