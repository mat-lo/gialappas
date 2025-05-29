# coded by chatgpt pompt:
# https://chatgpt.com/share/6837757f-c744-800e-9667-238138b78020

# TO DO:
# assign static IP

import network
import socket
import time
from machine import Pin

# Wi-Fi credentials
SSID = '🍑'
PASSWORD = 'miaomiao69?'

# Onboard LED (GPIO10 on Xiao ESP32C3)
led = Pin(10, Pin.OUT)

# Connect to Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            pass
    print('Network config:', wlan.ifconfig())

# Start a simple web server
def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Listening on', addr)

    while True:
        cl, addr = s.accept()
        print('Client connected from', addr)
        request = cl.recv(1024)
        request = str(request)
        print('Request:', request)

        # Simple GET check for "/led"
        if 'GET /led' in request:
            led.on()
            time.sleep(1)
            led.off()
            response = 'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nLED turned on for 1 second'
        else:
            response = 'HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nEndpoint not found'

        cl.send(response)
        cl.close()

# Main
connect_wifi()
start_server()
