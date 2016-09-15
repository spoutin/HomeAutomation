import tornado.web
import tornado.ioloop
import websocket_server
import MessageBroker
import websocket_client
import baseObject
import threading


class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render("web/index.html")

message_broker = MessageBroker.MessageBroker()

# Setup Units
message_broker.units.append(baseObject
                            .Temp('Sabrina\'s Room', "TEMP11")
                            .set_regex('\[11\] S_Temp: H:(\d+.\d+)% T:(\d+.\d+)\*C AT:(\d+.\d+)F.+')
                            .set_regex_update('update_temp11'))
message_broker.units.append(baseObject
                            .Temp('Dylan\'s Room', "TEMP12")
                            .set_regex('\[12\] S_Temp: H:(\d+.\d+)% T:(\d+.\d+)\*C AT:(\d+.\d+)F.+')
                            .set_regex_update('update_temp12'))
message_broker.units.append(baseObject
                            .Nest('Nest', 'nest_update', message_broker.ws_server_queue)
                            .set_regex_update('update_nest'))
message_broker.units.append(baseObject
                            .Garage('Garage', "GRGSTS")
                            .set_regex('\[99\] (.+?)   \[')
                            .set_regex_update('update_garage'))
message_broker.units.append(baseObject
                            .Pump('Sump Pump', "TEMP17")
                            .set_regex('\[17\] SUMP_LVL:(\d+)   \[')
                            .set_regex_update('update_pump'))
message_broker.units.append(baseObject.Switch("Christmas Light", "", message_broker=message_broker))
message_broker.units.append(baseObject.Switch("Modem", "", message_broker=message_broker))

# Setup websocket to RaspberryPi
wsc = websocket_client.Client('ws://10.0.0.25:8080/ws')
t = threading.Thread(name='Websocket Client', target=wsc.setup, kwargs={'message_broker': message_broker})
t.start()


app = tornado.web.Application([
    (r'^/?([^/]*)$', websocket_server.MyStaticFileHandler, {"path": r"web/", "default_filename": "index.html"}),
    (r'/static/(.*)', websocket_server.MyStaticFileHandler, {'path': r"web/static/"}),
    (r"/websocket/?", websocket_server.WebSocketHandler, {"message_broker": message_broker}),
    (r"/api/v1/units/?$", websocket_server.RestAPI, {"message_broker": message_broker}),
    (r"/api/v1/units/(\d{1,3})/?$", websocket_server.RestAPI, {"message_broker": message_broker}),
    (r"/api/v1/units/(\d{1,3})/([a-zA-Z0-9_]+)/?$", websocket_server.RestAPI, {"message_broker": message_broker}),
    ])
app.listen(8888)
tornado.ioloop.IOLoop.current().start()
