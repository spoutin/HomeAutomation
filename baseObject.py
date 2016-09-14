import re
import nest as nest_api
import requests.exceptions
import json
import configparser
import itertools
import wemo
import collections


# Input is the list of units
# Output is the list of units as dictionaries
def units_to_dict(units):
    unit_dict = []
    for unit in units:
        unit_dict.append(unit.__dict__)
    return unit_dict


def units_to_dict_group(units):
    unit_dict = {}
    for unit in units:
        if unit.type not in unit_dict:
            unit_dict[unit.type] = []
        unit_dict[unit.type].append(unit.__dict__)
    return collections.OrderedDict(sorted(unit_dict.items()))


def get_unit(units, unit_id):
    for unit in units:
        if unit.id == unit_id:
            return unit
    return


class Base(object):
    _create_id = itertools.count(0)
    env = None

    def __init__(self, name, update_msg=None):
        self.name = name
        self.clean_name = re.sub('[^A-Za-z0-9]+', '', self.name).lower()
        self.type = "Base"
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
            return False
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
        try:
            [x.send(str(message)) for x in pi_clients]
        except (AttributeError, RuntimeError, OSError):
            pass


class Temp(Base):

    def __init__(self, name, update_msg):
        super().__init__(name, update_msg)
        self.type = "Temperature"
        self.temp = None
        self.humidity = None

    def decode_message(self, message, **kwargs):
        m = self.regex.match(str(message))
        self.temp = m.group(2)
        self.humidity = m.group(1)
        return json.dumps({'unit_update': self.__dict__}, default=str)


class Nest(Base):

    def __init__(self, name, update_msg, ws_queue):
        super().__init__(name, update_msg)
        self.type = "Nest"
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
        self.actions.append("update_temperature")
        self.actions.append("toggle_away")

    def toggle_away(self, **kwargs):
        self.napi.structures[0].away = not self.away
        return not self.away

    def update_temperature(self, data, **kwargs):
        if not data:
            raise ValueError("Missing temperature value in json body")
        self.napi.structures[0].devices[0].temperature = data['temperature']

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
        self.ac_state = self.napi.structures[0].devices[0].hvac_ac_state
        self.mode = self.napi.structures[0].devices[0].mode
        self.fan = self.napi.structures[0].devices[0].fan
        self.ws_queue.put(json.dumps({'unit_update': self.__dict__}, default=str))


class Garage(Base):

    def __init__(self, name, update_msg):
        super().__init__(name, update_msg)
        self.type = "Garage"
        self.status = ""
        # additional actions
        self.actions.append("toggle")

    def decode_message(self, message, pi_clients, **kwargs):
        m = self.regex.match(str(message))
        self.status = m.group(1)
        # Send message to LED process
        self.update_led(pi_clients)
        return json.dumps({'unit_update': self.__dict__}, default=str)

    def update_led(self, pi_clients):
        if self.status.lower() == 'open':
            msg = {'led': 'red'}
        elif self.status.lower() == 'closed':
            msg = {'led': 'off'}
        else:
            msg = {'led': 'blue'}
        self.send_to_pi(pi_clients, json.dumps(msg, str))

    def toggle(self, pi_clients, **kwargs):
        if self.status.lower() == "closed":
            self.send_to_pi(pi_clients, "GRGOPN")
        elif self.status.lower() == "open":
            self.send_to_pi(pi_clients, "GRGCLS")
        else:
            raise ValueError("Unknown status: {}".format(self.status))


class Pump(Base):

    def __init__(self, name, update_msg):
        super().__init__(name, update_msg)
        self.level = None
        self.type = "Sump Pump"

    def decode_message(self, message, **kwargs):
        m = self.regex.match(str(message))
        self.level = m.group(1)
        return json.dumps({'unit_update': self.__dict__}, default=str)


class Switch(Base):
    def __init__(self, name, update_msg, message_broker):
        self.message_broker = message_broker
        super().__init__(name, update_msg)
        self.type = "Switches"
        self.actions.append("toggle")
        self.state = ""
        if not Base.env:
            Base.env = wemo.WeMoThread(message_broker=message_broker)
            Base.env.start()

    def request_update(self, *args, **kwargs):
        self.state = Base.env.get_state(self.name)
        self.message_broker.ws_server_queue.put(json.dumps({'unit_update': self.__dict__}, default=str))

    def toggle(self, *args, **kwargs):
        self.state = Base.env.toggle(self.name)
        self.request_update()
