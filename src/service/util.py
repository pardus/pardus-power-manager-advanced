import os
import sys
import json
import stat
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
    message = json.dumps(data).encode()
    for dir in listdir("/run/user"):
        # /run/user/<uid>/ppm belongs to the user. Don't follow symlinks
        # in it and don't block on a fifo that nobody reads.
        try:
            dir_fd = os.open("/run/user/{}/ppm".format(dir),
                             os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError:
            continue
        try:
            for fifo in os.listdir(dir_fd):
                debug("Send data to client: {} {}".format(dir, fifo))
                try:
                    if not os.path.isdir("/proc/{}".format(fifo)):
                        os.unlink(fifo, dir_fd=dir_fd)
                        continue
                    fd = os.open(fifo, os.O_WRONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
                                 dir_fd=dir_fd)
                except OSError:
                    continue
                try:
                    if stat.S_ISFIFO(os.fstat(fd).st_mode):
                        os.write(fd, message)
                except OSError:
                    pass
                finally:
                    os.close(fd)
        finally:
            os.close(dir_fd)
