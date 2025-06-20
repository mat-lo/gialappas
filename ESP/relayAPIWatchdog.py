# --- Final ESP32 Code for Robust Door Relay Control ---

import network
import socket
import time
import utime      # For uptime
import gc         # For garbage collection / memory info
import json       # To create a JSON response
from machine import Pin, WDT

# --- Configuration ---
# Fill these in with your details
SSID = 'casa gulli'
PASSWORD = 'welcometocasagulli2025'

# Relay control pin (GPIO3 on your board)
RELAY_PIN = 3

# How long to keep the door relay active (in seconds)
OPEN_DOOR_DELAY = 2
# --- End of Configuration ---

# --- Global Objects ---
# Hardware setup
relay = Pin(RELAY_PIN, Pin.OUT)
relay.off()  # Ensure relay is off on boot

# Start a watchdog timer. If the code freezes for more than 8 seconds,
# the ESP32 will automatically restart. This is a great safety net.
wdt = WDT(timeout=8000)

# Keep track of when the script starts for uptime calculation
start_time = utime.ticks_ms()

# Global WLAN object to access its status anywhere
wlan = network.WLAN(network.STA_IF)


def connect_wifi():
    """Activates the Wi-Fi interface and connects to the network."""
    global wlan
    print('Connecting to Wi-Fi...')
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    # Wait for connection
    max_wait = 15
    while max_wait > 0:
        if wlan.isconnected():
            break
        max_wait -= 1
        print('.', end='')
        time.sleep(1)

    if wlan.isconnected():
        print('\nConnected! Network config:', wlan.ifconfig())
    else:
        print('\nFailed to connect to Wi-Fi.')

def start_server():
    """Starts the web server to listen for commands."""
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    # This allows the port to be reused immediately after a crash/reboot
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print('Listening on', addr)

    while True:
        wdt.feed() # "Pet" the watchdog to prevent a reboot

        # --- Robustness Check 1: Wi-Fi Connection ---
        if not wlan.isconnected():
            print("Wi-Fi disconnected. Attempting to reconnect...")
            connect_wifi()
            time.sleep(5) # Wait a moment before continuing
            continue

        try:
            # Set a timeout on the listening socket.
            # This allows the loop to run and feed the watchdog periodically.
            s.settimeout(5.0)
            cl, addr = s.accept()
            s.settimeout(None) # Disable timeout for the active connection

            print('Client connected from', addr)
            request_bytes = cl.recv(1024)
            request = str(request_bytes)
            print('Request:', request)

            response = ''
            
            # --- Routing Logic ---
            if 'GET /open' in request:
                print('Activating relay...')
                relay.on()
                time.sleep(OPEN_DOOR_DELAY)
                relay.off()
                print('Relay deactivated.')
                response = 'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nSuccess: Relay activated.'
            
            elif 'GET /status' in request:
                gc.collect() # Clean up memory before checking
                uptime_seconds = utime.ticks_diff(utime.ticks_ms(), start_time) // 1000
                
                status_data = {
                    "status": "ok",
                    "uptime_seconds": uptime_seconds,
                    "free_memory_bytes": gc.mem_free(),
                    "wifi_rssi_dbm": wlan.status('rssi')
                }
                
                response_body = json.dumps(status_data)
                response = 'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n' + response_body

            else:
                response = 'HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nError: Endpoint not found. Use /open or /status'

            cl.sendall(response)
            cl.close()

        # --- Robustness Check 2: Error Handling ---
        except OSError as e:
            # ETIMEDOUT (110) is expected when no one connects for 5 seconds
            if e.args[0] != 110:
                print(f"A socket error occurred: {e}")
                if 'cl' in locals():
                    cl.close()
        except Exception as e:
            print(f"A critical error occurred: {e}")

# --- Main Execution ---
connect_wifi()
start_server()