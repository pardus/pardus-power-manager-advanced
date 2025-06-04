#!/usr/bin/env python3
from util import *
from service import main
from backends.power import set_mode
from backends.wakeup import enable_usb_wakeups
import time
import os
import json

from util import *

if not get("enabled",True,"service"):
    exit(0)

import traceback
singleinstance()

if os.path.exists("/run/ppm"):
    os.unlink("/run/ppm")

if get("usb-wakeups",False, "service"):
    enable_usb_wakeups()

log_begin()
log("Starting Pardus Power Manager Service")

@asynchronous
def battery_loop():
    interval = int(get("update-interval",60, "service"))
    while True:
        time.sleep(interval)
        data = {}
        data["pid"] = os.getpid()
        data["update"] = "service"
        main(data)

battery_loop()

# set initial mode state
mode = get("ac-mode","balanced","modes")
if not get_ac_online():
    mode = get("bat-mode","powersave","modes")
set_mode(mode)

while True:
    try:
        listen(main)
    except Exception as e:
        print(e)
        print("reload")
