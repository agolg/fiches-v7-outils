# FICTION agents - personnages de fiction (charte v7m)

Version destinée aux sous-agents de la compétence « 5 brouillons ». Dérivée de `mode-fiction-v7m.md` du projet « Fiches V7 » (état du 2026-11-10). Ce document prime sur SPEC.md pour tous les points qu'il redéfinit (clusters de recherche, structure, champs, maillage, metas). Tout le reste demeure : budget de recherche, niveaux de fiabilité, charte typographique, accents, interdits, contrôle par `render_import.py`. Retirés : la partie crédits photo et le rendu final manuel. Adaptations d'import marquées [import]. En cas de conflit, IMPORT.md prime.

## F1. Détection

Ta consigne indique déjà le mode. Si un doute apparaît pendant la recherche, vérifier :
1. Wikidata (signal décisif) : QID, puis propriété P31.
   - P31 = Q5 (être humain) : portrait de personne réelle, mode normal.
   - P31 = personnage de fiction (Q95074) ou une sous-classe (humain de fiction Q15632617, personnage littéraire Q3658341, de bande dessinée Q1114461, d'anime Q80447, de jeu vidéo Q1569167, d'animation Q15773347, animal de fiction, robot de fiction...) : MODE FICTION.
   - Indices concordants : P170 (créateur), P1441 (présent dans l'oeuvre), P4584 (première apparition), P1080 (univers narratif).
2. Wikipédia FR (confirmation) : infobox « Personnage de fiction », introduction « est un personnage de fiction » ou « personnage créé par », catégories « Personnage de ... ».

Cas limites :
- Pseudonyme ou nom de scène d'une personne réelle (Stromae, Lady Gaga) : mode normal.
- Personnage incarné par un artiste (Ali G, Hannah Montana, une marionnette) : mode fiction si la page Wikipédia porte sur le personnage ; l'interprète va dans Adaptations, Points clés et maillage.
- Personnage légendaire ou mythologique (Merlin, Robin des Bois) : mode fiction, avec mention factuelle du débat d'historicité dans Naissance du personnage.
- Personnage inspiré d'une personne réelle (d'Artagnan) : mode fiction ; la personne réelle est citée dans Naissance du personnage, sans fusion des deux biographies.
- Groupe ou entité fictive (Gorillaz) : mode fiction.
- Doute persistant : le signaler dans `vigilance` et dans ta réponse finale.

"type_fiche": "fiction" est obligatoire dans portrait.json. Sans ce champ, le linter applique le contrôle de personne réelle et rejette la structure.

## F2. Recherche et fiabilité

Plancher inchangé : 8 recherches, 2 fetchs, 5 sources citables.

Clusters fiction (parallèle) :
- A. identité : "[Nom] personnage", "[Nom] wikipedia", Wikidata
- B. création : "[Nom] créateur", "[Créateur] interview [Nom]", genèse
- C. oeuvres et chronologie : première apparition, oeuvres principales
- D. adaptations : films, séries, jeux, interprètes, doubleurs VO et VF
- E. réception : controverses, censure, procès de droits d'auteur, domaine public
- F. répliques : "[Nom] réplique", "[Nom] citation"
- G. actualité : "[Nom] [année courante]"

Sources primaires spécifiques : l'oeuvre elle-même (canon), sites officiels de l'éditeur, du studio ou des ayants droit, entretiens du créateur dans un média professionnel, ouvrages et travaux universitaires, fiches de doublage d'un studio ou d'un générique, BnF et bases de dépôt légal.

Exclusions maintenues : les wikis de fans (Fandom et similaires) restent Niveau C. Ils peuvent aider à repérer une référence (tome, épisode), à vérifier ensuite dans une source admise, jamais être cités.

Distinguer systématiquement :
- fait de fiction (dans l'oeuvre) : formulé comme tel, « dans la série », « selon le tome 3 », et rattaché à l'oeuvre qui l'établit ;
- fait réel (production, ventes, audiences, procès) : soumis aux niveaux A, B, C habituels.
Quand plusieurs canons divergent (reboot, adaptation), le canon d'origine fait foi et les écarts vont dans Adaptations.

## F3. Structure du HTML - ordre strict

1. Accroche : sans h3, 34-46 mots, un p
2. Naissance du personnage : h3, 1-2 p, 100-180 mots
3. Spécificité du personnage : h3, 1-2 p, 90-150 mots
4. Repères : h3, 8-15 lignes
5. Évolution : h3, 1-2 p, 130-260 mots
6. Adaptations : si existantes, h3, 1-2 p, 80-180 mots
7. Symbolique : si documentée, h3, 1 p, 60-120 mots
8. Anecdotes : h3, 3-6, 30-45 mots chacune
9. Points clés : h3, format fixe, six lignes

Titres h3 exacts, accents compris. Sections de portrait réel interdites (Parcours, Vie personnelle et engagements, Contexte du décès, Lieux de mémoire, Controverse) : une controverse documentée va dans Symbolique ou dans une anecdote.

ACCROCHE : réponse autonome à « Qui est [Nom] ? » : nom, nature (personnage de bande dessinée, de roman, de jeu vidéo...), créateur, oeuvre et année de première apparition, trait distinctif. `<strong>Nom du personnage</strong>` en unique gras hors Repères. Ton narratif admis, mais factuel : pas de superlatif.

NAISSANCE DU PERSONNAGE : année, auteur ou studio, contexte éditorial (revue, éditeur, commande), intention de départ, inspiration réelle attestée. Les noms complets des créateurs, éditeurs et modèles réels nourrissent le maillage.

SPÉCIFICITÉ DU PERSONNAGE : apparence, caractère, qualités et défauts, signes distinctifs (tenue, objet, tic de langage), ce qui le distingue des personnages comparables. Uniquement ce qu'établit l'oeuvre ou ce qu'analysent des sources admises.

REPÈRES : `<strong>Année</strong> : événement<br>`, de la création à l'actualité. Une étiquette d'oeuvre (`<strong>Tome 1</strong>`) est admise seulement pour une chronologie interne sans année. Ordre chronologique strict.

ÉVOLUTION : grandes étapes de la vie fictive, développement physique et psychologique, rôle dans la trame, évolution du dessin ou de l'interprétation au fil du temps, mort fictive le cas échéant (jamais dans les champs `date_mort`).

ADAPTATIONS : supports (BD, roman, film, série, animation, jeu, scène), ce qui change, ce qui est conservé, interprètes et doubleurs avec années.

SYMBOLIQUE : ce que le personnage représente pour son créateur, son époque, son public, en faits attribués : déclarations du créateur, analyses publiées, usages documentés (mascotte, slogan, timbre, procès, entrée dans le domaine public). Section omise si rien n'est sourcé ; la mentionner alors dans `faits_non_trouves`.

ANECDOTES : `<p>1 - ...<br>2 - ...<br>3 - ...</p>`, chiffres et tiret ordinaire. Mélanger : une anecdote de production, une référence culturelle ou réplique connue, une réception, controverse ou fait réel. Chaque anecdote porte au moins un ancrage vérifiable (nombre, date, nom propre ou lieu).

POINTS CLÉS : format exact, six lignes, toujours présentes :
- Créateur : ...<br>
- Interprètes : ... (noms et années, ou « Sans objet »)<br>
- Doublage de voix : ... (VF et VO, noms et années, ou « Sans objet »)<br>
- Première apparition : oeuvre, année<br>
- Alias ou surnoms : ... (noms à l'étranger, ou « Aucun »)<br>
- Genre ou espèce : ...

Vocabulaire : interdits v7 maintenus, plus « culte », « iconique », « mondialement connu ». « Légende », « légendaire » et « génie » sont admis au sens propre seulement (la légende arthurienne, le Génie d'Aladdin) : le linter les signale en WARN, à justifier dans `vigilance`.

## F4. Champs structurés

`date_naissance` : uniquement la date de première apparition publique du personnage : parution, diffusion ou sortie de la première oeuvre où il figure. Jamais une date de naissance interne à l'oeuvre, ni un anniversaire officiel fixé par l'ayant droit : ces dates peuvent figurer dans le texte, jamais dans ce champ. Jour et mois retenus seulement s'ils sont attestés par une source primaire non encyclopédique (presse datée, éditeur, studio, dépôt légal) ; sinon YYYY-00-00 ; année elle-même inconnue : vide. Dans `vigilance` : « Date : première apparition, [oeuvre], [support], [type de source] ». Écart avec la valeur en base : le signaler aussi.

`date_mort`, `cause_mort`, `annee_mort_negative` : toujours vides ou 0.

`sexe` : 1 masculin, 0 féminin, selon l'oeuvre ; vide si non applicable (robot, entité), à signaler dans `vigilance`.

`pays_naissance` : toujours le pays réel où le personnage a été créé : pays de l'éditeur, du studio ou du support de sa première apparition. Jamais le pays de sa vie fictive. Exemple : Blueberry, cowboy américain créé dans l'hebdomadaire Pilote (Dargaud, Paris) : France. Co-création entre pays : pays du support de première apparition, l'écart documenté dans `vigilance`.

`nationalite` : toujours vide, même si l'oeuvre attribue une nationalité au personnage. Écart avec la valeur en base : le signaler dans `vigilance`. [import] Pas de clé `import.nationalite` en mode fiction.

`ville_naissance` : toujours vide : la ville de création n'est pas un lieu de naissance, et un lieu imaginaire (Gotham City, Poudlard) reste dans le texte.

`taille_cm` : seulement si une source officielle de l'ayant droit la donne.

Q/R : [import] exactement 6 paires, nom complet dans chaque question. Angles utiles : créateur, oeuvre de première apparition (l'oeuvre, pas la date, déjà portée par `date_naissance`), doubleur ou interprète, origine du nom, évolution du dessin, domaine public, réplique, controverse.

CITATIONS : 0 à 3 répliques du personnage dans une oeuvre canonique, une par oeuvre, 15 mots maximum. Aucun plancher : mieux vaut aucune réplique qu'une réplique qui n'a pas de sens hors de sa scène. Le test d'autonomie de SPEC.md (section 6) s'applique : la réplique se comprend sans connaître la scène, ou le contexte ajouté la rend compréhensible ; sinon elle est écartée. Privilégier la réplique devenue référence (reprise, citée par la presse) ou celle qui résume le caractère du personnage. Version française officielle si elle existe ; sinon traduction fidèle avec « (traduit de l'anglais) » dans `source`. `source` = oeuvre + année (+ épisode ou tome), puis, si la réplique contient un pronom ou un référent absent, un contexte de 12 mots maximum introduit par « s'adressant à », « dans la scène », « à propos de », « après » ou « lors de », référent nommé en clair. Forme : « [Oeuvre], [année], tome 2, s'adressant à [personnage nommé] ». `url` = page consultée qui atteste la réplique (vérification, absente du fichier importé). Aucune réplique ne passe le test, ou personnage muet : liste vide et ligne dans `faits_non_trouves`.

PHOTO : [import] hors périmètre. Bloc `photo` vide, aucune recherche photo.

MAILLAGE : personnes réelles uniquement : créateurs, scénaristes, dessinateurs successifs, éditeurs, interprètes, doubleurs, modèles réels. Jamais un autre personnage de fiction. [import] Plancher 4 noms, cible 6 à 10 (plafond de l'import : 10). Correspondance des sections, le CMS n'acceptant que trois valeurs :
- Naissance du personnage, Spécificité, Repères, Évolution, Adaptations : Parcours
- Symbolique : Vie personnelle
- Anecdotes : Anecdotes

META TITLE : 50 à 65 caractères : nom + nature + oeuvre ou créateur + année de création. Exemple de forme : « Nom, personnage de [oeuvre] créé par [auteur] en [année] ».
META DESCRIPTION : 140 à 160 caractères, mêmes règles qu'en SPEC.md. Dans les deux cas, la valeur seule : jamais de décompte de caractères, ni dans la valeur, ni entre parenthèses, ni sur une ligne voisine.

## F5. Note et contrôle

Dans `note_livraison.vigilance`, première entrée : « Mode : personnage de fiction (P31 = [libellé], QID [valeur]) ».

Contrôle : `python3 render_import.py <slug>.json` (section 8 de SPEC.md). Le script détecte le mode fiction grâce à `"type_fiche": "fiction"` et lance les linters avec le contrôle fiction.
