from ouimeaux.environment import Environment
from ouimeaux.signals import receiver, statechange, devicefound
from ouimeaux.environment import UnknownDevice
import threading
import json
import queue


class WeMoThread(threading.Thread):

    def __init__(self, message_broker):
        self.message_broker = message_broker
        self.env = Environment()
        threading.Thread.__init__(self)

    def run(self):
        self.mainloop()

    def toggle(self, name):
        try:
            item = self.env.get_switch(name=name)
            return item.toggle()
        except UnknownDevice:
            print("Error - Failed to find device {}".format(name))
            return

    def get_state(self, name):
        try:
            item = self.env.get_switch(name=name)
            return item.get_state()
        except UnknownDevice:
            print("Error - Failed to find device {}".format(name))
            return

    def mainloop(self):

        @receiver(devicefound)
        def handler(sender, **kwargs):
            print("Found device", sender)

        @receiver(statechange)
        def motion(sender, **kwargs):
            state = "on" if kwargs.get('state') else "off"
            self.message_broker.get_unit(sender.name).request_update()

        self.env.start()
        self.env.discover(10)
        self.env.wait()  # Pass control to the event loop