# fiches-v7-outils

Scripts de contrôle des portraits anniversaire-celebrite.com (charte v7m).
Téléchargés à chaque session pour éviter de les recopier, ce qui coûte des tokens.

- `lint_portrait.py` : contrôle de la fiche de travail `<slug>.json` (charte v7m, modes personne et fiction).
- `lint.py` : contrôle du fichier d'import CMS `<slug>.md` (compétence « 5 brouillons »).
- `render_import.py` : produit `<slug>.md` à partir de `<slug>.json`, puis lance les deux linters.

Téléchargement :

    for f in lint_portrait.py lint.py render_import.py; do curl -fsSO https://raw.githubusercontent.com/agolg/fiches-v7-outils/main/$f || echo "ECHEC $f"; done

Toute modification d'un linter se fait ici : c'est la version de référence.
