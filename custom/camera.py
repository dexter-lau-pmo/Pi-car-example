from vilib import Vilib
from time import strftime,localtime
import os

class Camera(object):
    def __init__(self):
        username = os.environ['USER']
        #Vilib.rec_video_set["path"] = f"/home/{username}/Videos/" # set path
        Vilib.camera_start()
        #Vilib.display()
        Vilib.pose_detect_switch(True)
        Vilib.detect_obj_parameter['web_display_flag']  = False
        
    def start_record(self):
        vname = strftime("%Y-%m-%d-%H.%M.%S", localtime())
        Vilib.rec_video_set["name"] = vname #Where to store video
        # start record
        Vilib.rec_video_run()
        Vilib.rec_video_start()
        
        
    def stop_record(self):
        Vilib.rec_video_stop()
        
