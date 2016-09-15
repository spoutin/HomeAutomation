import tornado.web
import json
import baseObject
import tornado.websocket


class MyStaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def initialize(self, message_broker):
        self.message_broker = message_broker
        self.message_broker.running = True

    def open(self, *args):
        self.message_broker.ws_server_connection.append(self)
        # Send control or monitor messages to frontend clients
        self.message_broker.check_and_update_ws_client()

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
                self.write(json.dumps(unit.__dict__, default=str))
            else:
                self.set_status(404)
                self.finish("<html><body>Unit ID {} not found</body></html>".format(unit_id))
        else:
            self.write(json.dumps(baseObject.units_to_dict_group(self.message_broker.units), default=str))

    def post(self, unit_id=None):
        if not unit_id:
            self.set_status(500)
            self.finish("<html><body>Missing Unit ID</body></html>")
            return
        unit = baseObject.get_unit(self.message_broker.units, int(unit_id))
        if unit:
            unit.request_update(self.message_broker.pi_clients)
            self.write("<html><body>Request Sent to update {}</body></html>".format(unit.name))
        else:
            self.set_status(404)
            self.finish("<html><body>Unit ID {} not found</body></html>".format(unit_id))

    def put(self, unit_id=None, action=None):
        if not unit_id:
            self.set_status(500)
            self.finish("<html><body>Missing Unit ID</body></html>")
            return
        if not action:
            self.set_status(500)
            self.finish("<html><body>Missing Action</body></html>")
            return

        unit = baseObject.get_unit(self.message_broker.units, int(unit_id))
        if not unit:
            self.set_status(404)
            self.finish("<html><body>Unknown Unit ID</body></html>")
            return

        try:
            data = json.loads(self.request.body.decode("utf-8"))
        except ValueError:
            data = ''

        unit.run_actions(function=action, data=data, pi_clients=self.message_broker.pi_clients)
        self.write("<html><body>Request Sent to {} {}</body></html>".format(action, unit.name))
