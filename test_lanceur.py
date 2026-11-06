import json, os, sys, tempfile
import lanceur

d = tempfile.mkdtemp()
json.dump({"CatalogNamespace": "ns", "CatalogItemId": "ci", "AppName": "app", "DisplayName": "Jeu", "InstallLocation": d},
          open(os.path.join(d, "a.item"), "w"))
g = lanceur.scan_epic(d)
assert g[0]["name"] == "Jeu" and "ns%3Aci%3Aapp" in g[0]["cmd"]
assert lanceur.fmt(3900) == "1 h 05 min" and lanceur.fmt(120) == "2 min"
steam = lanceur.scan_steam(lanceur.steam_root())
assert steam and not any(x["name"].startswith(lanceur.IGNORE) for x in steam)
assert lanceur.running_in(os.path.dirname(sys.executable))  # python tourne depuis son dossier
print("OK", [x["name"] for x in steam])
