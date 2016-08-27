import re
import nest as nest_api
import requests.exceptions
import json
import configparser
import itertools


# Input is the list of units
# Output is the list of units as dictionaries
def units_to_dict(units):
    unit_dict = []
    for unit in units:
        unit_dict.append(unit.__dict__)
    return unit_dict


def get_unit(units, unit_id):
    for unit in units:
        if unit.id == unit_id:
            return unit
    return


class Base(object):
    _create_id = itertools.count(0)

    def __init__(self, name, update_msg=None):
        self.name = name
        self.regex = None
        self.regex_update = None
        self.update_msg = update_msg
        self.id = self._create_id.__next__()
        # Default Actions
        self.actions = ["request_update"]

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

    def request_update(self, pi_clients, **kwargs):
        self.send_to_pi(pi_clients, self.update_msg)

    def run_actions(self, function, **kwargs):
        if function in self.actions:
            getattr(self, function)(**kwargs)
        else:
            raise ValueError("Request unknown or not allowed {}".format(function))

    @staticmethod
    def send_to_pi(pi_clients, message):
        [x.send(str(message)) for x in pi_clients]


class Temp(Base):

    def __init__(self, name, update_msg):
        super().__init__(name, update_msg)
        self.temp = None
        self.humidity = None

    def decode_message(self, message):
        m = self.regex.match(str(message))
        self.temp = m.group(2)
        self.humidity = m.group(1)
        # print("%s - Temp: %s Humidity: %s" %(self.name, self.temp, self.humidity))


class Nest(Base):

    def __init__(self, name, update_msg, ws_queue):
        super().__init__(name, update_msg)
        try:
            config = configparser.ConfigParser()
            config.read('config/nest.ini')
            username = config['nest']['username']
            password = config['nest']['password']
        except KeyError:
            print("Missing Nest username or password in nest.ini file")
            raise
        self.napi = nest_api.Nest(username, password, access_token_cache_file='./cache/auth_cache')
        self.temp = None
        self.humidity = None
        self.ac_state = None
        self.heater_state = None
        self.target = None
        self.away = None
        self.ws_queue = ws_queue
        self.actions.append("update_temp")

    def update_temp(self, value, **kwargs):
        self.napi.structures[0].devices[0].temperature = int(value)

    def request_update(self, *args, **kwargs):
        try:
            self._request_update()
        except requests.exceptions.HTTPError:
            print("Error getting Nest information!")

    def _request_update(self):
        self.temp = self.napi.structures[0].devices[0].temperature
        self.humidity = self.napi.structures[0].devices[0].humidity
        self.target = self.napi.structures[0].devices[0].target
        self.away = self.napi.structures[0].away
        self.ac_state = self.napi.structures[0].devices[0].hvac_ac_state
        self.heater_state = self.napi.structures[0].devices[0].hvac_heater_state
        self.ws_queue.put(json.dumps({"nest": {"temp": round(self.temp, 1),
                                               "humidity": self.humidity,
                                               "ac_state": self.ac_state,
                                               "heater_state": self.heater_state,
                                               "target": round(self.target, 1),
                                               "away": self.away
                                               }
                                      }))


class Garage(Base):

    def __init__(self, name, update_msg):
        super().__init__(name, update_msg)
        self.status = None
        # additional actions
        self.actions.append("toggle")

    def decode_message(self, message):
        m = self.regex.match(str(message))
        self.status = m.group(1)

    def toggle(self, state, pi_clients):
        if state == "open":
            self.send_to_pi(pi_clients, "GRGOPN")
        elif state == "close":
            self.send_to_pi(pi_clients, "GRGCLS")


class Pump(Base):

    def __init__(self, name, update_msg):
        super().__init__(name, update_msg)
        self.level = None

    def decode_message(self, message):
        m = self.regex.match(str(message))
        self.level = m.group(1)
