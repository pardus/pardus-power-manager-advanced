import os
import sys
import json
from pathlib import Path
sys.path.insert(0, os.path.dirname( os.path.realpath(__file__) )+"/../common")
from common import *
def listen(main):
    if not os.path.exists("/run/ppm"):
        os.mkfifo("/run/ppm")
        os.chmod("/run/ppm", 0o222)
        os.chown("/run/ppm", 0, 0)
    while True:
        fifo = Path("/run/ppm")
        data = fifo.read_text().strip()
        print(data)
        if data != "":
            data = json.loads(data)
            if "pid" in data:
                main(data)
@cached
def list_acpi_osi():
    ret = []
    for name in strings("/sys/firmware/acpi/tables/DSDT"):
        if "_OSI\n" in name.strip():
            ret.append(name.split("\n")[-1])
    ret.sort()
    return ret

def send_client(data):
    print(data)
    data["pid"] = str(os.getpid())
    for dir in listdir("/run/user"):
        if os.path.exists("/run/user/{}/ppm/".format(dir)):
            for fifo in listdir("/run/user/{}/ppm/".format(dir)):
                debug("Send data to client: {} {}".format(dir, fifo))
                if not os.path.isdir("/proc/{}".format(fifo)):
                    os.unlink("/run/user/{}/ppm/{}".format(dir,fifo))
                else:
                    with open("/run/user/{}/ppm/{}".format(dir,fifo), "w") as f:
                        f.write(json.dumps(data))
                        f.flush()
