import json, os, shutil, subprocess, sys, tempfile, time
import lanceur

d = tempfile.mkdtemp()

# Epic
json.dump({"CatalogNamespace": "ns", "CatalogItemId": "ci", "AppName": "app", "DisplayName": "Jeu", "InstallLocation": d},
          open(os.path.join(d, "a.item"), "w"))
g = lanceur.scan_epic(d)
assert g[0]["name"] == "Jeu" and "ns%3Aci%3Aapp" in g[0]["cmd"]

# Format du temps
assert lanceur.fmt(0) == "Jamais lancé" and lanceur.fmt(30) == "< 1 min"
assert lanceur.fmt(3900) == "1 h 05 min" and lanceur.fmt(120) == "2 min"

# Jaquettes : portrait préféré, y compris dans les sous-dossiers hachés
root = os.path.join(d, "steam"); lc = os.path.join(root, "appcache", "librarycache", "7")
os.makedirs(os.path.join(lc, "aaa")); os.makedirs(os.path.join(lc, "bbb"))
for p in ("aaa/library_header.jpg", "bbb/library_600x900.jpg"):
    open(os.path.join(lc, p), "w").close()
assert lanceur.find_cover(root, "7").endswith("library_600x900.jpg") and lanceur.find_cover(root, "8") == ""

# Steam réel de ce PC
steam = lanceur.scan_steam(lanceur.steam_root())
assert steam and not any(x["name"].startswith(lanceur.IGNORE) for x in steam)
assert len({x["id"] for x in steam}) == len(steam)  # pas de doublons

# Vrai lancement d'un jeu : un exe copié dans un dossier à lui, temps compté, jeu terminé -> arrêt
game = os.path.join(d, "jeu"); os.makedirs(game)
exe = os.path.join(game, "faux_jeu.exe"); shutil.copy(r"C:\Windows\System32\ping.exe", exe)
assert not lanceur.running_in(game)
subprocess.Popen([exe, "-n", "7", "127.0.0.1"], stdout=subprocess.DEVNULL)  # ~6 s
total = []
t0 = time.time(); lanceur.watch(game, total.append, wait=10, step=1); dt = time.time() - t0
assert 3 < sum(total) <= dt + 1, (sum(total), dt)
assert not lanceur.running_in(game)

# Jeu jamais démarré : watch abandonne sans rien compter
t0 = time.time(); lanceur.watch(game, total.append, wait=2, step=1)
assert time.time() - t0 < 5 and len(total) < 20

# Jeu ajouté à la main
m = lanceur.manual_game(exe)
assert m["name"] == "faux_jeu" and m["dir"] == game and m["id"] == "man:" + exe

# FiveM : détecté avec "Steam d'abord"
fv = lanceur.scan_fivem(exe)
assert fv[0]["name"] == "FiveM" and fv[0]["steam"] and lanceur.scan_fivem(os.path.join(d, "nope.exe")) == []

# Steam d'abord : déjà prêt -> rien lancé ; sinon lancé une fois puis attente du chargement complet
started = []
assert lanceur.ensure_steam(ready=lambda: True, start=lambda: started.append(1)) and not started
calls = iter([False, False, False, True])
assert lanceur.ensure_steam(ready=lambda: next(calls), start=lambda: started.append(1), step=0.01) and started == [1]
assert not lanceur.ensure_steam(ready=lambda: False, start=lambda: None, timeout=0.2, step=0.05)
assert isinstance(lanceur.steam_ready(), bool)

# Interface : s'ouvre, affiche les jeux, recherche et lancement protégé
lanceur.DATA = os.path.join(d, "data.json")
app = lanceur.App(); app.update()
assert len(app.cards) == len(app.all) >= len(steam)
app.q.set("zzzz-introuvable"); app.update(); assert not app.cards
app.q.set(""); app.update(); assert len(app.cards) == len(app.all)
sv = {"time": {"a": 5, "b": 90}, "last": {"a": 200, "b": 100}}
gs = [{"id": "a", "name": "Zed"}, {"id": "b", "name": "Alpha"}, {"id": "c", "name": "Beta"}]
assert [x["id"] for x in lanceur.sort_games(gs, "Nom", sv)] == ["b", "c", "a"]
assert [x["id"] for x in lanceur.sort_games(gs, "Plus joués", sv)] == ["b", "a", "c"]
assert [x["id"] for x in lanceur.sort_games(gs, "Récents", sv)] == ["a", "b", "c"]
app.cycle_sort(); app.update(); assert len(app.cards) == len(app.all)
app.destroy()
print("OK", [x["name"] for x in steam])
