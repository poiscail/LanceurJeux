"""Lanceur de jeux unifié : Steam, Epic, jeux ajoutés à la main. Temps de jeu par jeu."""
import ctypes, glob, json, os, re, threading, time, tkinter as tk
from ctypes import wintypes
from tkinter import filedialog

DATA = os.path.join(os.environ.get("APPDATA", "."), "LanceurJeux", "data.json")
IGNORE = ("Steamworks Common", "Steam Linux Runtime", "Proton")


def kv(text, key):
    m = re.search(r'"%s"\s+"([^"]*)"' % key, text)
    return m.group(1) if m else ""


def steam_root():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
            return os.path.normpath(winreg.QueryValueEx(k, "SteamPath")[0])
    except OSError:
        return None


def scan_steam(root):
    if not root:
        return []
    libs = {root}
    try:
        vdf = open(os.path.join(root, "steamapps", "libraryfolders.vdf"), encoding="utf-8").read()
        libs |= {os.path.normpath(p.replace("\\\\", "\\")) for p in re.findall(r'"path"\s+"([^"]*)"', vdf)}
    except OSError:
        pass
    games = []
    for lib in {os.path.normcase(l): l for l in libs}.values():
        for f in glob.glob(os.path.join(lib, "steamapps", "appmanifest_*.acf")):
            t = open(f, encoding="utf-8", errors="ignore").read()
            name, appid, d = kv(t, "name"), kv(t, "appid"), kv(t, "installdir")
            if not name or name.startswith(IGNORE):
                continue
            cover = os.path.join(root, "appcache", "librarycache", appid, "library_600x900.jpg")
            games.append({"id": "steam:" + appid, "name": name, "cmd": "steam://rungameid/" + appid,
                          "dir": os.path.join(lib, "steamapps", "common", d), "cover": cover})
    return games


def scan_epic(manifests=os.path.expandvars(r"%ProgramData%\Epic\EpicGamesLauncher\Data\Manifests")):
    games = []
    for f in glob.glob(os.path.join(manifests, "*.item")):
        try:
            j = json.load(open(f, encoding="utf-8"))
            uri = "com.epicgames.launcher://apps/%s%%3A%s%%3A%s?action=launch&silent=true" % (
                j["CatalogNamespace"], j["CatalogItemId"], j["AppName"])
            games.append({"id": "epic:" + j["AppName"], "name": j["DisplayName"], "cmd": uri,
                          "dir": j["InstallLocation"], "cover": ""})
        except (OSError, KeyError, ValueError):
            pass
    return games


def fmt(sec):
    h, m = divmod(int(sec) // 60, 60)
    return f"{h} h {m:02d} min" if h else f"{m} min"


def running_in(folder):
    """Vrai si un processus tourne depuis ce dossier."""
    k = ctypes.windll.kernel32
    k.OpenProcess.restype = wintypes.HANDLE
    pids = (wintypes.DWORD * 4096)()
    n = wintypes.DWORD()
    ctypes.windll.psapi.EnumProcesses(pids, ctypes.sizeof(pids), ctypes.byref(n))
    folder = os.path.normcase(os.path.normpath(folder)) + os.sep
    buf = ctypes.create_unicode_buffer(1024)
    for pid in pids[: n.value // 4]:
        h = k.OpenProcess(0x1000, False, pid)
        if h:
            sz = wintypes.DWORD(1024)
            ok = k.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(sz))
            k.CloseHandle(h)
            if ok and os.path.normcase(buf.value).startswith(folder):
                return True
    return False


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lanceur de jeux")
        self.geometry("1000x700")
        self.configure(bg="#14161a")
        try:
            self.save = json.load(open(DATA, encoding="utf-8"))
        except (OSError, ValueError):
            self.save = {"manual": [], "time": {}}
        bar = tk.Frame(self, bg="#14161a")
        bar.pack(fill="x", padx=12, pady=8)
        for txt, cmd in (("Actualiser", self.refresh), ("Ajouter un jeu (.exe)", self.add)):
            tk.Button(bar, text=txt, command=cmd, bg="#2a2f3a", fg="white", relief="flat", padx=10).pack(side="left", padx=4)
        self.cv = tk.Canvas(self, bg="#14161a", highlightthickness=0)
        self.cv.pack(fill="both", expand=True)
        self.grid_f = tk.Frame(self.cv, bg="#14161a")
        self.cv.create_window(0, 0, window=self.grid_f, anchor="nw")
        self.bind_all("<MouseWheel>", lambda e: self.cv.yview_scroll(-e.delta // 120, "units"))
        self.imgs = []
        self.refresh()

    def persist(self):
        os.makedirs(os.path.dirname(DATA), exist_ok=True)
        json.dump(self.save, open(DATA, "w", encoding="utf-8"))

    def games(self):
        g = scan_steam(steam_root()) + scan_epic()
        for p in self.save["manual"]:
            g.append({"id": "man:" + p, "name": os.path.splitext(os.path.basename(p))[0], "cmd": p,
                      "dir": os.path.dirname(p), "cover": ""})
        return sorted(g, key=lambda x: x["name"].lower())

    def refresh(self):
        from PIL import Image, ImageTk
        for w in self.grid_f.winfo_children():
            w.destroy()
        self.imgs = []
        cols = 5
        for i, g in enumerate(self.games()):
            try:
                im = Image.open(g["cover"]).resize((150, 225))
            except (OSError, ValueError):
                im = Image.new("RGB", (150, 225), "#2a2f3a")
            ph = ImageTk.PhotoImage(im)
            self.imgs.append(ph)
            f = tk.Frame(self.grid_f, bg="#14161a", cursor="hand2")
            f.grid(row=i // cols, column=i % cols, padx=8, pady=8)
            lbl = tk.Label(f, image=ph, bg="#14161a")
            name = tk.Label(f, text=g["name"], fg="white", bg="#14161a", wraplength=150)
            t = tk.Label(f, text=fmt(self.save["time"].get(g["id"], 0)), fg="#8a93a6", bg="#14161a")
            g["label"] = t
            for w in (f, lbl, name, t):
                w.bind("<Button-1>", lambda e, g=g: self.launch(g))
            lbl.pack()
            name.pack()
            t.pack()
        self.grid_f.update_idletasks()
        self.cv.configure(scrollregion=(0, 0, self.grid_f.winfo_reqwidth(), self.grid_f.winfo_reqheight()))

    def add(self):
        p = filedialog.askopenfilename(filetypes=[("Programme", "*.exe")])
        if p and os.path.normpath(p) not in self.save["manual"]:
            self.save["manual"].append(os.path.normpath(p))
            self.persist()
            self.refresh()

    def launch(self, g):
        os.startfile(g["cmd"])
        threading.Thread(target=self.track, args=(g,), daemon=True).start()

    def track(self, g):
        for _ in range(60):  # attend jusqu'à 60 s que le jeu démarre
            if running_in(g["dir"]):
                break
            time.sleep(1)
        else:
            return
        while running_in(g["dir"]):
            time.sleep(5)
            self.save["time"][g["id"]] = self.save["time"].get(g["id"], 0) + 5
            self.persist()
            self.after(0, lambda: g["label"].configure(text=fmt(self.save["time"][g["id"]])))


if __name__ == "__main__":
    App().mainloop()
