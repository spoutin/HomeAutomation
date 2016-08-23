from threading import Timer, Event


class perpetualTimer(object):

    # give it a cycle time (t) and a callback (hFunction)
    def __init__(self, t, hFunction):
        self.t = t
        self.stop = Event()
        self.hFunction = hFunction
        self.thread = Timer(self.t, self.handle_function)

    def handle_function(self):
        self.hFunction()
        self.thread = Timer(self.t, self.handle_function)
        if not self.stop.is_set():
            self.thread.start()

    def start(self):
        self.stop.clear()
        self.thread.start()

    def cancel(self):
        self.stop.set()
        self.thread.cancel()
