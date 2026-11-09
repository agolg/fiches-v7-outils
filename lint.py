#!/usr/bin/env python3
import re, sys
FICTION = "--fiction" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]
txt = open(args[0], encoding="utf-8").read(); errs, warns = [], []
m = re.search(r"```html\n(.*?)\n```", txt, re.S)
if not m: print("ERREUR: bloc html absent"); sys.exit(1)
html, note = m.group(1), txt[m.end():]
if txt[:m.start()].strip(): errs.append("Texte avant le bloc html")
for t in set(re.findall(r"</?([a-zA-Z0-9]+)", html)):
    if t.lower() not in {"h3","p","br","strong","em"}: errs.append(f"Balise interdite <{t}>")
if re.search(r"<[a-z0-9]+\s+[^>]*=", html, re.I) or "<!--" in html: errs.append("Attribut ou commentaire HTML")
if re.search(r"</?(em|strong|p|br|h3)>", note): errs.append("Balise HTML dans la note")
for ch in "—–“”‘’… ":
    if ch in html or ch in note: errs.append(f"Caractère typographique U+{ord(ch):04X}")
FORBID = [r"embl[ée]matique", r"l[ée]gendaire", r"\bl[ée]gende\b", r"\bic[ôo]ne", r"incontournable", r"mythique", r"\bmajeure?s?\b", r"pionni[eè]re? de", r"s'impose comme", r"s'est impos[ée]e? comme", r"unanimement", r"\bg[ée]nie\b", r"\bstar\b", r"r[ée]v[èe]le tout son talent", r"longue maladie"]
if FICTION: FORBID += [r"\bculte\b", r"\biconique", r"mondialement connu"]
W = lambda s: len(re.sub(r"<[^>]+>", " ", s).split())
plain = re.sub(r"<em>.*?</em>", " ", html, flags=re.S)
for p in FORBID:
    if re.search(p, plain, re.I): errs.append(f"Vocabulaire interdit: {p}")
parts = re.split(r"<h3>(.*?)</h3>", html); secs = [(parts[i].strip(), parts[i+1]) for i in range(1, len(parts), 2)]; names = [s[0] for s in secs]
if not 34 <= W(parts[0]) <= 46: errs.append(f"Accroche {W(parts[0])} mots")
if not re.match(r"\s*<p><strong>", parts[0]): errs.append("Accroche sans <p><strong>")
if len(re.findall(r"<strong>", parts[0])) != 1: errs.append("Accroche : un seul <strong> attendu")
if FICTION:
    EXP = ["Naissance du personnage","Spécificité du personnage","Repères","Évolution","Adaptations","Symbolique","Anecdotes","Points clés"]
    REQ = ["Naissance du personnage","Spécificité du personnage","Repères","Évolution","Anecdotes","Points clés"]
    REP = "Repères"; NREP = (8, 15)
    TOT = {"Naissance du personnage":(100,180,[1,2]), "Spécificité du personnage":(90,150,[1,2]), "Évolution":(130,260,[1,2]), "Adaptations":(80,180,[1,2]), "Symbolique":(60,120,[1])}
    RULES = {}
    PK = ["- Créateur :","- Interprètes :","- Doublage de voix :","- Première apparition :","- Alias ou surnoms :","- Genre ou espèce :"]
else:
    EXP = ["Parcours","Controverse","Repères chronologiques","Vie personnelle et engagements","Contexte du décès","Lieux de mémoire","Anecdotes","Points clés"]
    REQ = ["Parcours","Repères chronologiques","Vie personnelle et engagements","Anecdotes","Points clés"]
    REP = "Repères chronologiques"; NREP = (10, 15)
    TOT = {}
    RULES = {"Parcours":(130,170,[2]), "Vie personnelle et engagements":(90,110,[2]), "Contexte du décès":(80,120,[1]), "Lieux de mémoire":(50,70,[1])}
    PK = ["- Métier(s) :","- Résidence principale :","- Relations de couple :","- Enfants :","- Distinctions :"]
for n in names:
    if n not in EXP: errs.append(f"Section interdite/inconnue: {n}")
for n in REQ:
    if n not in names: errs.append(f"Section manquante: {n}")
o = [EXP.index(n) for n in names if n in EXP]
if o != sorted(o): errs.append("Ordre des sections")
for n, b in secs:
    ps = re.findall(r"<p>(.*?)</p>", b, re.S)
    if n != REP and "<strong>" in b: errs.append(f"<strong> interdit dans {n}")
    if n in RULES:
        lo, hi, cnt = RULES[n]
        if len(ps) not in cnt: errs.append(f"{n}: {len(ps)} paragraphes")
        for i, p in enumerate(ps, 1):
            if not lo <= W(p) <= hi: errs.append(f"{n} §{i}: {W(p)} mots ({lo}-{hi})")
    if n == "Anecdotes":
        if len(ps) == 1:
            items = [re.sub(r"^\s*\d+\s*-\s*", "", x) for x in re.split(r"<br>\s*(?=\d+\s*-)", ps[0])]
        else:
            items = [re.sub(r"^\s*\d+\s*-\s*", "", p) for p in ps]
        mini = 3 if FICTION else 4
        if not mini <= len(items) <= 6: errs.append(f"Anecdotes: {len(items)} ({mini}-6)")
        for i, a in enumerate(items, 1):
            if not 30 <= W(a) <= 45: errs.append(f"Anecdote {i}: {W(a)} mots (30-45)")
            if not (re.search(r"\d", a) or re.search(r"\b[A-ZÀ-Ý][a-zà-ÿ]{2,}", a)): errs.append(f"Anecdote {i} sans ancrage")
    if n in TOT:
        lo, hi, cnt = TOT[n]
        if len(ps) not in cnt: errs.append(f"{n}: {len(ps)} paragraphes")
        if not lo <= W(" ".join(ps)) <= hi: errs.append(f"{n}: {W(' '.join(ps))} mots au total ({lo}-{hi})")
    if n == REP:
        ys = [int(y) for y in re.findall(r"<strong>(\d{3,4})</strong>", b)]
        if not NREP[0] <= len(ys) <= NREP[1]: errs.append(f"Repères: {len(ys)} entrées")
        if ys != sorted(ys): errs.append("Repères: ordre chronologique")
    if n == "Points clés":
        for a in PK:
            if a not in b: errs.append(f"Points clés: ligne « {a} » absente")
mt = re.search(r"^Meta title : (.+)$", note, re.M); md = re.search(r"^Meta description : (.+)$", note, re.M)
if not mt or not 50 <= len(mt.group(1).strip()) <= 65: errs.append(f"Meta title absent ou hors 50-65 car. ({len(mt.group(1).strip()) if mt else 0})")
if not md or not 140 <= len(md.group(1).strip()) <= 160: errs.append(f"Meta description absente ou hors 140-160 car. ({len(md.group(1).strip()) if md else 0})")
for g in (mt, md):
    if g and re.search(r"\d+\s*(car\.|caract|signes|chars?\b)|[(\[]\s*\d{2,3}\s*[)\]]\s*$", g.group(1), re.I): errs.append("Décompte de caractères dans une meta")
    if g:
        for p in FORBID:
            if re.search(p, g.group(1), re.I): errs.append(f"Vocabulaire interdit (meta): {p}")
if re.search(r"^(Décompte|Longueur|Nombre de caractères)", note, re.M | re.I): errs.append("Ligne de décompte dans la note")
mm = re.search(r"▶ Maillage sémantique\n(.*?)(?:\n\s*\n|\n▶)", note + "\n\n", re.S)
if not mm: errs.append("Maillage absent de la note")
else:
    ls = [l for l in mm.group(1).splitlines() if l.strip()]
    if not 6 <= len(ls) <= 10: errs.append(f"Maillage: {len(ls)} lignes (6-10)")
    for l in ls:
        mmm = re.fullmatch(r"• ([^,—–]+) - section (Parcours|Vie personnelle|Anecdotes)", l.strip())
        if not mmm: errs.append(f"Maillage mal formé: {l}")
        elif mmm.group(1) not in html: errs.append(f"Maillage: « {mmm.group(1)} » absent du corps")
if re.search(r"\bla commande\b|\bla consigne\b", note, re.I): errs.append("Note : référence à la commande/consigne")
y = re.search(r"```yaml\n(.*?)\n```", note, re.S)
if not y: errs.append("YAML absent")
else:
    yy = y.group(1)
    keys = ["sexe:","date_naissance:","citations:","qa:"] + (["pays_naissance:"] if FICTION else ["ville_naissance:","pays_naissance:","nationalite:"])
    for k in keys:
        if k not in yy: errs.append(f"YAML: {k} absent")
    for k in ["lieu_naissance:","date_deces:","cause_deces:","url:","photo:","credit_afficher:"]:
        if k in yy: errs.append(f"YAML: {k} à retirer du fichier importé")
    if FICTION and re.search(r"^(date_mort|cause_mort|nationalite|ville_naissance):", yy, re.M): errs.append("YAML fiction: date_mort, cause_mort, nationalite et ville_naissance interdits")
    nat = re.search(r'^nationalite: "([^"]*)"', yy, re.M)
    if nat and nat.group(1) and nat.group(1)[0].islower(): errs.append("YAML: nationalite attendue en nom de pays (ex. France), pas en adjectif")
    nq = len(re.findall(r"^\s*- question:", yy, re.M))
    if nq != 6: warns.append(f"{nq} Q/R (6 attendues)")
    if re.search(r'question: "(Quel âge|Qui est né)', yy): errs.append("Q/R auto-générée interdite")
    nc = len(re.findall(r'^\s*- citation: "[^"]+"', yy, re.M)); ns = len(re.findall(r'^\s+source: "[^"]+"', yy, re.M))
    if nc != ns: errs.append(f"{nc} citations / {ns} sources")
    if nc > 3: errs.append(f"{nc} citations (maximum 3)")
    if '  - citation: ""\nqa:' not in yy: errs.append("Élément vide '- citation: \"\"' manquant juste avant qa:")
    try:
        import yaml; d = yaml.safe_load(yy)
        for c in d.get("citations") or []:
            if c.get("citation") and len(c["citation"].split()) > 15: errs.append(f"Citation > 15 mots: {c['citation'][:40]}")
        for q in d.get("qa") or []:
            if not str(q.get("question","")).rstrip().endswith("?"): errs.append("Q/R sans ?")
    except ImportError: pass
    except Exception as e: errs.append(f"YAML invalide: {e}")
for e in errs: print("ERREUR:", e)
for w in warns: print("AVERT.:", w)
print("OK" if not errs else f"{len(errs)} erreur(s)"); sys.exit(1 if errs else 0)
