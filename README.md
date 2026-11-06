# LanceurJeux

Lanceur de jeux unifié pour Windows : détecte les jeux Steam et Epic Games, accepte des jeux ajoutés à la main (.exe, émulateurs…), les affiche avec leur jaquette (Steam) et enregistre le temps de jeu de chacun.

## Utilisation

Prérequis : Python 3 et Pillow (`pip install pillow`).

Double-clic sur `Lancer.bat` (ou `python lanceur.py`).

- Clic sur un jeu : il se lance et son temps de jeu est compté.
- **Ajouter un jeu (.exe)** : ajoute un jeu ou un émulateur à la main.
- **Actualiser** : relit les bibliothèques Steam et Epic.

Les données (jeux ajoutés, temps de jeu) sont dans `%APPDATA%\LanceurJeux\data.json`.

## Test

```
python test_lanceur.py
```
