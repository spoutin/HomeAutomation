import re
import nest as nest_api
import json
import configparser

class base:

    def __init__(self, name, update_msg=None):
        self.name = name
        self.regex = None
        self.update_msg = update_msg

    def set_regex(self, pattern):
        self.regex = re.compile(pattern)
        return self

    def set_regex_update(self, pattern):
        self.regex_update = re.compile(pattern)
        return self

    def check_update(self, message):
        if not self.regex_update:
            raise ValueError("Missing Regex")
        if self.regex_update.search(str(message)):
            return True
        else:
            return False

    def check_message(self, message):
        if not self.regex:
            return False
        if self.regex.search(str(message)):
            return True
        else:
            return False

    def request_update(self, pi_clients):
        [x.send(self.update_msg) for x in pi_clients]

class temp(base):

    def __init__(self, name, update_msg):
        super().__init__(name, update_msg)
        self.temp = None
        self.humidity = None

    def decode_message(self, message):
        m = self.regex.match(str(message))
        self.temp = m.group(2)
        self.humidity = m.group(1)
        #print("%s - Temp: %s Humidity: %s" %(self.name, self.temp, self.humidity))

class nest(base):

    def __init__(self, name, update_msg, ws_queue):
        super().__init__(name, update_msg)
        try:
            config = configparser.ConfigParser()
            config.read('nest.ini')
            username = config['nest']['username']
            password = config['nest']['password']
        except KeyError:
            print("Missing Nest username or password in nest.ini file")
            raise
        self.napi = nest_api.Nest(username, password)
        self.temp = None
        self.humidity = None
        self.ws_queue = ws_queue

    def request_update(self, *args):
        try:
            self.temp = self.napi.structures[0].devices[0].temperature
            self.humidity = self.napi.structures[0].devices[0].humidity
            self.ws_queue.put(json.dumps({"nest":{"temp":round(self.temp, 1), "humidity":self.humidity}}))
        except:
            print("Error trying to get Nest information!")