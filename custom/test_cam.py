from camera import Camera
from picarx import Picarx
from vilib import Vilib
from ftp_uploader import FTPUploader

import time


photo_name = "Test" #jpg file type
print("Start test")
my_cam = Camera()
ftp_uploader = FTPUploader()

start_time = time.time()

file_loc = my_cam.take_photo(photo_name)
print(file_loc)
gcp_file_loc = "photos/" + photo_name


ftp_uploader.upload_file(file_loc , gcp_file_loc)

print("End test")

end_time = time.time()

# Calculate the runtime
runtime = end_time - start_time

print("Runtime:", runtime, "seconds")
