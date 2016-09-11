from ws4py.client.threadedclient import WebSocketClient
from ws4py.messaging import PingControlMessage
import threading
import time
import socket


class Client(WebSocketClient):
    lock = threading.Lock()

    def __init__(self, url):
        super().__init__(url)
        self.message_broker = None
        self.ping_attempts = 0

    def setup(self, message_broker):
        self.message_broker = message_broker
        self.connect()

    def opened(self):
        pingthread = PingThread(self, frequency=30)
        pingthread.start()
        print("Connected to WebSocket")
        self.message_broker.pi_clients.append(self)
        # Start heartbeat

    def closed(self, code, reason=None):
        print("Connect to WebSocket has been lost, trying to reconnect")

    def received_message(self, m):
        # Check message broker for any objects that match the message
        self.message_broker.check_units(m)

    def ponged(self, pong):
        # Reset the ping attempts
        Client.lock.acquire()
        self.ping_attempts = 0
        Client.lock.release()


class PingThread(threading.Thread):

    def __init__(self, websocket, frequency=2.0):
        threading.Thread.__init__(self)
        self.websocket = websocket
        self.frequency = frequency
        self.go = False

    def run(self):
        self.go = True
        while self.go:
            time.sleep(self.frequency)
            if self.websocket.terminated:
                break
            try:
                self.websocket.send(PingControlMessage(data='beep'))

                # Track the number of ping attempts
                Client.lock.acquire()
                self.websocket.ping_attempts += 1
                Client.lock.release()

            except socket.error:
                print("Heartbeat failed for WS Client")
                self.websocket.server_terminated = True
                self.websocket.close_connection()
                time.sleep(30)
                print('Attempting to Reconnect to WS Client')
                self.websocket.connect()
