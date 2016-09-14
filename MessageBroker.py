import queue
import threading
from timer import perpetualTimer


class MessageBroker:

    def __init__(self):
        self.running = False
        self.units = []
        self.ws_server_queue = queue.Queue()
        self.ws_wemo_queue = queue.Queue()
        self.ws_server_connection = []
        self.pi_clients = []

        # Setup WS Sender
        self.senderthread = self.SenderThread(self)
        self.senderthread.start()

        # Setup never ending timer
        timer = perpetualTimer(60, self.update_all)
        timer.start()

    # Run the update function on all units
    def update_all(self):
        for unit in self.units:
            unit.request_update(self.pi_clients)

    def check_update_units(self, message):
        for unit in self.units:
            if unit.check_update(str(message)):
                # request update from unit
                unit.request_update(self.pi_clients)

    def check_units(self, message):
        for unit in self.units:
            if unit.check_message(str(message)):
                msg = unit.decode_message(message, pi_clients=self.pi_clients)
                if msg:
                    self.ws_server_queue.put(str(msg), block=True, timeout=1)
                else:
                    self.ws_server_queue.put(str(message), block=True, timeout=1)

    def get_unit(self,name):
        for unit in self.units:
            if unit.name == name:
                return unit
        return

    class SenderThread(threading.Thread):

        def __init__(self, message_broker):
            super(MessageBroker.SenderThread, self).__init__()
            self.message_broker = message_broker
            self.ws_server_queue = self.message_broker.ws_server_queue
            self.stop_request = threading.Event()

        def run(self):
            while not self.stop_request.is_set():
                try:
                    msg = self.ws_server_queue.get(True, 0.05)
                    [x.write_message(str(msg)) for x in self.message_broker.ws_server_connection]
                except queue.Empty:
                    continue

        def join(self, timeout=None):
            self.stop_request.set()
            super(MessageBroker.SenderThread, self).join(timeout)
