#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_import.py - derive le fichier d'import CMS (<slug>.md) de la fiche de
travail <slug>.json (schema v7m), puis lance les deux linters.

Usage :
    python3 render_import.py <slug>.json          # rendu + lint_portrait.py + lint.py
    python3 render_import.py <slug>.json --sans-lint

Le contenu n'est jamais reecrit : le HTML, les metas, le maillage, les notes,
les Q/R et les citations sont repris tels quels du JSON. Seuls les caracteres
typographiques proscrits sont normalises dans la note et le YAML.

Cles propres a l'import, a ajouter dans le JSON (ignorees par lint_portrait.py) :
    "import": {
        "nationalite": "France",          # nom du pays (mode personne)
        "date_naissance": "1975-09-30"    # facultatif : valeur en base a conserver
    }

Code retour 1 si le rendu echoue ou si un linter signale une erreur.
"""
import json, os, re, subprocess, sys

TYPO = {"—": "-", "–": "-", "‘": "'", "’": "'",
        "“": "« ", "”": " »", "…": "...",
        " ": " ", "‐": "-", "−": "-"}

def propre(s):
    s = str(s if s is not None else "")
    for a, b in TYPO.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()

def yval(s):
    """Valeur YAML entre guillemets doubles : jamais de guillemet double
    interieur (regle du parseur), remplace par des guillemets francais."""
    s = propre(s)
    s = re.sub(r'"([^"]*)"', "« \\1 »", s).replace('"', "'")
    return '"' + s.replace("\\", "/") + '"'

def puces(items, vide):
    items = [propre(i) for i in items if propre(i)]
    return "\n".join("• " + (i[2:] if i.startswith("• ") else i)
                     for i in items) if items else "• " + vide

def rendre(d):
    fiction = d.get("type_fiche") == "fiction"
    c, imp = d.get("champs", {}), d.get("import", {})
    nl = d.get("note_livraison", {})
    avis = []

    maillage = d.get("maillage", [])
    if len(maillage) > 10:
        avis.append(f"maillage tronque a 10 noms (sur {len(maillage)}) pour l'import")
        maillage = maillage[:10]

    t = c.get("taille_cm")
    taille = f"{t} cm" if t else "Taille non documentée."

    y = []
    sexe = c.get("sexe")
    y.append(f"sexe: {sexe}" if sexe in (0, 1) else 'sexe: ""')
    y.append("date_naissance: " + yval(imp.get("date_naissance") or c.get("date_naissance", "")))
    if not fiction:
        if c.get("date_mort"):
            y.append("date_mort: " + yval(c["date_mort"]))
        y.append("ville_naissance: " + yval(c.get("ville_naissance", "")))
    y.append("pays_naissance: " + yval(c.get("pays_naissance", "")))
    if not fiction:
        nat = imp.get("nationalite", "")
        if not nat and c.get("nationalite"):
            avis.append("import.nationalite absent : nom du pays attendu (ex. France)")
        y.append("nationalite: " + yval(nat))
        if c.get("date_mort") and c.get("cause_mort"):
            y.append("cause_mort: " + yval(c["cause_mort"]))
    if t:
        y.append(f'taille_cm: "{t}"')
    y.append("citations:")
    for cit in d.get("citations", []):
        if propre(cit.get("citation")):
            y.append("  - citation: " + yval(cit["citation"]))
            y.append("    source: " + yval(cit.get("source", "")))
    y.append('  - citation: ""')
    y.append("qa:")
    for p in d.get("qa", []):
        y.append("  - question: " + yval(p.get("question", "")))
        y.append("    reponse: " + yval(p.get("reponse", "")))

    note = [
        "▶ Metas Tags",
        "Meta title : " + propre(d.get("meta_title")),
        "Meta description : " + propre(d.get("meta_description")),
        "",
        "▶ Maillage sémantique",
        "\n".join(f"• {propre(m.get('nom'))} - section {propre(m.get('section'))}" for m in maillage),
        "",
        "▶ Taille", taille, "",
        "▶ Faits non trouvés", puces(nl.get("faits_non_trouves", []), "Aucun."), "",
        "▶ Faits attestés par une seule source (Niveau B)", puces(nl.get("niveau_b", []), "Aucun."), "",
        "▶ Note de vigilance factuelle", puces(nl.get("vigilance", []), "Aucune."), "",
        "▶ Champs structurés",
        "```yaml", "\n".join(y), "```",
    ]
    md = "```html\n" + d["html"].strip() + "\n```\n\n" + "\n".join(note) + "\n"
    return md, fiction, avis

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); sys.exit(2)
    src = args[0]
    with open(src, encoding="utf-8") as fh:
        d = json.load(fh)
    md, fiction, avis = rendre(d)
    dest = os.path.splitext(src)[0] + ".md"
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"RENDU  {dest} ({len(md)} caracteres)")
    for a in avis:
        print("AVERT.:", a)
    if "--sans-lint" in sys.argv:
        return
    ici = os.path.dirname(os.path.abspath(__file__))
    code = 0
    for cmd in ([sys.executable, os.path.join(ici, "lint_portrait.py"), src],
                [sys.executable, os.path.join(ici, "lint.py")] + (["--fiction"] if fiction else []) + [dest]):
        print(f"\n--- {os.path.basename(cmd[1])}")
        sys.stdout.flush()
        code |= subprocess.call(cmd)
    sys.exit(1 if code else 0)

if __name__ == "__main__":
    main()
