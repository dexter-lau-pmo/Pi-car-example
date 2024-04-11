# cv_thread.py
import threading
from time import sleep
from vilib import Vilib
from picarx import Picarx

class DetectionThread(threading.Thread):
    def __init__(self, joints):
        super(DetectionThread, self).__init__()
        Vilib.camera_start()
        Vilib.display()
        Vilib.pose_detect_switch(True)
        self.joints = joints
        
    def run(self):
        while True:
            self.joints = Vilib.detect_obj_parameter['body_joints']
