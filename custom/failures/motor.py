from move import Move
import threading

class Motor(threading.Thread):
    def __init__(self, motor, move_bool_array):
        super(Motor, self).__init__()
        self.motor = motor
        self.lock = threading.Lock()
        self.move_bool_array = move_bool_array

    def run(self):
        while True:
            if any(self.move_bool_array) == True:
                self.motor.forward()
            else:
                self.motor.stop()
                
    def update_boolean_move(self, isMove):
        with self.lock:
            self.move_bool = isMove
