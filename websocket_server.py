import tornado.websocket
import json
import baseObject


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


class RestAPI(tornado.web.RequestHandler):

    def initialize(self, message_broker):
        self.message_broker = message_broker

    def get(self, unit_id=None):
        if unit_id:
            unit = baseObject.get_unit(self.message_broker.units, int(unit_id))
            if unit:
                self.write("Unit: " + json.dumps(unit.__dict__, default=str))
            else:
                self.set_status(404)
                self.finish("<html><body>Unit ID {} not found</body></html>".format(unit_id))
        else:
            self.write("All Units:" + json.dumps(baseObject.units_to_dict(self.message_broker.units), default=str))

    def post(self, unit_id=None):
        unit = baseObject.get_unit(self.message_broker.units, int(unit_id))
        if unit:
            unit.request_update(self.message_broker.pi_clients)
            self.write("<html><body>Request Sent to update {}</body></html>".format(unit.name))
        else:
            self.set_status(404)
            self.finish("<html><body>Unit ID {} not found</body></html>".format(unit_id))
