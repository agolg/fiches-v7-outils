#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lint_portrait.py — controle de conformite d'un portrait v7 (anniversaire-celebrite.com)

Usage :
    python3 lint_portrait.py portrait.json
    python3 lint_portrait.py portrait.json --json      # rapport machine
    python3 lint_portrait.py dossier/ --json           # lot

Sortie : lignes ERROR / WARN / OK. Code retour 1 si au moins une ERROR.
Aucune dependance externe.

Mode fiction : si le JSON contient "type_fiche": "fiction", la structure,
les volumes, les Points cles et les champs sont controles selon le gabarit
personnage de fiction (Naissance du personnage, Specificite du personnage,
Reperes, Evolution, Adaptations, Symbolique, Anecdotes, Points cles).
En fiction : nationalite et ville_naissance toujours vides, pays_naissance
= pays reel de creation du personnage.
Absent ou "personne" : controle du portrait de personne reelle, inchange.

Citations (revision novembre 2026) : 0 a 3, aucun plancher. Test
d'autonomie : une citation contenant un pronom de 3e personne ou un
pronom demonstratif sans referent doit porter un contexte a la fin de
`source`, introduit par un marqueur (a propos de, au sujet de, en
evoquant, interroge sur, lors de, apres, s'adressant a, dans la scene).

Citations (revision 2, novembre 2026) : champ `objet` obligatoire, qui
nomme en clair ce dont parle la citation. ERROR si aucun mot significatif
de `objet` ne figure dans la citation et qu'aucun contexte n'est porte en
fin de `source` (cas « passé le pas », « jeter un film »). WARN sur les
referents implicites usuels (ce/cette/ces + nom, le pas, a l'epoque...).

Credits photo (revision 3, novembre 2026, document credits-photo-v7m.md) :
des qu'un fichier Commons est renseigne, le bloc photo porte aussi source,
licence_url, type_licence, autorisation, credit_afficher et statut. WARN (jamais
bloquant) si une cle manque, si la licence n'a pas de version exacte, si le
lien de licence ou le credit ne correspondent pas a la licence, si un champ
est rempli sans fichier. Bloc photo vide : aucun controle.
"""
import json, re, sys, os, unicodedata, difflib

# ----------------------------------------------------------------------------
# Referentiels
# ----------------------------------------------------------------------------
BALISES_OK = {"h3", "p", "br", "strong", "em"}

VOCAB_INTERDIT = [
    "emblématique", "légendaire", "légende", "icône", "incontournable",
    "mythique", "pionnier de", "s'impose comme", "unanimement",
    "immense talent", "révèle tout son talent", "figure majeure",
    "figure incontournable", "génie",
]
VOCAB_CONTEXTUEL = ["majeur", "star"]          # WARN seulement : polysemiques
EUPHEMISMES = ["longue maladie", "affrontée avec courage", "des suites d'une longue"]

# Caracteres typographiques proscrits dans le HTML visible
CHARS_INTERDITS = {
    0x2014: "quadratin (—)", 0x2013: "demi-cadratin (–)",
    0x2018: "apostrophe courbe ouvrante", 0x2019: "apostrophe courbe (’)",
    0x201C: "guillemet courbe ouvrant", 0x201D: "guillemet courbe fermant",
    0x2026: "points de suspension (…)", 0x00A0: "espace insecable",
    0x2010: "trait d'union Unicode", 0x2212: "signe moins Unicode",
}

# Mots francais frequemment livres sans accent. cle = forme fautive
ACCENTS_PIEGES = {
    "celebre": "célèbre", "celebrite": "célébrité", "decede": "décédé",
    "decedee": "décédée", "deces": "décès", "francais": "français",
    "francaise": "française", "realisateur": "réalisateur",
    "realisatrice": "réalisatrice", "premiere": "première",
    "epouse": "épouse", "epoux": "époux", "theatre": "théâtre",
    "cinema": "cinéma", "carriere": "carrière", "diplome": "diplômé",
    "etudes": "études", "ecole": "école", "eleve": "élève",
    "prefere": "préféré", "annees": "années", "annee": "année",
    "pere": "père", "mere": "mère", "frere": "frère", "scenario": "scénario",
    "scenariste": "scénariste", "societe": "société", "universite": "université",
    "lycee": "lycée", "medecin": "médecin", "deja": "déjà", "apres": "après",
    "tres": "très", "meme": "même", "etait": "était", "etaient": "étaient",
    "ete": "été", "nee": "née", "serie": "série", "televisee": "télévisée",
    "television": "télévision", "recompense": "récompense",
    "recompenses": "récompenses", "cesar": "César", "medaille": "médaille",
    "deputee": "députée", "depute": "député", "elu": "élu", "elue": "élue",
    "privee": "privée", "prive": "privé", "publiee": "publiée",
    "publie": "publié", "creation": "création", "cree": "créé",
    "interprete": "interprète", "succes": "succès", "proces": "procès",
    "condamne": "condamné", "accusee": "accusée", "accuse": "accusé",
    "enquete": "enquête", "hopital": "hôpital", "obseques": "obsèques",
    "cimetiere": "cimetière", "memoire": "mémoire",
}
# Exceptions : formes sans accent qui sont des mots valides
ACCENTS_EXCEPTIONS = {"elu", "cree", "ete", "nee", "prive", "privee"}

def _purger_pieges(d):
    """Ecarte toute entree dont la correction n'ajoute aucun accent : elle se
    declencherait sur l'orthographe correcte. Garde-fou contre une faute de
    saisie dans le referentiel."""
    def sans(x):
        x = unicodedata.normalize("NFD", x.lower())
        return "".join(c for c in x if unicodedata.category(c) != "Mn")
    return {k: v for k, v in d.items() if sans(v) != v.lower()}

ACCENTS_PIEGES = _purger_pieges(ACCENTS_PIEGES)

SECTIONS_ATTENDUES = [
    "Parcours", "Controverse", "Repères chronologiques",
    "Vie personnelle et engagements", "Contexte du décès",
    "Lieux de mémoire", "Anecdotes", "Points clés",
]
SECTIONS_CONDITIONNELLES = {"Controverse", "Contexte du décès", "Lieux de mémoire"}
MAILLAGE_SECTIONS_OK = {"Parcours", "Vie personnelle", "Anecdotes"}

# --- Mode fiction ------------------------------------------------------------
SECTIONS_FICTION = [
    "Naissance du personnage", "Spécificité du personnage", "Repères",
    "Évolution", "Adaptations", "Symbolique", "Anecdotes", "Points clés",
]
SECTIONS_FICTION_CONDITIONNELLES = {"Adaptations", "Symbolique"}
# (nb paragraphes min, max, mots min, mots max) par section, total de la section
VOLUMES_FICTION = {
    "Naissance du personnage":   (1, 2, 100, 180),
    "Spécificité du personnage": (1, 2, 90, 150),
    "Évolution":                 (1, 2, 130, 260),
    "Adaptations":               (1, 2, 80, 180),
    "Symbolique":                (1, 1, 60, 120),
}
POINTS_CLES_FICTION = [
    "- Créateur :", "- Interprètes :", "- Doublage de voix :",
    "- Première apparition :", "- Alias ou surnoms :", "- Genre ou espèce :",
]
# Termes interdits en mode personne mais legitimes au sens propre en fiction
# (la legende arthurienne, le Genie d'Aladdin) : rétrogradés en WARN.
VOCAB_FICTION_TOLERE = {"légendaire", "légende", "génie"}
VOCAB_FICTION_EN_PLUS = ["culte", "iconique", "mondialement connu"]

QA_INTERDITES = [
    r"quel age", r"date de naissance", r"quand est né", r"quand est-il né",
    r"quand est-elle née", r"quand est décédé", r"date de décès",
    r"quelle est la date", r"de quelle nationalité", r"où est né",
    r"où est-il né", r"où est-elle née",
]
PRONOMS_QA = r"^(est|a|quel|quelle|combien|où|pourquoi|comment|quand)[ -](il|elle|t-il|t-elle)\b"

STOPWORDS_EN = {"the", "and", "that", "with", "have", "this", "from",
                "they", "what", "been", "would", "about", "which", "there"}

# --- Citations : test d'autonomie --------------------------------------------
CITATIONS_MAX = 3
CITATION_MOTS_MIN = 5          # en dessous : WARN, verifier l'apport
CONTEXTE_MOTS_MAX = 12
# Pronoms dont le referent doit figurer dans la citation ou dans le contexte.
# Comparaison sur texte devance (minuscule, sans accent).
ANAPHORES_FORTES = re.compile(
    r"\b(il|elle|ils|elles|lui|eux|leur|leurs|celui|celle|ceux|celles|"
    r"celui-ci|celle-ci|celui-la|celle-la)\b")
ANAPHORES_FAIBLES = re.compile(r"\b(ca|cela|ceci)\b")
# Tournures impersonnelles a neutraliser avant detection
IMPERSONNELS = re.compile(
    r"\bil (faut|fallait|faudra|faudrait|y a|y avait|y aura|y aurait|"
    r"s'agit|s'agissait|parait|semble|suffit|arrive|existe|reste|"
    r"etait une fois|est (temps|vrai|clair|difficile|important|impossible|"
    r"possible|rare|normal|evident|dommage|inutile|facile))\b")
# Marqueurs introduisant le contexte en fin de `source`
MARQUEURS_CONTEXTE = re.compile(
    r"\b(a propos d|au sujet d|en evoquant|evoquant|en parlant d|"
    r"interrogee? sur|lors d|apres|s'adressant a|dans la scene)")
# Referents implicites usuels, non pronominaux (WARN) : determinants
# demonstratifs, locutions elliptiques. Comparaison sur texte devance.
REFERENTS_IMPLICITES = re.compile(
    r"\b(cet|cette|ces|"
    r"ce (?!que\b|qui\b|dont\b|sont\b|ne\b|n'|soit\b|serait\b|fut\b|sera\b)\w+|"
    r"la-bas|ce jour-la|a l'epoque|cette fois|le pas|le cap|le saut)\b")
# Mots ignores dans le recoupement objet / citation
STOP_OBJET = {"dans", "pour", "avec", "sans", "sous", "vers", "chez", "entre",
              "leur", "leurs", "elle", "elles", "propos", "sujet", "cette",
              "celui", "celle", "comme", "apres", "avant", "depuis"}

# Decompte de caracteres glisse dans une meta : "(58 car.)", "62 caractères",
# "[150 signes]", "(61)" en fin de valeur...
DECOMPTE_META = re.compile(
    r"\d+\s*(car\.|caract|signes\b|chars?\b)|[(\[]\s*\d{2,3}\s*[)\]]\s*$", re.I)

# ----------------------------------------------------------------------------
# Outils
# ----------------------------------------------------------------------------
class Rapport:
    def __init__(self):
        self.lignes = []
    def err(self, champ, msg):  self.lignes.append(("ERROR", champ, msg))
    def warn(self, champ, msg): self.lignes.append(("WARN", champ, msg))
    @property
    def n_err(self):  return sum(1 for n, _, _ in self.lignes if n == "ERROR")
    @property
    def n_warn(self): return sum(1 for n, _, _ in self.lignes if n == "WARN")

def devance(s):
    """minuscule sans accent, pour comparaison"""
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

def mots(html_frag):
    txt = re.sub(r"<[^>]+>", " ", html_frag)
    txt = re.sub(r"&[a-z]+;", " ", txt)
    return [m for m in re.split(r"\s+", txt.strip()) if m]

def norm_citation(c):
    c = devance(c)
    return re.sub(r"[^a-z0-9 ]", " ", c).strip()

def similaires(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()

def racines(txt):
    """Racines (5 premieres lettres) des mots significatifs de 4 lettres et plus,
    pour un recoupement tolerant aux flexions (film/films, comedien/comedienne)."""
    return {w[:5] for w in re.findall(r"[a-z]{4,}", devance(txt).replace("'", " "))
            if w not in STOP_OBJET}

# ----------------------------------------------------------------------------
# Controles
# ----------------------------------------------------------------------------
def check_html_commun(html, r, fiction=False):
    """Balises, caracteres, vocabulaire, accents : communs aux deux modes."""
    # balises
    for tag in set(t.lower() for t in re.findall(r"</?\s*([a-zA-Z0-9]+)", html)):
        if tag not in BALISES_OK:
            r.err("html", f"balise interdite <{tag}>")
    if re.search(r"application/ld\+json|@context", html, re.I):
        r.err("html", "bloc JSON-LD present")
    if re.search(r"portrait mis à jour", html, re.I):
        r.err("html", "ligne 'Portrait mis a jour' presente")

    # caracteres typographiques
    for ch in set(html):
        cp = ord(ch)
        if cp in CHARS_INTERDITS:
            r.err("html", f"caractere interdit : {CHARS_INTERDITS[cp]}")

    # vocabulaire (les titres d'oeuvres en <em> sont exclus : Star Wars, etc.)
    plat = devance(re.sub(r"<em>.*?</em>", " ", html, flags=re.S))
    for mot in VOCAB_INTERDIT + (VOCAB_FICTION_EN_PLUS if fiction else []):
        if devance(mot) in plat:
            if fiction and mot in VOCAB_FICTION_TOLERE:
                r.warn("html", f"terme toléré en fiction au sens propre seulement : « {mot} »")
            else:
                r.err("html", f"vocabulaire interdit : « {mot} »")
    for mot in VOCAB_CONTEXTUEL:
        if re.search(r"\b" + devance(mot) + r"\b", plat):
            r.warn("html", f"terme a verifier en contexte : « {mot} »")
    for e in EUPHEMISMES:
        if devance(e) in plat:
            r.err("html", f"euphemisme sur le deces : « {e} »")

    check_accents(re.sub(r"<[^>]+>", " ", html), "html", r)

    # decoupage par section
    bouts = re.split(r"<h3>\s*(.*?)\s*</h3>", html)
    accroche, blocs = bouts[0], {}
    for i in range(1, len(bouts), 2):
        blocs[bouts[i].strip()] = bouts[i + 1]

    # accroche
    n = len(mots(accroche))
    if not 34 <= n <= 46:
        r.err("accroche", f"{n} mots (cible 34-46)")
    strongs_accroche = re.findall(r"<strong>(.*?)</strong>", accroche, re.S)
    if len(strongs_accroche) != 1:
        r.err("accroche", f"{len(strongs_accroche)} <strong> (attendu 1 : le nom)")
    return blocs

def check_anecdotes(blocs, r, mini=4):
    if "Anecdotes" not in blocs:
        return
    bloc = blocs["Anecdotes"]
    items = re.split(r"(?:^|<br>\s*|<p>\s*)\d+\s*-\s*", bloc)
    items = [i for i in (x.strip() for x in items) if len(mots(i)) > 3]
    if not mini <= len(items) <= 6:
        r.err("Anecdotes", f"{len(items)} anecdotes (cible {mini}-6)")
    for i, a in enumerate(items, 1):
        n = len(mots(a))
        if not 30 <= n <= 45:
            r.err("Anecdotes", f"anecdote {i} : {n} mots (cible 30-45)")
        txt = re.sub(r"<[^>]+>", "", a)
        ancre = re.search(r"\d", txt) or re.search(r"\b[A-ZÀ-Ý][a-zà-ÿ]{2,}", txt)
        if not ancre:
            r.err("Anecdotes", f"anecdote {i} : aucun ancrage (nombre, date, nom, lieu)")
    debuts = [devance(" ".join(mots(a)[:2])) for a in items]
    if len(set(debuts)) < len(debuts):
        r.warn("Anecdotes", "deux anecdotes commencent de la meme facon")

def check_html_fiction(html, r):
    blocs = check_html_commun(html, r, fiction=True)

    for nom, bloc in blocs.items():
        if nom == "Repères":
            continue
        k = len(re.findall(r"<strong>", bloc))
        if k:
            r.err(nom, f"{k} <strong> interdit hors accroche et Repères")

    presentes = list(blocs)
    for s in presentes:
        if s not in SECTIONS_FICTION:
            proche = difflib.get_close_matches(s, SECTIONS_FICTION, n=1, cutoff=0.6)
            indice = f" (attendu « {proche[0]} » ?)" if proche else ""
            r.err("structure", f"section inconnue en mode fiction : « {s} »{indice}")
    for s in SECTIONS_FICTION:
        if s not in presentes and s not in SECTIONS_FICTION_CONDITIONNELLES:
            r.err("structure", f"section absente : {s}")
    ordre_ref = [s for s in SECTIONS_FICTION if s in presentes]
    if [s for s in presentes if s in SECTIONS_FICTION] != ordre_ref:
        r.err("structure", f"ordre incorrect : {presentes} au lieu de {ordre_ref}")
    for s in ("Parcours", "Vie personnelle et engagements", "Contexte du décès", "Lieux de mémoire"):
        if s in presentes:
            r.err("structure", f"section de portrait réel interdite en fiction : {s}")

    for nom, (pmin, pmax, lo, hi) in VOLUMES_FICTION.items():
        if nom not in blocs:
            continue
        paras = re.findall(r"<p>(.*?)</p>", blocs[nom], re.S)
        if not pmin <= len(paras) <= pmax:
            r.err(nom, f"{len(paras)} paragraphes (attendu {pmin}-{pmax})")
        n = len(mots(" ".join(paras)))
        if not lo <= n <= hi:
            r.err(nom, f"{n} mots (cible {lo}-{hi})")

    if "Repères" in blocs:
        bloc = blocs["Repères"]
        etiquettes = re.findall(r"<strong>\s*(.*?)\s*</strong>\s*:", bloc, re.S)
        if not 8 <= len(etiquettes) <= 15:
            r.err("Repères", f"{len(etiquettes)} lignes (cible 8-15)")
        annees = [int(a) for a in etiquettes if re.fullmatch(r"-?\d{1,4}", a)]
        if len(annees) == len(etiquettes) and annees != sorted(annees):
            r.err("Repères", "ordre chronologique non respecte")
        elif len(annees) != len(etiquettes):
            r.warn("Repères", "étiquettes non numériques (oeuvres) : vérifier l'ordre à la main")

    check_anecdotes(blocs, r, mini=3)

    if "Points clés" in blocs:
        for a in POINTS_CLES_FICTION:
            if a not in blocs["Points clés"]:
                r.err("Points clés", f"ligne manquante ou mal formee : « {a} »")

    check_ponctuation(re.sub(r"<[^>]+>", " ", html), "html", r)
    return blocs

def check_html(html, r, decede):
    blocs = check_html_commun(html, r)

    # strong hors accroche et hors Reperes
    for nom, bloc in blocs.items():
        if nom == "Repères chronologiques":
            continue
        k = len(re.findall(r"<strong>", bloc))
        if k:
            r.err(nom, f"{k} <strong> interdit hors accroche et Reperes")

    # presence et ordre
    presentes = [b for b in blocs]
    attendu = [s for s in SECTIONS_ATTENDUES
               if s in presentes or s not in SECTIONS_CONDITIONNELLES]
    for s in [x for x in attendu if x not in presentes]:
        proche = difflib.get_close_matches(s, presentes, n=1, cutoff=0.75)
        if proche:
            r.err("structure", f"titre h3 incorrect : « {proche[0]} » attendu « {s} »")
        else:
            r.err("structure", f"section absente : {s}")
    ordre_ref = [s for s in SECTIONS_ATTENDUES if s in presentes]
    if presentes != ordre_ref:
        r.err("structure", f"ordre incorrect : {presentes} au lieu de {ordre_ref}")
    if decede:
        for s in ("Contexte du décès", "Lieux de mémoire"):
            if s not in presentes:
                r.err("structure", f"sujet decede : section {s} obligatoire")
    else:
        for s in ("Contexte du décès", "Lieux de mémoire"):
            if s in presentes:
                r.err("structure", f"sujet vivant : section {s} ne doit pas figurer")

    # volumes
    cibles = {
        "Parcours": (2, 130, 170),
        "Vie personnelle et engagements": (2, 90, 110),
    }
    for nom, (nb_p, lo, hi) in cibles.items():
        if nom not in blocs:
            continue
        paras = re.findall(r"<p>(.*?)</p>", blocs[nom], re.S)
        if len(paras) != nb_p:
            r.err(nom, f"{len(paras)} paragraphes (attendu {nb_p})")
        for i, p in enumerate(paras, 1):
            n = len(mots(p))
            if not lo <= n <= hi:
                r.err(nom, f"paragraphe {i} : {n} mots (cible {lo}-{hi})")

    for nom, (lo, hi) in {"Contexte du décès": (80, 120),
                          "Lieux de mémoire": (50, 70)}.items():
        if nom in blocs:
            n = len(mots(blocs[nom]))
            if not lo <= n <= hi:
                r.err(nom, f"{n} mots (cible {lo}-{hi})")

    # reperes
    if "Repères chronologiques" in blocs:
        bloc = blocs["Repères chronologiques"]
        lignes = re.findall(r"<strong>\s*(-?\d{1,4})\s*</strong>\s*:", bloc)
        if not 10 <= len(lignes) <= 15:
            r.err("Repères chronologiques", f"{len(lignes)} lignes (cible 10-15)")
        annees = [int(a) for a in lignes]
        if annees != sorted(annees):
            r.err("Repères chronologiques", "ordre chronologique non respecte")

    # anecdotes
    check_anecdotes(blocs, r, mini=4)

    # points cles
    if "Points clés" in blocs:
        attendues = ["- Métier(s) :", "- Résidence principale :",
                     "- Relations de couple :", "- Enfants :", "- Distinctions :"]
        for a in attendues:
            if a not in blocs["Points clés"]:
                r.err("Points clés", f"ligne manquante ou mal formee : « {a} »")

    check_ponctuation(re.sub(r"<[^>]+>", " ", html), "html", r)
    return blocs

def check_accents(txt, champ, r):
    # les URL et noms de domaine ne sont pas du texte francais : les retirer
    txt = re.sub(r"https?://\S+|\b[\w-]+\.(?:com|fr|org|net|be|ch|ca)\b", " ", txt)
    presents = set(re.findall(r"\b[a-z]{3,}\b", txt.lower()))
    for faute, bon in ACCENTS_PIEGES.items():
        if faute in presents and faute not in ACCENTS_EXCEPTIONS:
            r.err(champ, f"accent manquant : « {faute} » -> « {bon} »")

def check_ponctuation(txt, champ, r):
    if "  " in txt.replace("\n", " ").replace("> <", "><"):
        r.warn(champ, "double espace")
    for motif, libelle in [
        (r"[,;:][^\s)]", "ponctuation sans espace apres"),
        (r"\s+[,.;]", "espace avant une virgule ou un point"),
        (r"[.]{2,3}(?!\.)", "points de suspension en ASCII a verifier"),
        (r"[!?]{2,}", "ponctuation doublee"),
        (r",,|\.\s*\.", "ponctuation dupliquee"),
    ]:
        if re.search(motif, txt):
            r.warn(champ, libelle)
    if txt.count("«") != txt.count("»"):
        r.err(champ, "guillemets francais non apparies")
    if txt.count("(") != txt.count(")"):
        r.err(champ, "parentheses non appariees")

def check_metas(d, r, fiction=False):
    t, desc = d.get("meta_title", ""), d.get("meta_description", "")
    if fiction:
        for mot in VOCAB_FICTION_EN_PLUS:
            if devance(mot) in devance(t + " " + desc):
                r.err("metas", f"superlatif interdit : « {mot} »")
    if not 50 <= len(t) <= 65:
        r.err("meta_title", f"{len(t)} caracteres (cible 50-65)")
    if not 140 <= len(desc) <= 160:
        r.err("meta_description", f"{len(desc)} caracteres (cible 140-160)")
    if re.search(r"anniversaire-celebrite|[|]\s*$", t):
        r.err("meta_title", "suffixe de marque ou de domaine interdit")
    for champ, v in (("meta_title", t), ("meta_description", desc)):
        if DECOMPTE_META.search(v):
            r.err(champ, "decompte de caracteres dans la valeur : livrer la valeur seule")
        for mot in VOCAB_INTERDIT + VOCAB_CONTEXTUEL:
            if devance(mot) in devance(v):
                r.err(champ, f"superlatif interdit : « {mot} »")
        check_accents(v, champ, r)
        check_ponctuation(v, champ, r)
    # meta description ne doit pas evoquer un fait non trouve
    for f in d.get("note_livraison", {}).get("faits_non_trouves", []):
        tete = devance(str(f)).split(":")[0].strip()
        if tete and len(tete) > 4 and tete in devance(desc):
            r.err("meta_description", f"evoque un fait non documente : « {tete} »")

def check_champs_fiction(d, r):
    c = d.get("champs", {})
    v = c.get("date_naissance", "")
    if v and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(v)):
        r.err("champs.date_naissance", f"format invalide : « {v} » (YYYY-MM-DD ou YYYY-00-00)")
    for cle in ("date_mort", "cause_mort"):
        if c.get(cle):
            r.err(f"champs.{cle}", "doit rester vide en fiction (la mort fictive va dans Évolution)")
    if c.get("sexe") not in (0, 1, None, ""):
        r.err("champs.sexe", f"valeur invalide : {c.get('sexe')!r} (0, 1, ou vide si non applicable)")
    t = c.get("taille_cm")
    if t is not None and (not isinstance(t, int) or not 1 <= t <= 10000):
        r.err("champs.taille_cm", f"valeur invalide : {t!r}")
    if c.get("nationalite"):
        r.err("champs.nationalite", "doit rester vide en fiction, meme si l'oeuvre en attribue une au personnage")
    if c.get("ville_naissance"):
        r.err("champs.ville_naissance", "doit rester vide en fiction (ni ville de creation, ni lieu de la vie fictive)")
    if not c.get("pays_naissance"):
        r.warn("champs.pays_naissance", "fiction : pays reel de creation du personnage attendu (editeur, studio ou support de premiere apparition)")
    vig = " ".join(map(str, d.get("note_livraison", {}).get("vigilance", [])))
    if v and "date" not in devance(vig):
        r.warn("champs.date_naissance", "fiction : date de première apparition (oeuvre, support, source) à préciser dans vigilance")

def check_champs(d, r):
    c = d.get("champs", {})
    for cle in ("date_naissance", "date_mort"):
        v = c.get(cle, "")
        if v and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(v)):
            r.err(f"champs.{cle}", f"format invalide : « {v} » (YYYY-MM-DD ou YYYY-00-00)")
    if c.get("sexe") not in (0, 1):
        r.err("champs.sexe", f"valeur invalide : {c.get('sexe')!r} (0 ou 1)")
    nat = c.get("nationalite", "")
    if nat and (nat != nat.lower() or nat.endswith("s")):
        r.warn("champs.nationalite", f"attendu adjectif feminin singulier minuscule : « {nat} »")
    t = c.get("taille_cm")
    if t is not None and (not isinstance(t, int) or not 100 <= t <= 250):
        r.err("champs.taille_cm", f"valeur invalide : {t!r}")
    if c.get("date_mort") and not c.get("cause_mort"):
        r.warn("champs.cause_mort", "sujet decede et cause vide : verifier si documentee")
    if re.search(r"\d", str(c.get("ville_naissance", ""))) or "," in str(c.get("ville_naissance", "")):
        r.err("champs.ville_naissance", "ville seule attendue, sans departement ni pays")

def check_qa(d, r):
    qa, nom = d.get("qa", []), d.get("nom_complet", "")
    if not 4 <= len(qa) <= 8:
        r.err("qa", f"{len(qa)} paires (cible 4-8)")
    vus = []
    for i, p in enumerate(qa, 1):
        q, a = p.get("question", ""), p.get("reponse", "")
        if nom and devance(nom) not in devance(q):
            r.err(f"qa[{i}]", "la question ne contient pas le nom complet")
        if re.search(PRONOMS_QA, devance(q)):
            r.err(f"qa[{i}]", "question construite sur un pronom")
        for motif in QA_INTERDITES:
            if re.search(motif, devance(q)):
                r.err(f"qa[{i}]", f"question redondante avec un scalaire : « {q} »")
        if not q.rstrip().endswith("?"):
            r.err(f"qa[{i}]", "question sans point d'interrogation")
        if len(re.findall(r"[.!?]", a)) > 3:
            r.warn(f"qa[{i}]", "reponse de plus de 3 phrases")
        cle = norm_citation(q)
        for v in vus:
            if similaires(cle, v) > 0.85:
                r.err(f"qa[{i}]", "question quasi identique a une autre")
        vus.append(cle)
        check_accents(q + " " + a, f"qa[{i}]", r)
        check_ponctuation(q + " " + a, f"qa[{i}]", r)

def contexte_de(src):
    """Renvoie le contexte porte par `source` (texte a partir du marqueur),
    ou chaine vide. Le premier segment (media) est ignore."""
    segs = src.replace("’", "'").split(",", 1)
    reste = devance(segs[1]) if len(segs) > 1 else ""
    m = MARQUEURS_CONTEXTE.search(reste)
    return reste[m.start():].strip() if m else ""

def check_citations(d, r):
    cits = d.get("citations", [])
    if len(cits) > CITATIONS_MAX:
        r.err("citations", f"{len(cits)} citations (maximum {CITATIONS_MAX} : ne garder que les plus parlantes)")
    if not cits:
        fnt = devance(" ".join(map(str, d.get("note_livraison", {}).get("faits_non_trouves", []))))
        if "citation" not in fnt:
            r.warn("citations", "aucune citation : le declarer dans faits_non_trouves")
    normes, sources, urls = [], [], []
    for i, c in enumerate(cits, 1):
        txt, src, url = c.get("citation", ""), c.get("source", ""), c.get("url", "")
        n = len(mots(txt))
        if n > 15:
            r.err(f"citations[{i}]", f"{n} mots (maximum 15)")
        elif n < CITATION_MOTS_MIN:
            r.warn(f"citations[{i}]", f"{n} mots : verifier qu'elle apporte une information sur le sujet")
        if not src:
            r.err(f"citations[{i}]", "champ source vide")
        if not url:
            r.err(f"citations[{i}]", "champ url vide (requis pour l'audit)")
        if not re.search(r"\b(19|20)\d{2}\b", src):
            r.warn(f"citations[{i}]", "source sans annee")
        if c.get("langue_origine", "fr") != "fr" and "traduit" not in devance(src):
            r.err(f"citations[{i}]", "traduction non signalee dans source")
        bas = devance(txt).replace("’", "'")
        if sum(1 for w in re.findall(r"\b[a-z]+\b", bas) if w in STOPWORDS_EN) >= 2:
            r.err(f"citations[{i}]", "citation probablement livree en anglais")

        # test d'autonomie : referent des pronoms
        ctx = contexte_de(src)
        sans_imp = IMPERSONNELS.sub(" ", bas)
        forte = ANAPHORES_FORTES.search(sans_imp)
        faible = ANAPHORES_FAIBLES.search(sans_imp)
        if forte and not ctx:
            r.err(f"citations[{i}]", f"pronom « {forte.group(1)} » sans referent : "
                  "ajouter un contexte en fin de source (« à propos de ... ») ou ecarter la citation")
        elif faible and not ctx:
            forme = {"ca": "ça"}.get(faible.group(1), faible.group(1))
            r.warn(f"citations[{i}]", f"« {forme} » : verifier que la citation se comprend seule, "
                   "sinon ajouter un contexte en fin de source")
        if ctx:
            nc = len(ctx.split())
            if nc > CONTEXTE_MOTS_MAX:
                r.warn(f"citations[{i}]", f"contexte de {nc} mots (maximum {CONTEXTE_MOTS_MAX})")
            if not re.search(r"[A-ZÀ-Ý]", src[len(src) - len(ctx):]) and forte:
                r.warn(f"citations[{i}]", "contexte sans nom propre : nommer le referent en clair")

        # test d'autonomie : objet de la citation (referent non pronominal)
        objet = str(c.get("objet", "")).strip()
        if not objet:
            r.err(f"citations[{i}]", "champ objet vide : nommer en clair ce dont parle la citation")
        elif not ctx and not (racines(objet) & racines(txt)):
            r.err(f"citations[{i}]", f"objet « {objet} » absent de la citation : "
                  "le porter en contexte en fin de source (« à propos de ... ») ou ecarter la citation")
        implicite = REFERENTS_IMPLICITES.search(bas)
        if implicite and not ctx:
            r.warn(f"citations[{i}]", f"referent implicite « {implicite.group(0)} » : "
                   "verifier que la citation se comprend sans l'article")

        # doublons
        cle = norm_citation(txt)
        for j, v in enumerate(normes, 1):
            s = similaires(cle, v)
            if s > 0.90:
                r.err(f"citations[{i}]", f"doublon de la citation {j} (similarite {s:.0%})")
            elif s > 0.75:
                r.warn(f"citations[{i}]", f"tres proche de la citation {j} (similarite {s:.0%})")
        normes.append(cle)
        if src:
            base = devance(re.split(r",", src)[0])
            if base in sources:
                r.err(f"citations[{i}]", f"deuxieme citation tiree de la meme source : « {base} »")
            sources.append(base)
        if url:
            if url in urls:
                r.err(f"citations[{i}]", "URL dupliquee")
            urls.append(url)
        check_accents(txt + " " + src, f"citations[{i}]", r)
        check_ponctuation(txt, f"citations[{i}]", r)

def check_maillage(d, r, plancher=6, cible=8):
    m = d.get("maillage", [])
    noms = []
    for i, e in enumerate(m, 1):
        nom, sec = e.get("nom", ""), e.get("section", "")
        if sec not in MAILLAGE_SECTIONS_OK:
            r.err(f"maillage[{i}]", f"section invalide : « {sec} »")
        if not re.fullmatch(r"[A-ZÀ-Ý][\w'’\-\.]+(?:\s+[A-ZÀ-Ýa-zà-ÿ][\w'\-\.]*)+", nom):
            r.err(f"maillage[{i}]", f"nom complet attendu (Prenom Nom) : « {nom} »")
        if "," in nom or re.search(r"\bet\b", nom):
            r.err(f"maillage[{i}]", "plusieurs noms sur une entree")
        if nom and devance(nom) not in devance(d.get("html", "")):
            r.err(f"maillage[{i}]", f"« {nom} » absent du corps du portrait")
        noms.append(devance(nom))
    uniq = len(set(noms))
    if uniq < plancher:
        r.err("maillage", f"{uniq} noms distincts (plancher {plancher}, cible {cible}-15)")
    elif uniq < cible:
        r.warn("maillage", f"{uniq} noms distincts (cible {cible}-15)")
    if len(noms) != uniq:
        r.warn("maillage", "noms dupliques dans la liste")

# --- Credits photo (revision 3, novembre 2026) --------------------------------
# Les champs source, type_licence, autorisation et credit_afficher reprennent
# a l'identique les « Infos photo » de l'onglet Images du CMS. licence_url
# n'a pas de champ CMS : le site le deduit de la version citee dans le credit.
TYPES_LICENCE_CMS = {"royalty-free", "creative-commons", "domaine-public",
                     "licence-commerciale", "droits-reserves"}
LICENCE_CC = re.compile(r"CC (BY(?:-SA|-ND|-NC|-NC-SA|-NC-ND)?) (\d\.\d)(?: ([a-z]{2}))?")
PHOTO_STATUTS = {"candidat", "identifiée"}
PHOTO_CLES = ("source", "commons_licence", "commons_auteur", "licence_url",
              "type_licence", "autorisation", "credit_afficher", "statut")

def licence_attendue(lic):
    """(type_licence CMS, licence_url, suffixe du credit) pour une licence
    Commons normalisee, ou None si la licence n'est pas reconnue."""
    m = LICENCE_CC.fullmatch(lic or "")
    if m:
        if "NC" in m.group(1) or "ND" in m.group(1):
            return None                      # licence non libre : jamais creditee
        url = f"https://creativecommons.org/licenses/{m.group(1).lower()}/{m.group(2)}/"
        if m.group(3):
            url += m.group(3) + "/"
        return "creative-commons", url, f"{lic}, recadrée et retouchée"
    if lic == "CC0":
        return "domaine-public", "https://creativecommons.org/publicdomain/zero/1.0/", "CC0"
    if lic == "Domaine public":
        return "domaine-public", "", "domaine public"
    return None

def check_photo(d, r):
    """Jamais bloquant : la photo n'est pas lue par le parseur et deux tiers des
    photos du site ne viennent pas de Commons. Chaque WARN signifie : ne pas
    saisir ce credit en l'etat (le corriger ou vider le bloc photo)."""
    p = d.get("photo", {})
    qid, f = p.get("wikidata_qid", ""), p.get("commons_file", "")
    if qid and not re.fullmatch(r"Q\d+", qid):
        r.warn("photo.wikidata_qid", f"format invalide : « {qid} »")
    if not f:
        if qid:
            r.warn("photo.commons_file", "QID renseigne sans fichier Commons")
        for cle in PHOTO_CLES:
            if p.get(cle):
                r.warn(f"photo.{cle}", "rempli sans fichier Commons : vider (un credit faux est pire qu'un champ vide)")
        return
    if f.lower().startswith("file:") or f.lower().startswith("fichier:"):
        r.warn("photo.commons_file", "prefixe File: a retirer")
    if not re.search(r"\.(jpg|jpeg|png|tif|tiff|webp|svg)$", f, re.I):
        r.warn("photo.commons_file", "extension de fichier absente ou invalide")
    for cle in PHOTO_CLES:
        if cle not in p:
            r.warn(f"photo.{cle}", "cle absente du bloc photo (schema credits-photo-v7m)")
    lic, aut = p.get("commons_licence", ""), p.get("commons_auteur", "")
    if not aut:
        r.warn("photo.commons_auteur", "auteur vide : Artist de Commons, sinon Credit, sinon « Auteur inconnu »")
    att = licence_attendue(lic)
    if not lic:
        r.warn("photo.commons_licence", "licence requise des lors qu'un fichier est renseigne")
    elif att is None:
        r.warn("photo.commons_licence", f"licence « {lic} » non reconnue : version exacte attendue "
              "(ex. CC BY-SA 3.0, CC BY 2.0 de), CC0 ou Domaine public ; sinon vider le bloc et signaler")
    src_att = "https://commons.wikimedia.org/wiki/File:" + f.replace(" ", "_")
    if p.get("source") and p["source"] != src_att:
        r.warn("photo.source", f"page Commons du fichier attendue : {src_att}")
    if att:
        typ, url, suffixe = att
        if p.get("type_licence") != typ:
            r.warn("photo.type_licence", f"« {typ} » attendu pour {lic}")
        if p.get("licence_url", "") != url:
            r.warn("photo.licence_url", f"« {url} » attendu pour {lic}")
        cred = f"Photo : {aut} / Wikimedia Commons, {suffixe}"
        if p.get("credit_afficher") != cred:
            r.warn("photo.credit_afficher", f"attendu : « {cred} »")
    if p.get("type_licence") and p["type_licence"] not in TYPES_LICENCE_CMS:
        r.warn("photo.type_licence", f"valeur hors menu CMS : « {p['type_licence']} »")
    if p.get("autorisation") != "oui":
        r.warn("photo.autorisation", "« oui » attendu pour une licence libre attestee par Commons")
    if p.get("statut") not in PHOTO_STATUTS:
        r.warn("photo.statut", "« candidat » (P18, origine de la photo du site non verifiee) "
              "ou « identifiée » (meme prise de vue que la photo du site)")
    elif p.get("statut") == "candidat":
        vig = devance(" ".join(map(str, d.get("note_livraison", {}).get("vigilance", []))))
        if "candidat" not in vig:
            r.warn("photo.statut", "photo candidate : le dire dans vigilance (credit a saisir seulement "
                   "si la photo de la fiche provient de ce fichier)")
    for cle in ("commons_auteur", "credit_afficher"):
        for ch in str(p.get(cle, "")):
            if ord(ch) in CHARS_INTERDITS:
                r.warn(f"photo.{cle}", f"caractere interdit : {CHARS_INTERDITS[ord(ch)]}")

def lint(d):
    r = Rapport()
    for cle in ("slug", "nom_complet", "html", "champs", "qa", "citations",
                "maillage", "note_livraison", "meta_title", "meta_description"):
        if cle not in d:
            r.err("schema", f"cle absente : {cle}")
    if r.n_err:
        return r
    type_fiche = d.get("type_fiche", "personne")
    if type_fiche not in ("personne", "fiction"):
        r.err("schema", f"type_fiche invalide : « {type_fiche} » (personne ou fiction)")
        return r
    if type_fiche == "fiction":
        check_html_fiction(d["html"], r)
        check_metas(d, r, fiction=True)
        check_champs_fiction(d, r)
        check_maillage(d, r, plancher=4, cible=6)
    else:
        decede = bool(d.get("champs", {}).get("date_mort"))
        check_html(d["html"], r, decede)
        check_metas(d, r)
        check_champs(d, r)
        check_maillage(d, r)
    check_qa(d, r)
    check_citations(d, r)
    check_photo(d, r)
    return r

# ----------------------------------------------------------------------------
def traiter(chemin, en_json):
    with open(chemin, encoding="utf-8") as fh:
        d = json.load(fh)
    r = lint(d)
    if en_json:
        return r, {"fichier": os.path.basename(chemin),
                   "erreurs": r.n_err, "avertissements": r.n_warn,
                   "lignes": [{"niveau": n, "champ": c, "message": m}
                              for n, c, m in r.lignes]}
    print(f"\n=== {d.get('nom_complet') or os.path.basename(chemin)} ===")
    for niveau, champ, msg in r.lignes:
        print(f"{niveau:5s} {champ:34s} {msg}")
    if not r.lignes:
        print("OK    conforme")
    print(f"----- {r.n_err} erreur(s), {r.n_warn} avertissement(s)")
    return r, None

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    en_json = "--json" in sys.argv
    if not args:
        print(__doc__); sys.exit(2)
    cibles = []
    for a in args:
        if os.path.isdir(a):
            cibles += sorted(os.path.join(a, f) for f in os.listdir(a) if f.endswith(".json"))
        else:
            cibles.append(a)
    total, rapports = 0, []
    for c in cibles:
        r, j = traiter(c, en_json)
        total += r.n_err
        if j: rapports.append(j)
    if en_json:
        print(json.dumps(rapports, ensure_ascii=False, indent=2))
    sys.exit(1 if total else 0)

if __name__ == "__main__":
    main()
