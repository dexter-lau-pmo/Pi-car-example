import threading

class Timer(object):
    
    def __init__(self):
        self.flag = True
        self.timer = None

    def new_timer(self, time=10):
        self.flag = False
        if isinstance(self.timer, threading.Timer):
            self.timer.cancel()
        self.timer = threading.Timer(time, self.set_flag)
        self.timer.start()
        
    def set_flag(self):
        self.flag = True
        
    def is_timelapse_over(self):
        if self.flag:
            self.flag = False
            return True
        return False
