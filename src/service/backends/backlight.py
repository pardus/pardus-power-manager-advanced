import os
from util import readfile
from common import *

class backlight_devices:
    def __init__(self):
        self.name = ""
        self.max_brightness = 0

def get_max_brightness(device_name):
    if not os.path.exists("/sys/class/backlight/{}/max_brightness".format(device_name)):
        return 0
    fd = readfile("/sys/class/backlight/{}/max_brightness".format(device_name))
    return int(fd)

def get_devices():
    return os.listdir("/sys/class/backlight/")

def get_brightness(device_name):
    if not os.path.exists("/sys/class/backlight/{}/brightness".format(device_name)):
        return 0
    fd = readfile("/sys/class/backlight/{}/brightness".format(device_name))
    return int(fd)

@asynchronous
def set_brightness(device_name,value):
    log("New backlight: {} = {}".format(device_name, value))
    if device_name == "all":
        for dev in get_devices():
            set_brightness(dev, value)
        return
    # device_name comes from the world writable /run/ppm fifo
    if device_name not in get_devices():
        return
    if value.startswith("%"):
        percent = int(value[1:])
        value = (percent / 100 ) * get_max_brightness(device_name)
    elif value.startswith("+%"):
        percent = int(value[2:])
        fval = get_max_brightness(device_name) * percent / 100
        value = get_brightness(device_name) + fval
    elif value.startswith("-%"):
        percent = int(value[2:])
        fval = get_max_brightness(device_name) * percent / 100
        value = get_brightness(device_name) - fval
    elif value.startswith("+"):
        fval = int(value[1:])
        value = get_brightness(device_name) + fval
    elif value.startswith("-"):
        fval = int(value[1:])
        value = get_brightness(device_name) - fval

    if not os.path.exists("/sys/class/backlight/{}/brightness".format(device_name)):
        return
    fd = open("/sys/class/backlight/{}/brightness".format(device_name),"w")
    fd.write(str(int(value)))
    fd.flush()
    fd.close()

