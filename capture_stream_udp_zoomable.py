import socket
import time
import threading

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

# Initialize Picamera2 and zoom-related variables
picam2 = Picamera2()
video_config_default  = picam2.create_video_configuration({"size": (1532, 864)}, raw=picam2.sensor_modes[0])
video_config_full_fov = picam2.create_video_configuration({"size": (1532, 864)}, raw=picam2.sensor_modes[1])
video_config_full_res = picam2.create_video_configuration({"size": (1532, 864)}, raw=picam2.sensor_modes[2])
picam2.configure(video_config_default)
encoder = H264Encoder(2000000)

full_res = picam2.camera_properties['PixelArraySize']
size = full_res

def use_config_full_res():
    print(picam2.camera_config)
    if picam2.camera_config['raw']['size'][0] != 4608:
        print("changing to full res")
        picam2.stop()
        picam2.configure(video_config_full_res)
        picam2.start()

def use_config_default():
    if picam2.camera_config['raw']['size'][0] != 1532:
        print("changing to default")
        picam2.stop()
        picam2.configure(video_config_default)
        picam2.start()

def use_config_full_fov():
    print(picam2.camera_config)
    if picam2.camera_config['raw']['size'][0] != 2304:
        print("changing to full fov")
        picam2.stop()
        picam2.configure(video_config_full_fov)
        picam2.start()

# Function to handle zooming
def zoom_max():
    print("zooming max")
    use_config_full_res()
    global size
    #time.sleep(2)
    #size = [int(s * 0.95) for s in size]
    size = [1532, 864]
    offset = calc_center_offset(size)
    picam2.set_controls({"ScalerCrop": offset + size})

def zoom_min():
    print("zooming min")
    use_config_full_fov()
    global size
    #size = [int(s * 1.05) for s in size]
    size = [4608, 2592]
    offset = calc_center_offset(size)
    picam2.set_controls({"ScalerCrop": offset + size})

def zoom_mid():
    print("zoom reset")
    use_config_default()
    global size
    size = [3072, 1728]
    offset = calc_center_offset(size)
    picam2.set_controls({"ScalerCrop": offset + size})

def calc_center_offset(size):
    return [(r - s) // 2 for r, s in zip(full_res, size)]

# Function to handle zooming network commands
def handle_commands(sock):
    while True:
        data, addr = sock.recvfrom(1024)
        command = data.decode('utf-8')
        if command == 'zoom_max':
            zoom_max()
        elif command == 'zoom_min':
            zoom_min()
        elif command == 'zoom_mid':
            zoom_mid()

# Create a UDP socket for video
video_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
video_sock.connect(("desk.local", 10001))  # Replace REMOTEIP with the target IP address
stream = video_sock.makefile("wb")

# Create a UDP socket for zooming commands
command_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
command_sock.bind(("0.0.0.0", 10002))

# Start the command handling thread
command_thread = threading.Thread(target=handle_commands, args=(command_sock,))
command_thread.daemon = True
command_thread.start()

# Start video recording
picam2.start_recording(encoder, FileOutput(stream))

try:
    while True:
        # Wait for a new frame
        picam2.capture_metadata()
        time.sleep(0.05)
        
except KeyboardInterrupt:
    print("Stopping recording.")
    picam2.stop_recording()
