# LanceurJeux

Lanceur de jeux unifié pour Windows : détecte les jeux Steam et Epic Games, accepte des jeux ajoutés à la main (.exe, émulateurs…), les affiche avec leur jaquette dans une interface sombre et enregistre le temps de jeu de chacun.

## Utilisation

Double-cliquer sur `LanceurJeux.exe` (rien à installer). Depuis le code : `pip install pillow` puis `Lancer.bat`.

- Clic sur un jeu : il se lance, son temps de jeu est compté (« ● En cours » pendant la partie).
- Recherche en haut ; **Tri** : nom, plus joués, récents ; **+ Ajouter** : ajoute un jeu ou émulateur (.exe) ; **⟳** : relit Steam et Epic ; **F11** : plein écran.
- Clic droit : ouvrir le dossier, retirer un jeu ajouté à la main, ou cocher « Lancer Steam d'abord » (FiveM le fait par défaut : Steam démarre, la fenêtre attend qu'il soit chargé, puis le jeu se lance).

Données (jeux ajoutés, temps de jeu) : `%APPDATA%\LanceurJeux\data.json`.

## Test

```
python test_lanceur.py
```
