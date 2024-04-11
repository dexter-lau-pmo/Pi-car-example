import threading
from vilib import Vilib
from picarx import Picarx

class CVThread(threading.Thread):
    def __init__(self, px, move_bool_array):
        super(CVThread, self).__init__()
        self.px = px
        self.move_bool_array = move_bool_array

    def run(self):
        while True:
            joints = Vilib.detect_obj_parameter['body_joints']
            if joints and (len(joints) >= 12) and joints[11] and joints[12]:
                # proximity check
                filtered_list = list(filter(lambda x: x is not None, joints))
                x_list = list(map(lambda x: x[0], filtered_list))
                y_list = list(map(lambda x: x[1], filtered_list))
                
                max_y = max(y_list) * 480
                max_x = max(x_list) * 640
                min_y = min(y_list) * 480
                min_x = min(x_list) * 640
                human_area = (max_x - min_x) * (max_y - min_y)
                coverage_ratio = human_area / (640 * 480)
              
                if coverage_ratio < 0.01:
                    self.update_boolean_move(True)
                else:
                    self.update_boolean_move(False)
                
    def update_boolean_move(self, isMove):
        self.move_bool_array[0] = isMove
