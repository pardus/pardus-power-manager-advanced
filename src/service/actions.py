#!/usr/bin/env python3
from util import *
import sys
import subprocess
import json

if len(sys.argv) < 2:
    sys.exit(0)

def write_settings(data):
    ctx = ""
    for section in data:
        if section == "osi":
            if "prefer" in data["osi"].keys() and data["osi"]["prefer"] != "":
                grub_cfg = "GRUB_CMDLINE_LINUX_DEFAULT=\"${GRUB_CMDLINE_LINUX_DEFAULT} acpi_osi=\\\""+data["osi"]["prefer"]+"\\\"\""
                writefile("/etc/default/grub.d/99-ppm.conf", grub_cfg)
            else:
                if os.path.isfile("/etc/default/grub.d/99-ppm.conf"):
                    os.unlink("/etc/default/grub.d/99-ppm.conf")
            subprocess.run(["grub-mkconfig", "-o", "/boot/grub/grub.cfg"])
            continue
        ctx += "[" + section + "]\n"
        for var in data[section]:
            ctx += str(var) + "=" + str(data[section][var]) +"\n"
        ctx += "\n"
    writefile("/etc/pardus/ppm.conf.d/99-ppm-settings.conf",ctx)


if sys.argv[1] == "save-config":
    write_settings(json.loads(sys.argv[2]))