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

    def setup(self, message_broker, timeout=15):
        try:
            self.__init__(self.url)
            self.message_broker = message_broker
            self.connect()
            self.run_forever()
        except KeyboardInterrupt:
            self.close()
        except:
            # print("Timing out for %i seconds. . ." % timeout)
            time.sleep(timeout)
            # print("Attempting reconnect. . .")
            self.setup(self.message_broker)

    def closed(self, code, reason=None):
        print("Websocket Client Connection Lost: ", code, reason)
        self.message_broker.pi_clients.remove(self)
        # Update frontend with loss of connectivity
        self.message_broker.check_and_update_ws_client()
        # print("Timing out for a bit. . .")
        time.sleep(3)
        # print("Reconnecting. . .")
        try:
            self.sock.close()
        except AttributeError:
            # socket already closed
            pass
        self.setup(self.message_broker)

    def opened(self):
        pingthread = PingThread(self, frequency=30)
        pingthread.start()
        print("Connected to WebSocket")
        self.message_broker.pi_clients.append(self)
        # update front with connectivity
        self.message_broker.check_and_update_ws_client()

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

            except (socket.error,RuntimeError):
                self.websocket.server_terminated = True
                self.websocket.close_connection()
                break