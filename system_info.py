"""
SysControl - System information & monitoring module
"""
import platform
import socket
import uuid
import psutil
import datetime
import os
import winreg

try:
    import cpuinfo
except ImportError:
    cpuinfo = None

try:
    import wmi as wmilib
    WMI = wmilib.WMI()
except Exception:
    WMI = None

try:
    import pynvml
    pynvml.nvmlInit()
    HAS_NVIDIA = True
except Exception:
    HAS_NVIDIA = False


def get_size(b, suffix="B"):
    for unit in ["", "K", "M", "G", "T"]:
        if abs(b) < 1024.0:
            return f"{b:.1f} {unit}{suffix}"
        b /= 1024.0
    return f"{b:.1f} P{suffix}"


# ─── CPU ────────────────────────────────────────
def cpu_info():
    info = {}
    info["name"] = platform.processor()
    if cpuinfo:
        try:
            ci = cpuinfo.get_cpu_info()
            info["name"] = ci.get("brand_raw", info["name"])
            info["arch"] = ci.get("arch_string_raw", "")
        except Exception:
            pass
    info["physical_cores"] = psutil.cpu_count(logical=False)
    info["logical_cores"] = psutil.cpu_count(logical=True)
    freq = psutil.cpu_freq()
    if freq:
        info["max_freq"] = f"{freq.max:.0f} MHz"
        info["current_freq"] = f"{freq.current:.0f} MHz"
    info["usage"] = psutil.cpu_percent(interval=0.5)
    info["per_core"] = psutil.cpu_percent(percpu=True, interval=0.3)
    return info


# ─── RAM ────────────────────────────────────────
def ram_info():
    vm = psutil.virtual_memory()
    return {
        "total": get_size(vm.total),
        "available": get_size(vm.available),
        "used": get_size(vm.used),
        "percent": vm.percent,
        "total_bytes": vm.total,
        "used_bytes": vm.used,
    }


# ─── GPU ────────────────────────────────────────
def gpu_info():
    gpus = []
    if HAS_NVIDIA:
        try:
            count = pynvml.nvmlDeviceGetCount()
            for i in range(count):
                h = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(h)
                if isinstance(name, bytes):
                    name = name.decode()
                mem = pynvml.nvmlDeviceGetMemoryInfo(h)
                try:
                    temp = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
                except Exception:
                    temp = 0
                try:
                    util = pynvml.nvmlDeviceGetUtilizationRates(h)
                    gpu_pct = util.gpu
                except Exception:
                    gpu_pct = 0
                gpus.append({
                    "name": name,
                    "total": get_size(mem.total),
                    "used": get_size(mem.used),
                    "free": get_size(mem.free),
                    "temp": f"{temp}°C",
                    "usage": gpu_pct,
                })
        except Exception:
            pass
    if not gpus and WMI:
        try:
            for g in WMI.Win32_VideoController():
                gpus.append({
                    "name": g.Name or "Unknown",
                    "total": get_size(int(g.AdapterRAM or 0)) if g.AdapterRAM else "N/A",
                    "used": "N/A", "free": "N/A", "temp": "N/A", "usage": 0,
                })
        except Exception:
            pass
    return gpus


# ─── DISK ───────────────────────────────────────
def disk_info():
    partitions = []
    for p in psutil.disk_partitions():
        try:
            u = psutil.disk_usage(p.mountpoint)
            partitions.append({
                "device": p.device,
                "mountpoint": p.mountpoint,
                "fstype": p.fstype,
                "total": get_size(u.total),
                "used": get_size(u.used),
                "free": get_size(u.free),
                "percent": u.percent,
            })
        except PermissionError:
            continue
    io = psutil.disk_io_counters()
    return {
        "partitions": partitions,
        "read": get_size(io.read_bytes) if io else "N/A",
        "write": get_size(io.write_bytes) if io else "N/A",
    }


# ─── NETWORK ───────────────────────────────────
def network_info():
    addrs = {}
    for name, nics in psutil.net_if_addrs().items():
        for nic in nics:
            if nic.family == socket.AF_INET:
                addrs[name] = nic.address
    io = psutil.net_io_counters()
    return {
        "interfaces": addrs,
        "bytes_sent": io.bytes_sent,
        "bytes_recv": io.bytes_recv,
        "sent_str": get_size(io.bytes_sent),
        "recv_str": get_size(io.bytes_recv),
        "hostname": socket.gethostname(),
    }


def net_speed():
    io1 = psutil.net_io_counters()
    return io1.bytes_sent, io1.bytes_recv


# ─── OS / SYSTEM ────────────────────────────────
def system_info():
    bt = datetime.datetime.fromtimestamp(psutil.boot_time())
    return {
        "os": f"{platform.system()} {platform.release()}",
        "os_version": platform.version(),
        "hostname": socket.gethostname(),
        "machine": platform.machine(),
        "mac": ":".join(f"{(uuid.getnode() >> i) & 0xff:02x}" for i in range(0, 48, 8)),
        "boot_time": bt.strftime("%Y-%m-%d %H:%M:%S"),
        "uptime": str(datetime.datetime.now() - bt).split(".")[0],
        "user": os.getlogin(),
    }


# ─── PROCESSES ──────────────────────────────────
def process_list(sort_by="cpu"):
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
        try:
            info = p.info
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    key = "cpu_percent" if sort_by == "cpu" else "memory_percent"
    return sorted(procs, key=lambda x: x.get(key, 0) or 0, reverse=True)[:80]


def kill_process(pid):
    try:
        psutil.Process(pid).kill()
        return True
    except Exception:
        return False


# ─── SERVICES ───────────────────────────────────
def services_list():
    svcs = []
    for s in psutil.win_service_iter():
        try:
            info = s.as_dict()
            svcs.append({
                "name": info["name"],
                "display_name": info["display_name"],
                "status": info["status"],
                "start_type": info.get("start_type", ""),
            })
        except Exception:
            continue
    return sorted(svcs, key=lambda x: x["display_name"].lower())


# ─── STARTUP PROGRAMS ──────────────────────────
def startup_programs():
    items = []
    paths = [
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
    ]
    for hive, path in paths:
        try:
            key = winreg.OpenKey(hive, path)
            i = 0
            while True:
                try:
                    name, val, _ = winreg.EnumValue(key, i)
                    items.append({"name": name, "command": val, "scope": "User" if hive == winreg.HKEY_CURRENT_USER else "System"})
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception:
            continue
    return items


# ─── BATTERY ────────────────────────────────────
def battery_info():
    b = psutil.sensors_battery()
    if b is None:
        return None
    return {
        "percent": b.percent,
        "plugged": b.power_plugged,
        "secs_left": b.secsleft if b.secsleft != psutil.POWER_TIME_UNLIMITED else -1,
    }


# ─── TEMPERATURES ──────────────────────────────
def temps():
    result = {}
    if HAS_NVIDIA:
        try:
            count = pynvml.nvmlDeviceGetCount()
            for i in range(count):
                h = pynvml.nvmlDeviceGetHandleByIndex(i)
                t = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
                result[f"GPU {i}"] = f"{t}°C"
        except Exception:
            pass
    try:
        ts = psutil.sensors_temperatures()
        for name, entries in ts.items():
            for e in entries:
                label = e.label or name
                result[label] = f"{e.current:.0f}°C"
    except Exception:
        pass
    return result


# ─── FULL REPORT TEXT ──────────────────────────
def full_report():
    lines = []
    lines.append("═══ SysControl Report ═══\n")

    si = system_info()
    lines.append(f"🖥 OS: {si['os']} ({si['os_version']})")
    lines.append(f"👤 User: {si['user']} @ {si['hostname']}")
    lines.append(f"⏱ Uptime: {si['uptime']}")
    lines.append(f"🔌 Boot: {si['boot_time']}\n")

    ci = cpu_info()
    lines.append(f"💻 CPU: {ci['name']}")
    lines.append(f"   Cores: {ci['physical_cores']}P / {ci['logical_cores']}L")
    lines.append(f"   Usage: {ci['usage']}%\n")

    ri = ram_info()
    lines.append(f"🧠 RAM: {ri['used']} / {ri['total']} ({ri['percent']}%)\n")

    gpus = gpu_info()
    for g in gpus:
        lines.append(f"🎮 GPU: {g['name']}")
        lines.append(f"   VRAM: {g['used']} / {g['total']}")
        lines.append(f"   Temp: {g['temp']}  Usage: {g['usage']}%\n")

    di = disk_info()
    for p in di["partitions"]:
        lines.append(f"💾 {p['device']} ({p['fstype']}): {p['used']} / {p['total']} ({p['percent']}%)")
    lines.append(f"   Total Read: {di['read']}  Write: {di['write']}\n")

    ni = network_info()
    lines.append(f"🌐 Host: {ni['hostname']}")
    for name, ip in ni["interfaces"].items():
        lines.append(f"   {name}: {ip}")
    lines.append(f"   ↑ Sent: {ni['sent_str']}  ↓ Recv: {ni['recv_str']}\n")

    bat = battery_info()
    if bat:
        plug = "⚡ Plugged" if bat["plugged"] else "🔋 On Battery"
        lines.append(f"🔋 Battery: {bat['percent']}% ({plug})\n")

    return "\n".join(lines)
