from vilib import Vilib
from time import strftime,localtime
import os
from ftp_uploader import FTPUploader


class Camera(object):
    def __init__(self):
        username = os.environ['USER']
        #Vilib.rec_video_set["path"] = f"/home/{username}/Videos/" # set path for if video recording is used
        Vilib.camera_start()
        #Vilib.display() #Shows image on screen and enables web interface; Still problematic, and not recomended to use in production environment, but good for debugging
        Vilib.pose_detect_switch(True)
        Vilib.detect_obj_parameter['web_display_flag']  = False
    
    #Video recording functions are no longer used. Camera class is only to initalise camera for now
    '''
    def start_record(self):
        vname = strftime("%Y-%m-%d-%H.%M.%S", localtime())
        Vilib.rec_video_set["name"] = vname #Where to store video
        # start record
        Vilib.rec_video_run()
        Vilib.rec_video_start()
        
        
    def stop_record(self):
        Vilib.rec_video_stop()
    '''
    def take_photo(self, photo_name):
        loc_path = "/home/admin/picar-x/custom/photos"
        Vilib.take_photo(photo_name , path=loc_path)
        print("Take photo triggered")
        return loc_path + "/" + str(photo_name) +".jpg"
        
