# fiches-v7-outils

Scripts de contrôle des portraits
Téléchargés à chaque session pour éviter de les recopier, ce qui coûte des tokens.

- `lint_portrait.py` : contrôle de la fiche de travail `<slug>.json` (charte v7m, modes personne et fiction).
- `lint.py` : contrôle du fichier d'import CMS `<slug>.md` (compétence « 5 brouillons »).
- `render_import.py` : produit `<slug>.md` à partir de `<slug>.json`, puis lance les deux linters.
- `SPEC.md` : charte v7m pour les sous-agents (recherche, fiabilité, rédaction, structure). Dérivée des instructions du projet « Fiches V7 », sans la livraison manuelle, avec les adaptations d'import.
- `FICTION.md` : complément pour les personnages de fiction, dérivé de `mode-fiction-v7m.md`.

Téléchargement :

    for f in lint_portrait.py lint.py render_import.py SPEC.md FICTION.md; do curl -fsSO https://raw.githubusercontent.com/agolg/fiches-v7-outils/main/$f || echo "ECHEC $f"; done

Toute modification d'un linter se fait ici : c'est la version de référence.

Synchronisation : `SPEC.md` et `FICTION.md` sont des copies allégées. Quand une règle change dans les instructions du projet « Fiches V7 » ou dans `mode-fiction-v7m.md`, reporter le changement ici (et dans le linter si la règle est contrôlée). Le dépôt est public : n'y mettre aucune donnée privée.
