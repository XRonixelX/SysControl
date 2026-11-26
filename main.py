"""
SysControl — Full System Manager for Windows
Modern dark theme · Real-time monitoring · Telegram integration
"""
import customtkinter as ctk
import threading
import time
import os
import json
import subprocess

import system_info as si
from telegram_sender import TelegramBot

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

ACCENT   = "#00C9A7"
ACCENT2  = "#00B4D8"
BG_DARK  = "#0D0D14"
BG_CARD  = "#161622"
BG_CARD2 = "#1C1C2E"
FG_DIM   = "#8E8E93"
RED      = "#FF453A"
GREEN    = "#30D158"
YELLOW   = "#FFD60A"

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".syscontrol.json")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SysControl")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(fg_color=BG_DARK)
        self.telegram = TelegramBot()
        self.prev_sent = 0
        self.prev_recv = 0
        self.running = True
        self.load_config()
        self.build_ui()
        self.start_monitoring()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ─── CONFIG ──────────────────────────────
    def load_config(self):
        try:
            with open(CONFIG_FILE) as f:
                cfg = json.load(f)
            self.telegram.configure(cfg.get("tg_token", ""), cfg.get("tg_chat", ""))
        except Exception:
            pass

    def save_config(self, token, chat_id):
        self.telegram.configure(token, chat_id)
        with open(CONFIG_FILE, "w") as f:
            json.dump({"tg_token": token, "tg_chat": chat_id}, f)

    # ─── UI ──────────────────────────────────
    def build_ui(self):
        # Sidebar
        sidebar = ctk.CTkFrame(self, width=200, fg_color=BG_CARD, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo = ctk.CTkLabel(sidebar, text="⚡ SysControl", font=ctk.CTkFont(size=22, weight="bold"), text_color=ACCENT)
        logo.pack(pady=(24, 4))
        sub = ctk.CTkLabel(sidebar, text="System Manager", font=ctk.CTkFont(size=11), text_color=FG_DIM)
        sub.pack(pady=(0, 24))

        self.tabs = {}
        self.content = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self.content.pack(side="right", fill="both", expand=True)

        buttons_info = [
            ("📊  Dashboard",   "dashboard"),
            ("💻  Hardware",    "hardware"),
            ("📋  Processes",   "processes"),
            ("🌐  Network",     "network"),
            ("💾  Disks",       "disks"),
            ("🔧  Services",    "services"),
            ("🚀  Startup",     "startup"),
            ("📱  Telegram",    "telegram"),
            ("⚙️  Power",       "power"),
        ]
        self.btn_refs = {}
        for text, key in buttons_info:
            btn = ctk.CTkButton(sidebar, text=text, anchor="w", height=38,
                                font=ctk.CTkFont(size=14),
                                fg_color="transparent", hover_color=BG_CARD2,
                                text_color="#EBEBF5",
                                command=lambda k=key: self.switch_tab(k))
            btn.pack(fill="x", padx=10, pady=2)
            self.btn_refs[key] = btn

        self.current_tab = None
        self.switch_tab("dashboard")

    def switch_tab(self, key):
        if self.current_tab == key:
            return
        self.current_tab = key
        for k, btn in self.btn_refs.items():
            btn.configure(fg_color=ACCENT if k == key else "transparent",
                          text_color="#000000" if k == key else "#EBEBF5")
        for w in self.content.winfo_children():
            w.destroy()
        builder = getattr(self, f"build_{key}", None)
        if builder:
            builder()

    # ─── HELPERS ──────────────────────────────
    def card(self, parent, **kwargs):
        return ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=14, **kwargs)

    def stat_box(self, parent, title, value, color=ACCENT):
        f = self.card(parent)
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=12), text_color=FG_DIM).pack(anchor="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(f, text=value, font=ctk.CTkFont(size=22, weight="bold"), text_color=color).pack(anchor="w", padx=14, pady=(0, 12))
        return f

    def meter(self, parent, label, pct, color=ACCENT):
        f = self.card(parent)
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=12), text_color=FG_DIM).pack(anchor="w", padx=14, pady=(10, 2))
        bar = ctk.CTkProgressBar(f, height=12, corner_radius=6, progress_color=color, fg_color=BG_CARD2)
        bar.set(pct / 100.0)
        bar.pack(fill="x", padx=14, pady=(0, 4))
        val = ctk.CTkLabel(f, text=f"{pct:.1f}%", font=ctk.CTkFont(size=18, weight="bold"), text_color="#FFFFFF")
        val.pack(anchor="w", padx=14, pady=(0, 10))
        return f, bar, val

    # ═══════════════ DASHBOARD ═══════════════
    def build_dashboard(self):
        scroll = ctk.CTkScrollableFrame(self.content, fg_color=BG_DARK)
        scroll.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(scroll, text="Dashboard", font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w", pady=(0, 12))

        row1 = ctk.CTkFrame(scroll, fg_color="transparent")
        row1.pack(fill="x", pady=4)
        row1.columnconfigure((0, 1, 2, 3), weight=1)

        # CPU
        cpu = si.cpu_info()
        self.cpu_frame, self.cpu_bar, self.cpu_val = self.meter(row1, f"CPU  —  {cpu['name'][:30]}", cpu["usage"], ACCENT)
        self.cpu_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # RAM
        ram = si.ram_info()
        self.ram_frame, self.ram_bar, self.ram_val = self.meter(row1, f"RAM  —  {ram['used']} / {ram['total']}", ram["percent"], ACCENT2)
        self.ram_frame.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)

        # GPU
        gpus = si.gpu_info()
        gpu_pct = gpus[0]["usage"] if gpus else 0
        gpu_name = gpus[0]["name"][:22] if gpus else "No GPU"
        self.gpu_frame, self.gpu_bar, self.gpu_val = self.meter(row1, f"GPU  —  {gpu_name}", gpu_pct, YELLOW)
        self.gpu_frame.grid(row=0, column=2, sticky="nsew", padx=4, pady=4)

        # Net
        self.net_box = self.stat_box(row1, "Network  ↑ / ↓", "0 / 0", GREEN)
        self.net_box.grid(row=0, column=3, sticky="nsew", padx=4, pady=4)
        self.net_up_lbl = self.net_box.winfo_children()[1]

        # Row 2: Disks
        row2 = ctk.CTkFrame(scroll, fg_color="transparent")
        row2.pack(fill="x", pady=4)
        di = si.disk_info()
        self.disk_bars = []
        for idx, p in enumerate(di["partitions"][:4]):
            row2.columnconfigure(idx, weight=1)
            f, bar, val = self.meter(row2, f"{p['device']}  —  {p['used']}/{p['total']}", p["percent"],
                                     RED if p["percent"] > 90 else ACCENT)
            f.grid(row=0, column=idx, sticky="nsew", padx=4, pady=4)

        # Sys info
        sys = si.system_info()
        info_frame = self.card(scroll)
        info_frame.pack(fill="x", pady=8)
        ctk.CTkLabel(info_frame, text=f"🖥  {sys['os']}  ·  {sys['user']}@{sys['hostname']}  ·  Uptime: {sys['uptime']}",
                      font=ctk.CTkFont(size=13), text_color=FG_DIM).pack(padx=14, pady=10)

        # CPU per-core
        core_frame = self.card(scroll)
        core_frame.pack(fill="x", pady=4)
        ctk.CTkLabel(core_frame, text="CPU Per-Core Usage", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(10, 6))
        self.core_bars = []
        for i, pct in enumerate(cpu.get("per_core", [])):
            row_f = ctk.CTkFrame(core_frame, fg_color="transparent", height=18)
            row_f.pack(fill="x", padx=14, pady=1)
            ctk.CTkLabel(row_f, text=f"Core {i}", width=50, font=ctk.CTkFont(size=11), text_color=FG_DIM).pack(side="left")
            bar = ctk.CTkProgressBar(row_f, height=8, corner_radius=4, progress_color=ACCENT, fg_color=BG_CARD2)
            bar.set(pct / 100.0)
            bar.pack(side="left", fill="x", expand=True, padx=6)
            lbl = ctk.CTkLabel(row_f, text=f"{pct:.0f}%", width=40, font=ctk.CTkFont(size=11), text_color="#FFFFFF")
            lbl.pack(side="right")
            self.core_bars.append((bar, lbl))
        ctk.CTkLabel(core_frame, text="", height=6).pack()

    # ═══════════════ HARDWARE ═══════════════
    def build_hardware(self):
        scroll = ctk.CTkScrollableFrame(self.content, fg_color=BG_DARK)
        scroll.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(scroll, text="Hardware Info", font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w", pady=(0, 12))

        def section(title, items):
            f = self.card(scroll)
            f.pack(fill="x", pady=6)
            ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT).pack(anchor="w", padx=14, pady=(12, 6))
            for k, v in items:
                row = ctk.CTkFrame(f, fg_color="transparent")
                row.pack(fill="x", padx=14, pady=2)
                ctk.CTkLabel(row, text=k, font=ctk.CTkFont(size=13), text_color=FG_DIM, width=180, anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=str(v), font=ctk.CTkFont(size=13), text_color="#FFFFFF", anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(f, text="", height=6).pack()

        sys = si.system_info()
        section("🖥  System", [
            ("OS", sys["os"]), ("Version", sys["os_version"]), ("Hostname", sys["hostname"]),
            ("User", sys["user"]), ("Architecture", sys["machine"]), ("MAC Address", sys["mac"]),
            ("Boot Time", sys["boot_time"]), ("Uptime", sys["uptime"]),
        ])

        cpu = si.cpu_info()
        section("💻  CPU", [
            ("Processor", cpu["name"]), ("Physical Cores", cpu["physical_cores"]),
            ("Logical Cores", cpu["logical_cores"]),
            ("Max Frequency", cpu.get("max_freq", "N/A")),
            ("Current Frequency", cpu.get("current_freq", "N/A")),
        ])

        ram = si.ram_info()
        section("🧠  Memory", [
            ("Total", ram["total"]), ("Used", ram["used"]),
            ("Available", ram["available"]), ("Usage", f"{ram['percent']}%"),
        ])

        gpus = si.gpu_info()
        for g in gpus:
            section(f"🎮  GPU — {g['name']}", [
                ("VRAM Total", g["total"]), ("VRAM Used", g["used"]),
                ("VRAM Free", g["free"]), ("Temperature", g["temp"]),
                ("GPU Usage", f"{g['usage']}%"),
            ])

        temps = si.temps()
        if temps:
            section("🌡  Temperatures", [(k, v) for k, v in temps.items()])

    # ═══════════════ PROCESSES ═══════════════
    def build_processes(self):
        top = ctk.CTkFrame(self.content, fg_color=BG_DARK)
        top.pack(fill="x", padx=16, pady=(16, 6))
        ctk.CTkLabel(top, text="Processes", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="🔄 Refresh", width=90, height=30, fg_color=ACCENT,
                       text_color="#000000", command=self.refresh_procs).pack(side="right", padx=4)
        ctk.CTkButton(top, text="❌ Kill Selected", width=110, height=30, fg_color=RED,
                       text_color="#FFFFFF", command=self.kill_selected).pack(side="right", padx=4)

        self.proc_scroll = ctk.CTkScrollableFrame(self.content, fg_color=BG_DARK)
        self.proc_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Header
        hdr = ctk.CTkFrame(self.proc_scroll, fg_color=BG_CARD2, corner_radius=8, height=32)
        hdr.pack(fill="x", pady=(0, 4))
        for txt, w in [("PID", 70), ("Name", 240), ("CPU %", 80), ("RAM %", 80), ("Status", 100)]:
            ctk.CTkLabel(hdr, text=txt, width=w, font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT, anchor="w").pack(side="left", padx=4)

        self.proc_widgets = []
        self.selected_pid = None
        self.refresh_procs()

    def refresh_procs(self):
        for w in self.proc_widgets:
            w.destroy()
        self.proc_widgets.clear()

        procs = si.process_list("cpu")
        for p in procs:
            row = ctk.CTkFrame(self.proc_scroll, fg_color=BG_CARD, corner_radius=6, height=28, cursor="hand2")
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            pid = p.get("pid", 0)
            cpu_pct = p.get("cpu_percent", 0) or 0
            mem_pct = p.get("memory_percent", 0) or 0
            cpu_color = RED if cpu_pct > 50 else (YELLOW if cpu_pct > 20 else "#FFFFFF")
            ctk.CTkLabel(row, text=str(pid), width=70, font=ctk.CTkFont(size=12), text_color=FG_DIM, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=str(p.get("name", ""))[:30], width=240, font=ctk.CTkFont(size=12), text_color="#FFFFFF", anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=f"{cpu_pct:.1f}", width=80, font=ctk.CTkFont(size=12), text_color=cpu_color, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=f"{mem_pct:.1f}", width=80, font=ctk.CTkFont(size=12), text_color=ACCENT2, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=str(p.get("status", "")), width=100, font=ctk.CTkFont(size=12), text_color=FG_DIM, anchor="w").pack(side="left", padx=4)
            row.bind("<Button-1>", lambda e, pid=pid: self.select_proc(pid))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, pid=pid: self.select_proc(pid))
            self.proc_widgets.append(row)

    def select_proc(self, pid):
        self.selected_pid = pid
        for w in self.proc_widgets:
            try:
                lbl = w.winfo_children()[0]
                is_sel = lbl.cget("text") == str(pid)
                w.configure(fg_color=BG_CARD2 if is_sel else BG_CARD)
            except Exception:
                pass

    def kill_selected(self):
        if self.selected_pid:
            si.kill_process(self.selected_pid)
            self.after(300, self.refresh_procs)

    # ═══════════════ NETWORK ═══════════════
    def build_network(self):
        scroll = ctk.CTkScrollableFrame(self.content, fg_color=BG_DARK)
        scroll.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(scroll, text="Network", font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w", pady=(0, 12))

        ni = si.network_info()
        f = self.card(scroll)
        f.pack(fill="x", pady=6)
        ctk.CTkLabel(f, text="📡  Interfaces", font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT).pack(anchor="w", padx=14, pady=(12, 6))
        for name, ip in ni["interfaces"].items():
            row = ctk.CTkFrame(f, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=2)
            ctk.CTkLabel(row, text=name, font=ctk.CTkFont(size=13), text_color=FG_DIM, width=200, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=ip, font=ctk.CTkFont(size=13), text_color="#FFFFFF").pack(side="left")
        ctk.CTkLabel(f, text="", height=6).pack()

        f2 = self.card(scroll)
        f2.pack(fill="x", pady=6)
        ctk.CTkLabel(f2, text="📊  Total Traffic", font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT2).pack(anchor="w", padx=14, pady=(12, 6))
        row2 = ctk.CTkFrame(f2, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=6)
        row2.columnconfigure((0, 1), weight=1)
        self.stat_box(row2, "↑ Uploaded", ni["sent_str"], GREEN).grid(row=0, column=0, sticky="nsew", padx=4)
        self.stat_box(row2, "↓ Downloaded", ni["recv_str"], ACCENT2).grid(row=0, column=1, sticky="nsew", padx=4)
        ctk.CTkLabel(f2, text="", height=6).pack()

        # Live speed
        f3 = self.card(scroll)
        f3.pack(fill="x", pady=6)
        ctk.CTkLabel(f3, text="⚡  Live Speed", font=ctk.CTkFont(size=16, weight="bold"), text_color=YELLOW).pack(anchor="w", padx=14, pady=(12, 6))
        self.live_up = ctk.CTkLabel(f3, text="↑ 0 KB/s", font=ctk.CTkFont(size=18, weight="bold"), text_color=GREEN)
        self.live_up.pack(anchor="w", padx=14, pady=2)
        self.live_down = ctk.CTkLabel(f3, text="↓ 0 KB/s", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT2)
        self.live_down.pack(anchor="w", padx=14, pady=(2, 12))

        # Active connections
        f4 = self.card(scroll)
        f4.pack(fill="x", pady=6)
        ctk.CTkLabel(f4, text="🔗  Active Connections (top 20)", font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT).pack(anchor="w", padx=14, pady=(12, 6))
        try:
            conns = [c for c in psutil.net_connections(kind="inet") if c.status == "ESTABLISHED"][:20]
            for c in conns:
                row = ctk.CTkFrame(f4, fg_color="transparent")
                row.pack(fill="x", padx=14, pady=1)
                local = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "N/A"
                remote = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "N/A"
                ctk.CTkLabel(row, text=f"{local}  →  {remote}", font=ctk.CTkFont(size=11), text_color=FG_DIM).pack(anchor="w")
        except Exception:
            ctk.CTkLabel(f4, text="Need admin rights to view connections", text_color=RED, font=ctk.CTkFont(size=12)).pack(padx=14, pady=6)
        ctk.CTkLabel(f4, text="", height=6).pack()

    # ═══════════════ DISKS ═══════════════
    def build_disks(self):
        scroll = ctk.CTkScrollableFrame(self.content, fg_color=BG_DARK)
        scroll.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(scroll, text="Disks", font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w", pady=(0, 12))

        di = si.disk_info()
        for p in di["partitions"]:
            f = self.card(scroll)
            f.pack(fill="x", pady=6)
            color = RED if p["percent"] > 90 else (YELLOW if p["percent"] > 75 else ACCENT)
            ctk.CTkLabel(f, text=f"💾  {p['device']}  ({p['fstype']})", font=ctk.CTkFont(size=16, weight="bold"), text_color=color).pack(anchor="w", padx=14, pady=(12, 6))
            bar = ctk.CTkProgressBar(f, height=14, corner_radius=7, progress_color=color, fg_color=BG_CARD2)
            bar.set(p["percent"] / 100.0)
            bar.pack(fill="x", padx=14, pady=4)
            row = ctk.CTkFrame(f, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=(2, 10))
            ctk.CTkLabel(row, text=f"Used: {p['used']}", font=ctk.CTkFont(size=13), text_color=FG_DIM).pack(side="left")
            ctk.CTkLabel(row, text=f"Free: {p['free']}", font=ctk.CTkFont(size=13), text_color=FG_DIM).pack(side="left", padx=20)
            ctk.CTkLabel(row, text=f"Total: {p['total']}", font=ctk.CTkFont(size=13), text_color="#FFFFFF").pack(side="left", padx=20)
            ctk.CTkLabel(row, text=f"{p['percent']}%", font=ctk.CTkFont(size=14, weight="bold"), text_color=color).pack(side="right")

        io_f = self.card(scroll)
        io_f.pack(fill="x", pady=6)
        ctk.CTkLabel(io_f, text="Total Disk I/O", font=ctk.CTkFont(size=14, weight="bold"), text_color=ACCENT2).pack(anchor="w", padx=14, pady=(10, 4))
        ctk.CTkLabel(io_f, text=f"Read: {di['read']}   |   Write: {di['write']}", font=ctk.CTkFont(size=13), text_color=FG_DIM).pack(anchor="w", padx=14, pady=(0, 10))

    # ═══════════════ SERVICES ═══════════════
    def build_services(self):
        top = ctk.CTkFrame(self.content, fg_color=BG_DARK)
        top.pack(fill="x", padx=16, pady=(16, 6))
        ctk.CTkLabel(top, text="Services", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")
        self.svc_search = ctk.CTkEntry(top, placeholder_text="Search...", width=200, height=30)
        self.svc_search.pack(side="right", padx=4)
        self.svc_search.bind("<KeyRelease>", lambda e: self.filter_services())

        self.svc_scroll = ctk.CTkScrollableFrame(self.content, fg_color=BG_DARK)
        self.svc_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.all_svcs = si.services_list()
        self.svc_widgets = []
        self.render_services(self.all_svcs)

    def render_services(self, svcs):
        for w in self.svc_widgets:
            w.destroy()
        self.svc_widgets.clear()
        for s in svcs[:100]:
            row = ctk.CTkFrame(self.svc_scroll, fg_color=BG_CARD, corner_radius=6, height=30)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            status_color = GREEN if s["status"] == "running" else FG_DIM
            ctk.CTkLabel(row, text="●", width=20, text_color=status_color, font=ctk.CTkFont(size=14)).pack(side="left", padx=(8, 2))
            ctk.CTkLabel(row, text=s["display_name"][:40], width=300, font=ctk.CTkFont(size=12), text_color="#FFFFFF", anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s["status"], width=80, font=ctk.CTkFont(size=11), text_color=status_color, anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=s.get("start_type", ""), width=80, font=ctk.CTkFont(size=11), text_color=FG_DIM, anchor="w").pack(side="left", padx=4)
            self.svc_widgets.append(row)

    def filter_services(self):
        q = self.svc_search.get().lower()
        filtered = [s for s in self.all_svcs if q in s["display_name"].lower() or q in s["name"].lower()]
        self.render_services(filtered)

    # ═══════════════ STARTUP ═══════════════
    def build_startup(self):
        scroll = ctk.CTkScrollableFrame(self.content, fg_color=BG_DARK)
        scroll.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(scroll, text="Startup Programs", font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w", pady=(0, 12))

        items = si.startup_programs()
        if not items:
            ctk.CTkLabel(scroll, text="No startup programs found.", text_color=FG_DIM).pack(pady=20)
            return
        for item in items:
            f = self.card(scroll)
            f.pack(fill="x", pady=4)
            row = ctk.CTkFrame(f, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=10)
            ctk.CTkLabel(row, text=f"🚀  {item['name']}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#FFFFFF", anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=item["scope"], font=ctk.CTkFont(size=11), text_color=ACCENT, anchor="e").pack(side="right")
            ctk.CTkLabel(f, text=item["command"], font=ctk.CTkFont(size=11), text_color=FG_DIM, wraplength=700, anchor="w").pack(padx=14, pady=(0, 10))

    # ═══════════════ TELEGRAM ═══════════════
    def build_telegram(self):
        scroll = ctk.CTkScrollableFrame(self.content, fg_color=BG_DARK)
        scroll.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(scroll, text="📱 Telegram Integration", font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w", pady=(0, 12))

        f = self.card(scroll)
        f.pack(fill="x", pady=6)
        ctk.CTkLabel(f, text="Configure your Telegram Bot to receive system reports.", text_color=FG_DIM, font=ctk.CTkFont(size=13)).pack(anchor="w", padx=14, pady=(12, 8))

        ctk.CTkLabel(f, text="Bot Token:", text_color=FG_DIM, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=14)
        self.tg_token = ctk.CTkEntry(f, placeholder_text="123456:ABC-...", height=36)
        self.tg_token.pack(fill="x", padx=14, pady=(2, 8))
        if self.telegram.token:
            self.tg_token.insert(0, self.telegram.token)

        ctk.CTkLabel(f, text="Chat ID:", text_color=FG_DIM, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=14)
        self.tg_chat = ctk.CTkEntry(f, placeholder_text="Your chat ID", height=36)
        self.tg_chat.pack(fill="x", padx=14, pady=(2, 8))
        if self.telegram.chat_id:
            self.tg_chat.insert(0, self.telegram.chat_id)

        btn_row = ctk.CTkFrame(f, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(4, 14))
        ctk.CTkButton(btn_row, text="💾  Save Config", height=36, fg_color=ACCENT, text_color="#000000",
                       command=self.save_tg).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="📤  Send Report Now", height=36, fg_color=ACCENT2, text_color="#000000",
                       command=self.send_tg_report).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="🧪  Test Message", height=36, fg_color=YELLOW, text_color="#000000",
                       command=self.test_tg).pack(side="left")

        self.tg_status = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=13), text_color=GREEN)
        self.tg_status.pack(anchor="w", pady=6)

        # Guide
        g = self.card(scroll)
        g.pack(fill="x", pady=6)
        ctk.CTkLabel(g, text="📖  How to get Bot Token & Chat ID", font=ctk.CTkFont(size=14, weight="bold"), text_color=YELLOW).pack(anchor="w", padx=14, pady=(12, 6))
        guide = (
            "1. Open Telegram → search @BotFather → /newbot → copy the token\n"
            "2. Send a message to your bot\n"
            "3. Open: https://api.telegram.org/bot<TOKEN>/getUpdates\n"
            "4. Find your chat id in the response"
        )
        ctk.CTkLabel(g, text=guide, font=ctk.CTkFont(size=12), text_color=FG_DIM, justify="left", wraplength=600).pack(anchor="w", padx=14, pady=(0, 12))

    def save_tg(self):
        self.save_config(self.tg_token.get(), self.tg_chat.get())
        self.tg_status.configure(text="✓ Config saved!", text_color=GREEN)

    def test_tg(self):
        self.save_config(self.tg_token.get(), self.tg_chat.get())
        self.tg_status.configure(text="Sending...", text_color=YELLOW)
        def cb(ok, msg):
            self.after(0, lambda: self.tg_status.configure(text=msg, text_color=GREEN if ok else RED))
        self.telegram.send_message("🧪 <b>SysControl Test</b>\n\nConnection successful!", cb)

    def send_tg_report(self):
        self.save_config(self.tg_token.get(), self.tg_chat.get())
        self.tg_status.configure(text="Generating report...", text_color=YELLOW)
        def _gen():
            report = si.full_report()
            def cb(ok, msg):
                self.after(0, lambda: self.tg_status.configure(text=msg, text_color=GREEN if ok else RED))
            self.telegram.send_report(report, cb)
        threading.Thread(target=_gen, daemon=True).start()

    # ═══════════════ POWER ═══════════════
    def build_power(self):
        scroll = ctk.CTkScrollableFrame(self.content, fg_color=BG_DARK)
        scroll.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(scroll, text="⚙️  Power & System Control", font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w", pady=(0, 12))

        bat = si.battery_info()
        if bat:
            f = self.card(scroll)
            f.pack(fill="x", pady=6)
            plug = "⚡ Plugged In" if bat["plugged"] else "🔋 On Battery"
            color = GREEN if bat["plugged"] else YELLOW
            ctk.CTkLabel(f, text=f"Battery: {bat['percent']}%  —  {plug}",
                          font=ctk.CTkFont(size=16, weight="bold"), text_color=color).pack(padx=14, pady=(12, 4))
            bar = ctk.CTkProgressBar(f, height=14, corner_radius=7, progress_color=color, fg_color=BG_CARD2)
            bar.set(bat["percent"] / 100.0)
            bar.pack(fill="x", padx=14, pady=(4, 12))

        f = self.card(scroll)
        f.pack(fill="x", pady=6)
        ctk.CTkLabel(f, text="⚠️  System Actions", font=ctk.CTkFont(size=16, weight="bold"), text_color=RED).pack(anchor="w", padx=14, pady=(12, 10))
        actions = [
            ("🔄  Restart Explorer", lambda: self.run_cmd("taskkill /f /im explorer.exe && start explorer.exe")),
            ("🧹  Clear Temp Files", lambda: self.run_cmd("del /q/f/s %TEMP%\\* >nul 2>&1")),
            ("📋  Flush DNS", lambda: self.run_cmd("ipconfig /flushdns")),
            ("💤  Lock Screen", lambda: self.run_cmd("rundll32.exe user32.dll,LockWorkStation")),
            ("😴  Sleep", lambda: self.run_cmd("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")),
            ("♻️  Restart PC", lambda: self.confirm_action("Restart", "shutdown /r /t 5")),
            ("⏹  Shutdown PC", lambda: self.confirm_action("Shutdown", "shutdown /s /t 5")),
        ]
        for text, cmd in actions:
            btn = ctk.CTkButton(f, text=text, anchor="w", height=36, fg_color=BG_CARD2,
                                 hover_color="#2C2C3E", text_color="#FFFFFF",
                                 font=ctk.CTkFont(size=14), command=cmd)
            btn.pack(fill="x", padx=14, pady=3)
        ctk.CTkLabel(f, text="", height=10).pack()

        self.power_log = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=12), text_color=GREEN)
        self.power_log.pack(anchor="w", pady=4)

    def run_cmd(self, cmd):
        try:
            subprocess.Popen(cmd, shell=True)
            self.power_log.configure(text=f"✓ Executed: {cmd[:50]}...")
        except Exception as e:
            self.power_log.configure(text=f"✗ Error: {e}", text_color=RED)

    def confirm_action(self, name, cmd):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Confirm {name}")
        dialog.geometry("360x150")
        dialog.configure(fg_color=BG_DARK)
        dialog.transient(self)
        dialog.grab_set()
        ctk.CTkLabel(dialog, text=f"Are you sure you want to {name}?",
                      font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(24, 16))
        row = ctk.CTkFrame(dialog, fg_color="transparent")
        row.pack()
        ctk.CTkButton(row, text="Cancel", width=100, fg_color=FG_DIM, text_color="#000000",
                       command=dialog.destroy).pack(side="left", padx=8)
        ctk.CTkButton(row, text=f"Yes, {name}", width=120, fg_color=RED, text_color="#FFFFFF",
                       command=lambda: [dialog.destroy(), self.run_cmd(cmd)]).pack(side="left", padx=8)

    # ─── MONITORING THREAD ──────────────────
    def start_monitoring(self):
        def _loop():
            import psutil as ps
            self.prev_sent, self.prev_recv = si.net_speed()
            while self.running:
                time.sleep(2)
                try:
                    if self.current_tab == "dashboard":
                        cpu_pct = ps.cpu_percent(interval=0)
                        ram = ps.virtual_memory()
                        gpus = si.gpu_info()
                        gpu_pct = gpus[0]["usage"] if gpus else 0
                        cores = ps.cpu_percent(percpu=True, interval=0)
                        sent, recv = si.net_speed()
                        up_speed = (sent - self.prev_sent) / 2
                        dn_speed = (recv - self.prev_recv) / 2
                        self.prev_sent, self.prev_recv = sent, recv
                        self.after(0, lambda cp=cpu_pct, rp=ram.percent, gp=gpu_pct, us=up_speed, ds=dn_speed, cr=cores:
                                   self.update_dashboard(cp, rp, gp, us, ds, cr))
                    elif self.current_tab == "network":
                        sent, recv = si.net_speed()
                        up_speed = (sent - self.prev_sent) / 2
                        dn_speed = (recv - self.prev_recv) / 2
                        self.prev_sent, self.prev_recv = sent, recv
                        self.after(0, lambda us=up_speed, ds=dn_speed: self.update_net_speed(us, ds))
                except Exception:
                    pass
        t = threading.Thread(target=_loop, daemon=True)
        t.start()

    def update_dashboard(self, cpu, ram, gpu, up, dn, cores):
        try:
            self.cpu_bar.set(cpu / 100.0)
            self.cpu_val.configure(text=f"{cpu:.1f}%")
            self.ram_bar.set(ram / 100.0)
            self.ram_val.configure(text=f"{ram:.1f}%")
            self.gpu_bar.set(gpu / 100.0)
            self.gpu_val.configure(text=f"{gpu:.1f}%")
            self.net_up_lbl.configure(text=f"↑ {si.get_size(up)}/s   ↓ {si.get_size(dn)}/s")
            for i, (bar, lbl) in enumerate(self.core_bars):
                if i < len(cores):
                    bar.set(cores[i] / 100.0)
                    lbl.configure(text=f"{cores[i]:.0f}%")
        except Exception:
            pass

    def update_net_speed(self, up, dn):
        try:
            self.live_up.configure(text=f"↑ {si.get_size(up)}/s")
            self.live_down.configure(text=f"↓ {si.get_size(dn)}/s")
        except Exception:
            pass

    def on_close(self):
        self.running = False
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
