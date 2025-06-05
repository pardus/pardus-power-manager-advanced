import os
from util import writefile, readfile, listdir
from backends.cpu import list_cpu, list_big_cpu, list_little_cpu,  change_cpu_status
from backends.backlight import set_brightness
from common import *
from service.ai_assistant import AIAssistant


_cur_mode = None
ai_assistant = AIAssistant()

def set_mode(mode):
    global _cur_mode
    if _cur_mode == mode:
        return
    backlight="%100"
    if mode == "performance":
        _performance()
        backlight = get("backlight-performance","%100","modes")
    elif mode == "balanced":
        _balanced()
        backlight = get("backlight-balanced","%75","modes")
    elif mode == "powersave":
        _powersave()
        backlight = get("backlight-powersave","%50","modes")
    elif mode == "ai_optimized":
        _ai_optimized()
        backlight = get("backlight-ai_optimized","%75","modes")
    else:
        return
    _cur_mode = mode
    set_brightness("all", backlight)
    log("New mode: {}".format(mode))

def get_mode():
    return _cur_mode

#### Power Functions ####

def set_governor_mode(powersave):
    if get("governor",True,"power"):
       # cpu governor
        cpu_path="/sys/devices/system/cpu/"
        for dir in listdir(cpu_path):
            if dir.startswith("cpu"):
                if powersave:
                    writefile("{}/{}/cpufreq/scaling_governor".format(cpu_path,dir),"powersave")
                else:
                    writefile("{}/{}/cpufreq/scaling_governor".format(cpu_path,dir),"performance")

def set_core_mode(powersave):
    if powersave:
        if get("cpufreq",True,"power"):
            # decrease max cpu freq
            ratio = float(get("freq-ratio",0.5,"powersave"))
            if ratio > 1.0:
                ratio = 1.0
            cpu_path="/sys/devices/system/cpu/"
            for dir in listdir(cpu_path):
                if not dir.startswith("cpu"):
                    continue
                freq_file = "{}/{}/cpufreq/scaling_available_frequencies".format(cpu_path,dir)
                if os.path.exists(freq_file):
                    freqs = readfile(freq_file).split(" ")
                    if len(freqs) > 0 and freqs[0] != '':
                        new_freq = freqs[int((len(freqs) -1) * ratio)]
                        writefile("{}/{}/cpufreq/scaling_max_freq".format(cpu_path,dir),int(new_freq))
                else:
                    min_freq=readfile("{}/{}/cpufreq/cpuinfo_min_freq".format(cpu_path,dir))
                    max_freq=readfile("{}/{}/cpufreq/cpuinfo_max_freq".format(cpu_path,dir))
                    if min_freq != "" and max_freq != "":
                        # ignore if lower than 2Ghz
                        if int(max_freq) >= 2000000:
                            new_freq = int(max_freq) * ratio
                            if new_freq < 2000000:
                                new_freq = 2000000
                            writefile("{}/{}/cpufreq/scaling_max_freq".format(cpu_path,dir),int(new_freq))

        if get("core",True,"power"):
            # disable cpu core
            def cpu_disable_event(cpus, min):
                dnum = len(cpus) * float(get("core-ratio",0.5,"powersave"))
                if len(cpus) <= min:
                    dnum = 0
                elif len(cpus) - dnum < min:
                    dnum = min
                for cpu in range(len(cpus) - int(dnum), len(cpus)):
                    change_cpu_status(cpu,False)
            cpu_disable_event(list_big_cpu(), 4)
            cpu_disable_event(list_little_cpu(), 0)
    else:
        if get("core",True,"power"):
            # enable cpu core
            cpus = list_cpu()
            print(cpus)
            for cpu in range(0, len(cpus)):
                change_cpu_status(cpu,True)

        if get("cpufreq",True,"power"):
            # increase max cpu freq
            cpu_path="/sys/devices/system/cpu/"
            for dir in listdir(cpu_path):
                if not dir.startswith("cpu"):
                    continue
                max_freq=readfile("{}/{}/cpufreq/cpuinfo_max_freq".format(cpu_path,dir))
                if max_freq != "":
                    writefile("{}/{}/cpufreq/scaling_max_freq".format(cpu_path,dir),max_freq)

def set_pstate_mode(powersave):
    # intel pstate
    freq_path="/sys/devices/system/cpu/cpufreq/"
    for dir in listdir(freq_path):
        if dir.startswith("policy"):
            epath="energy_performance_preference"
            if powersave:
                writefile("{}/{}/{}".format(freq_path, dir, epath), "power")
            else:
                writefile("{}/{}/{}".format(freq_path, dir, epath), "performance")

def set_sysfs_mode(powersave):
    if powersave:
        # laptop mode
        writefile("/proc/sys/vm/laptop_mode",5)

        # NMI watchdog
        writefile("/proc/sys/kernel/nmi_watchdog",0)

        # platform profile
        writefile("/sys/firmware/acpi/platform_profile","low-power")

        # less disk activity
        writefile("/proc/sys/vm/dirty_writeback_centisecs",1500)
        writefile("/proc/sys/vm/dirty_expire_centisecs",3000)
        writefile("/proc/sys/vm/dirty_ratio", "10")
        writefile("/proc/sys/vm/dirty_background_ratio", "5")

        # vfs cache pressure
        writefile("/proc/sys/vm/vfs_cache_pressure", "50")

        # disable THP
        writefile("/sys/kernel/mm/transparent_hugepage/enabled", "never")
    else:
        # laptop mode
        writefile("/proc/sys/vm/laptop_mode",0)

        # NMI watchdog
        writefile("/proc/sys/kernel/nmi_watchdog",0)

        # platform profile
        writefile("/sys/firmware/acpi/platform_profile","performance")

        # more disk activity
        writefile("/proc/sys/vm/dirty_writeback_centisecs",500)
        writefile("/proc/sys/vm/dirty_expire_centisecs",500)
        writefile("/proc/sys/vm/dirty_ratio", "20")
        writefile("/proc/sys/vm/dirty_background_ratio", "10")

        # vfs cache pressure
        writefile("/proc/sys/vm/vfs_cache_pressure", "100")

        # enable THP
        writefile("/sys/kernel/mm/transparent_hugepage/enabled", "madvise")


def set_scsi_mode(powersave):
    if get("scsi",True,"power"):
        # sata channel
        scsi_host_path="/sys/class/scsi_host/"
        for dir in listdir(scsi_host_path):
            if dir.startswith("host"):
                if powersave:
                    writefile("{}/{}/link_power_management_policy".format(scsi_host_path,dir),"max_performance")
                else:
                    writefile("{}/{}/link_power_management_policy".format(scsi_host_path,dir),"min_power")

def set_usb_mode(powersave):
    if get("usb",True,"power"):
        # usb auto suspend
        usb_path="/sys/bus/usb/devices/"
        for dir in listdir(usb_path):
            # ignore if interface type is HID or HUB
            if os.path.isfile("{}/{}/bInterfaceClass".format(usb_path,dir)):
                if readfile("{}/{}/bInterfaceClass".format(usb_path,dir)) in ["03","09"]:
                    continue
                if powersave:
                    writefile("{}/{}/power/control".format(usb_path,dir),"auto")
                else:
                    writefile("{}/{}/power/control".format(usb_path,dir),"on")
                writefile("{}/{}/power/autosuspend_delay_ms".format(usb_path,dir),get("suspend_delay", "60000", "power"))


def set_block_mode(powersave):
    if get("block",True,"power"):
        # block auto suspend
        block_path="/sys/block/"
        for dir in listdir(block_path):
            if powersave:
                writefile("{}/{}/device/power/control".format(block_path,dir),"auto")
            else:
                writefile("{}/{}/device/power/control".format(block_path,dir),"on")

def set_pci_mode(powersave):
    if get("pci",True,"power"):
        # pci auto suspend
        pci_path="/sys/bus/pci/devices/"
        for dir in listdir(pci_path):
            if powersave:
                writefile("{}/{}/power/control".format(pci_path,dir),"auto")
            else:
                writefile("{}/{}/power/control".format(pci_path,dir),"on")
            writefile("{}/{}/power/autosuspend_delay_ms".format(pci_path,dir),get("suspend_delay", "60000", "power"))
        if powersave:
            writefile("/sys/module/pcie_aspm/parameters/policy", "powersave")
        else:
            writefile("/sys/module/pcie_aspm/parameters/policy", "performance")

def set_i2c_mode(powersave):
    if get("i2c",True,"power"):
        # i2c auto suspend
        i2c_path="/sys/bus/i2c/devices/"
        for dir in listdir(i2c_path):
            if powersave:
                writefile("{}/{}/power/control".format(i2c_path,dir),"auto")
                writefile("{}/{}/device/power/control".format(i2c_path,dir),"auto")
            else:
                writefile("{}/{}/power/control".format(i2c_path,dir),"on")
                writefile("{}/{}/device/power/control".format(i2c_path,dir),"on")


def set_audio_mode(powersave):
    if get("audio",True,"power"):
        # audio card
        if powersave:
            writefile("/sys/module/snd_hda_intel/parameters/power_save",1)
            writefile("/sys/module/snd_hda_intel/parameters/power_save_controller","Y")
        else:
            writefile("/sys/module/snd_hda_intel/parameters/power_save",0)
            writefile("/sys/module/snd_hda_intel/parameters/power_save_controller","N")

def set_turbo_mode(powersave):
    if get("turbo",True,"power"):
        # turbo boost
        if powersave:
            writefile("/sys/devices/system/cpu/intel_pstate/no_turbo",1)
            writefile("/sys/devices/system/cpu/cpufreq/boost",0)
        else:
            # turbo boost
            writefile("/sys/devices/system/cpu/intel_pstate/no_turbo",0)
            writefile("/sys/devices/system/cpu/cpufreq/boost",1)

def set_gpu_mode(powersave):
    if get("gpu",True,"power"):
        # gpu powersave boost
        dri_path="/sys/class/drm/"
        for card in listdir(dri_path):
            if card.startswith("card") and card[4:].isnumeric():
                if powersave:
                    writefile("{}/{}/device/power_dpm_force_performance_level".format(dri_path, card), "low")
                    writefile("{}/{}/device/power_dpm_state".format(dri_path, card), "battery")
                    writefile("{}/{}/device/power/control".format(dri_path, card), "auto")
                else:
                    writefile("{}/{}/device/power_dpm_force_performance_level".format(dri_path, card), "auto")
                    writefile("{}/{}/device/power_dpm_state".format(dri_path, card), "performance")
                    writefile("{}/{}/device/power/control".format(dri_path, card), "on")

def set_network_mode(powersave):
    if get("network",True,"power"):
        # network
        net_path="/sys/class/net/"
        for dir in listdir(net_path):
            if powersave:
                writefile("{}/{}/device/power/control".format(net_path,dir),"auto")
            else:
                writefile("{}/{}/device/power/control".format(net_path,dir),"on")

def set_bluetooth_mode(powersave):
    if get("bluetooth",True,"power"):
        # bluetooth
        net_path="/sys/class/bluetooth/"
        for dir in listdir(net_path):
            if powersave:
                writefile("{}/{}/power/control".format(net_path,dir),"auto")
            else:
                writefile("{}/{}/power/control".format(net_path,dir),"on")

def set_nvme_mode(powersave):
    if get("nvme",True,"power"):
        # nvme
        net_path="/sys/class/nvme/"
        for dir in listdir(net_path):
            if powersave:
                writefile("{}/{}/power/control".format(net_path,dir),"auto")
            else:
                writefile("{}/{}/power/control".format(net_path,dir),"on")

# https://wiki.debian.org/SimplePowerSave
@asynchronous
def _powersave():
    """
    Powersave mode provide maximum battery life.
    It will reduce power usage and fan speed.
    """
    set_governor_mode(True)
    set_core_mode(True)
    set_pstate_mode(True)
    set_sysfs_mode(True)

    if not is_acpi_supported() and not get("unstable", False, "service"):
        return

    set_scsi_mode(True)
    set_usb_mode(True)
    set_block_mode(True)
    set_pci_mode(True)
    set_i2c_mode(True)
    set_audio_mode(True)
    set_turbo_mode(True)
    set_gpu_mode(True)
    set_network_mode(True)
    set_bluetooth_mode(True)
    set_nvme_mode(True)

@asynchronous
def _balanced():
    """
    Balanced mode same with powersave but core and sysfs modes are performance
    Balanced mode provide power save without performance issues
    """
    set_governor_mode(True)
    set_core_mode(False)
    set_pstate_mode(True)
    set_sysfs_mode(False)

    if not is_acpi_supported() and not get("unstable", False, "service"):
        return

    set_scsi_mode(True)
    set_usb_mode(True)
    set_block_mode(True)
    set_pci_mode(True)
    set_i2c_mode(True)
    set_audio_mode(True)
    set_turbo_mode(True)
    set_gpu_mode(True)
    set_network_mode(True)
    set_bluetooth_mode(True)
    set_nvme_mode(True)


@asynchronous
def _ai_optimized():
    """
    AI Optimized mode uses the AI Assistant to choose an underlying power profile,
    or a configured default mode if the assistant is disabled.
    """
    ai_enabled = get("enabled", "true", "ai_assistant").lower() == "true"

    if ai_enabled:
        recommended_mode = ai_assistant.get_recommendation()
        log(f"AI Optimized mode: AI Assistant enabled, recommended: {recommended_mode}")
        if recommended_mode == "performance":
            _performance()
        elif recommended_mode == "balanced":
            _balanced()
        elif recommended_mode == "powersave":
            _powersave()
        else:
            log(f"AI Assistant recommended an unknown mode: {recommended_mode}. Defaulting to balanced.")
            _balanced()
    else:
        default_mode = get("default_mode", "balanced", "ai_assistant")
        log(f"AI Optimized mode: AI Assistant disabled, using default_mode: {default_mode}")
        if default_mode == "performance":
            _performance()
        elif default_mode == "balanced":
            _balanced()
        elif default_mode == "powersave":
            _powersave()
        else:
            log(f"Configured default_mode '{default_mode}' is unknown. Defaulting to balanced.")
            _balanced()

    # The actual settings applied are from one of the above modes.
    # _ai_optimized itself doesn't have a fixed set of power settings anymore.


@asynchronous
def _performance():
    """
    Performance mode provide maximum performance.
    It will increase power usage and fan speed.
    """
    set_governor_mode(False)
    set_core_mode(False)
    set_pstate_mode(False)
    set_sysfs_mode(False)

    if not is_acpi_supported() and not get("unstable", False, "service"):
        return

    set_scsi_mode(False)
    set_usb_mode(False)
    set_block_mode(False)
    set_pci_mode(False)
    set_i2c_mode(False)
    set_audio_mode(False)
    set_turbo_mode(False)
    set_gpu_mode(False)
    set_network_mode(False)
    set_bluetooth_mode(False)
    set_nvme_mode(False)

