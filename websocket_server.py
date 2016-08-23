import tornado.websocket

class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def initialize(self, message_broker):
        self.message_broker = message_broker
        self.message_broker.running = True

    def open(self, *args):
        self.message_broker.ws_server_connection.append(self)

    def on_close(self):
        self.message_broker.ws_server_connection.remove(self)

    def on_message(self, message):
        self.message_broker.check_update_units(message)

    def check_origin(self, origin):
        return True

