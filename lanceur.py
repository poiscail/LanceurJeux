"""Lanceur de jeux unifié : Steam, Epic, jeux ajoutés à la main. Temps de jeu par jeu."""
import ctypes, glob, json, os, re, sys, threading, time, tkinter as tk
from ctypes import wintypes
from tkinter import filedialog

DATA = os.path.join(os.environ.get("APPDATA", "."), "LanceurJeux", "data.json")
IGNORE = ("Steamworks Common", "Steam Linux Runtime", "Proton")
COVERS = ("library_600x900*.jpg", "library_capsule*.jpg", "library_header*.jpg")  # par ordre de préférence
BG, CARD, HOVER, TEXT, MUTED, ACCENT, GREEN = "#0f1115", "#181b22", "#232836", "#e8eaf0", "#8a93a6", "#4c8dff", "#3ddc84"
CW, CH = 160, 240
WAIT, STEP = 180, 5  # attente du démarrage d'un jeu (s) / pas de comptage du temps (s)
SORTS = ("Nom", "Plus joués", "Récents")


def sort_games(games, mode, save):
    t, last = save["time"], save["last"]
    key = {"Nom": lambda g: g["name"].lower(), "Plus joués": lambda g: -t.get(g["id"], 0),
           "Récents": lambda g: -last.get(g["id"], 0)}[mode]
    return sorted(games, key=lambda g: (key(g), g["name"].lower()))


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


def find_cover(root, appid):
    base = os.path.join(root, "appcache", "librarycache", appid)
    for pat in COVERS:
        hits = glob.glob(os.path.join(base, "**", pat), recursive=True)
        if hits:
            return hits[0]
    return ""


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
            if not name or not d or name.startswith(IGNORE):
                continue
            games.append({"id": "steam:" + appid, "name": name, "cmd": "steam://rungameid/" + appid,
                          "dir": os.path.join(lib, "steamapps", "common", d), "cover": find_cover(root, appid)})
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


def scan_fivem(path=os.path.expandvars(r"%LOCALAPPDATA%\FiveM\FiveM.exe")):
    """FiveM n'a pas de manifeste : on le cherche à son emplacement habituel. Il a besoin de Steam (GTA V)."""
    g = manual_game(path) if os.path.isfile(path) else None
    return [dict(g, id="fivem", name="FiveM", steam=True)] if g else []


def steam_ready():
    """Steam est lancé ET entièrement chargé (connecté) : le pid enregistré est bien celui de steam.exe."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam\ActiveProcess") as k:
            pid, user = winreg.QueryValueEx(k, "pid")[0], winreg.QueryValueEx(k, "ActiveUser")[0]
    except OSError:
        return False
    kern = ctypes.windll.kernel32
    kern.OpenProcess.restype = wintypes.HANDLE
    h = kern.OpenProcess(0x1000, False, pid)
    if not h:
        return False  # pid périmé : Steam est fermé
    buf, sz = ctypes.create_unicode_buffer(1024), wintypes.DWORD(1024)
    ok = kern.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(sz))
    kern.CloseHandle(h)
    return bool(user) and bool(ok) and os.path.basename(buf.value).lower() == "steam.exe"


def ensure_steam(ready=steam_ready, start=None, timeout=240, step=1):
    """Lance Steam s'il n'est pas prêt et attend son chargement complet. Renvoie False si trop long."""
    if ready():
        return True
    (start or (lambda: os.startfile("steam://open/main")))()
    t0 = time.time()
    while not ready():
        if time.time() - t0 > timeout:
            return False
        time.sleep(step)
    return True


def manual_game(path):
    return {"id": "man:" + path, "name": os.path.splitext(os.path.basename(path))[0], "cmd": path,
            "dir": os.path.dirname(path), "cover": ""}


def fmt(sec):
    h, m = divmod(int(sec) // 60, 60)
    return f"{h} h {m:02d} min" if h else (f"{m} min" if m else ("< 1 min" if sec else "Jamais lancé"))


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


def watch(folder, add, wait=180, step=5, on_start=None):
    """Attend que le jeu démarre (max `wait` s), puis appelle add(secondes) tant qu'il tourne."""
    t0 = time.time()
    while not running_in(folder):
        if time.time() - t0 > wait:
            return
        time.sleep(1)
    if on_start:
        on_start()
    last = time.time()
    while running_in(folder):
        time.sleep(step)
        now = time.time()
        add(now - last)
        last = now


def placeholder(name):
    from PIL import Image, ImageDraw, ImageFont
    h = sum(map(ord, name)) % 360
    im = Image.new("RGB", (CW, CH), "#20242e")
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("segoeuib.ttf", 72)
    except OSError:
        font = ImageFont.load_default()
    d.text((CW / 2, CH / 2), name[:1].upper(), fill=f"hsl({h},45%,55%)", font=font, anchor="mm")
    return im


def load_cover(g):
    from PIL import Image, ImageOps
    try:
        return ImageOps.fit(Image.open(g["cover"]).convert("RGB"), (CW, CH))  # recadre sans déformer
    except (OSError, ValueError):
        return placeholder(g["name"])


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lanceur de jeux")
        try:
            self.iconbitmap(os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "icone.ico"))
        except tk.TclError:
            pass
        self.geometry("1050x720")
        self.minsize(520, 400)
        self.configure(bg=BG)
        try:
            self.save = json.load(open(DATA, encoding="utf-8"))
        except (OSError, ValueError):
            self.save = {}
        if not isinstance(self.save, dict):
            self.save = {}
        self.save.setdefault("manual", [])
        self.save.setdefault("time", {})
        self.save.setdefault("last", {})
        self.save.setdefault("steam_first", {})
        self.sort = 0
        self.status = {}
        self.playing, self.cards, self.frames, self.photos, self.all, self.shown, self.cols = set(), {}, {}, {}, [], [], 0
        self.lock = threading.RLock()

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(top, text="Mes jeux", fg=TEXT, bg=BG, font=("Segoe UI Semibold", 20)).pack(side="left")
        self.count = tk.Label(top, fg=MUTED, bg=BG, font=("Segoe UI", 10))
        self.count.pack(side="left", padx=12, pady=(8, 0))
        self.sortbtn = None
        for txt, cmd in (("⟳", self.refresh), ("+ Ajouter", self.add), ("Tri : Nom", self.cycle_sort)):
            b = tk.Button(top, text=txt, command=cmd, bg=CARD, fg=TEXT, activebackground=HOVER, activeforeground=TEXT,
                      relief="flat", bd=0, padx=14, pady=6, font=("Segoe UI", 10), cursor="hand2")
            b.pack(side="right", padx=(8, 0))
            self.sortbtn = b if txt.startswith("Tri") else self.sortbtn
        self.q = tk.StringVar()
        self.q.trace_add("write", lambda *a: self.layout())
        tk.Entry(top, textvariable=self.q, bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat",
                 font=("Segoe UI", 11), width=22).pack(side="right", ipady=6, padx=8)

        wrap = tk.Frame(self, bg=BG)
        wrap.pack(fill="both", expand=True, padx=(24, 8))
        self.cv = tk.Canvas(wrap, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(wrap, command=self.cv.yview)
        self.cv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.cv.pack(side="left", fill="both", expand=True)
        self.grid_f = tk.Frame(self.cv, bg=BG)
        self.cv.create_window(0, 0, window=self.grid_f, anchor="nw")
        self.cv.bind("<Configure>", lambda e: self.layout(keep=True))
        self.bind_all("<MouseWheel>", lambda e: self.cv.yview_scroll(-e.delta // 120 * 2, "units"))
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        self.menu = tk.Menu(self, tearoff=0)
        self.refresh()
        self.tick()

    # --- données ---
    def persist(self):
        with self.lock:
            os.makedirs(os.path.dirname(DATA), exist_ok=True)
            tmp = DATA + ".tmp"
            json.dump(self.save, open(tmp, "w", encoding="utf-8"))
            os.replace(tmp, DATA)  # écriture atomique : pas de fichier corrompu si on ferme en plein milieu

    def add_time(self, gid, sec):
        with self.lock:  # un thread de comptage par jeu : on protège la sauvegarde
            self.save["time"][gid] = self.save["time"].get(gid, 0) + sec
            self.persist()

    def refresh(self):
        from PIL import ImageTk
        self.all = scan_steam(steam_root()) + scan_epic() + scan_fivem() + [manual_game(p) for p in self.save["manual"]]
        for c in self.grid_f.winfo_children():
            c.destroy()
        self.cards, self.frames, self.photos = {}, {}, {}
        for g in self.all:  # les cartes sont créées une fois ; recherche et tri ne font que les replacer
            self.photos[g["id"]] = ImageTk.PhotoImage(load_cover(g))
            f = tk.Frame(self.grid_f, bg=CARD, cursor="hand2", padx=8, pady=8)
            img = tk.Label(f, image=self.photos[g["id"]], bg=CARD)
            name = tk.Label(f, text=g["name"], fg=TEXT, bg=CARD, wraplength=CW, justify="left", anchor="w",
                            font=("Segoe UI Semibold", 10), height=2)
            t = tk.Label(f, fg=MUTED, bg=CARD, font=("Segoe UI", 9), anchor="w")
            for lbl in (img, name, t):
                lbl.pack(fill="x", pady=(0, 2))
            widgets = (f, img, name, t)
            for wd in widgets:
                wd.bind("<Button-1>", lambda e, g=g: self.launch(g))
                wd.bind("<Button-3>", lambda e, g=g: self.context(e, g))
                wd.bind("<Enter>", lambda e, ws=widgets: [x.configure(bg=HOVER) for x in ws])
                wd.bind("<Leave>", lambda e, ws=widgets: [x.configure(bg=CARD) for x in ws])
            self.frames[g["id"]], self.cards[g["id"]] = f, t
        self.layout()

    # --- affichage ---
    def layout(self, keep=False):
        """Place les cartes selon recherche, tri et largeur. keep=True : rien à faire si les colonnes n'ont pas changé."""
        cols = max(1, self.cv.winfo_width() // (CW + 24))
        if keep and cols == self.cols:
            return
        self.cols = cols
        q = self.q.get().lower()
        self.shown = [g for g in sort_games(self.all, SORTS[self.sort], self.save) if q in g["name"].lower()]
        for f in self.frames.values():
            f.grid_forget()
        for i, g in enumerate(self.shown):
            self.frames[g["id"]].grid(row=i // cols, column=i % cols, padx=8, pady=8, sticky="n")
        self.count.configure(text=f"{len(self.shown)} jeu{'x' if len(self.shown) > 1 else ''}")
        self.grid_f.update_idletasks()
        self.cv.configure(scrollregion=(0, 0, self.grid_f.winfo_reqwidth(), self.grid_f.winfo_reqheight()))
        self.tick(once=True)

    def tick(self, once=False):
        for gid, t in self.cards.items():
            if gid in self.status:
                t.configure(text=self.status[gid], fg=ACCENT)
            elif gid in self.playing:
                t.configure(text="● En cours · " + fmt(self.save["time"].get(gid, 0)), fg=GREEN)
            else:
                t.configure(text=fmt(self.save["time"].get(gid, 0)), fg=MUTED)
        if not once:
            self.after(2000, self.tick)

    def cycle_sort(self):
        self.sort = (self.sort + 1) % len(SORTS)
        self.sortbtn.configure(text="Tri : " + SORTS[self.sort])
        self.layout()

    def toggle_fullscreen(self, _=None):
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))  # mode plein écran / canapé

    def context(self, e, g):
        self.menu.delete(0, "end")
        self.menu.add_command(label="Ouvrir le dossier", command=lambda: os.path.isdir(g["dir"]) and os.startfile(g["dir"]))
        if not g["id"].startswith(("steam:", "epic:")):
            on = self.save["steam_first"].get(g["id"], g.get("steam", False))
            self.menu.add_command(label=("✓ " if on else "") + "Lancer Steam d'abord",
                                  command=lambda: self.toggle_steam(g, on))
        if g["id"].startswith("man:"):
            self.menu.add_command(label="Retirer de la liste", command=lambda: self.remove(g))
        self.menu.tk_popup(e.x_root, e.y_root)

    # --- actions ---
    def add(self):
        p = filedialog.askopenfilename(filetypes=[("Programme", "*.exe")])
        p = os.path.normpath(p) if p else ""
        if p and p not in self.save["manual"]:
            with self.lock:
                self.save["manual"].append(p)
                self.persist()
            self.refresh()

    def toggle_steam(self, g, on):
        with self.lock:
            self.save["steam_first"][g["id"]] = not on
            self.persist()

    def remove(self, g):
        with self.lock:
            self.save["manual"].remove(g["cmd"])
            self.persist()
        self.refresh()

    def flash(self, gid, text):
        self.status[gid] = text
        time.sleep(4)
        self.status.pop(gid, None)

    def launch(self, g):
        gid = g["id"]
        if gid in self.playing:  # évite de compter deux fois le même jeu
            return
        with self.lock:
            self.save["last"][gid] = time.time()
        self.playing.add(gid)

        def run():
            try:
                if self.save["steam_first"].get(gid, g.get("steam", False)):
                    self.status[gid] = "Démarrage de Steam…"
                    try:
                        ok = ensure_steam()
                    except OSError:
                        ok = False
                    self.status.pop(gid, None)
                    if not ok:
                        return self.flash(gid, "Steam n'a pas démarré")
                self.status[gid] = "Lancement…"
                try:
                    os.startfile(g["cmd"], cwd=g["dir"]) if gid.startswith(("man:", "fivem")) else os.startfile(g["cmd"])
                except OSError:
                    return self.flash(gid, "Lancement impossible")
                watch(g["dir"], lambda s: self.add_time(gid, s), wait=WAIT, step=STEP,
                      on_start=lambda: self.status.pop(gid, None))
            finally:  # quoi qu'il arrive, la carte redevient cliquable
                self.status.pop(gid, None)
                self.playing.discard(gid)

        threading.Thread(target=run, daemon=True).start()
        self.tick(once=True)


if __name__ == "__main__":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # texte net sur écrans haute résolution
    except OSError:
        pass
    App().mainloop()
