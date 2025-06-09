import network
import socket
import time
from machine import Pin

# Wi-Fi credentials
SSID = '🍑'
PASSWORD = 'miaomiao69?'

# open door delay (in seconds)
openDelay = 2

# Relay control pin (confirmed GPIO3 on your board)
relay = Pin(3, Pin.OUT)
relay.off()  # Ensure off on boot

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            pass
    print('Connected! Network config:', wlan.ifconfig())

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

        if 'GET /open' in request:
            relay.on()  # If your relay is active-low, change this to relay.off()
            time.sleep(openDelay)
            relay.off()
            response = 'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nRelay activated for 1 second'

        else:
            response = 'HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nEndpoint not found'

        cl.send(response)
        cl.close()

# Main
connect_wifi()
start_server()
