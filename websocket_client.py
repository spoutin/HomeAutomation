from ws4py.client.threadedclient import WebSocketClient


class Client(WebSocketClient):

    def setup(self, message_broker):
        self.message_broker = message_broker
        self.connect()

    def opened(self):
        print("Connected to WebSocket")
        self.message_broker.pi_clients.append(self)

    def closed(self, code, reason=None):
        print("Connect to WebSocket has been lost, trying to reconnect")

    def received_message(self, m):
        # Check message broker for any objects that match the message
        self.message_broker.check_units(m)
