"""
LandGuard Neuro-Symbolic AI
run_problog.py — Lanceur ProbLog + Classification du risque (Partie 3)

Usage :
    pip install problog
    python run_problog.py
"""

import os
import sys
from datetime import datetime

# ── Essayer d'importer ProbLog ───────────────────────────────
try:
    from problog.program import PrologString
    from problog import get_evaluatable
    PROBLOG_OK = True
except ImportError:
    PROBLOG_OK = False

# ============================================================
# CLASSIFICATION DU RISQUE
# ============================================================

def classer_risque(prob: float) -> tuple[str, str]:
    """Retourne (niveau, couleur_ANSI) selon la probabilité."""
    if prob < 0.30:
        return "FAIBLE",   "\033[92m"   # vert
    elif prob < 0.60:
        return "MOYEN",    "\033[93m"   # jaune
    elif prob < 0.80:
        return "ELEVE",    "\033[33m"   # orange
    else:
        return "CRITIQUE", "\033[91m"   # rouge

RESET = "\033[0m"
BOLD  = "\033[1m"

# ============================================================
# RÉSULTATS SIMULÉS (si ProbLog non installé)
# ============================================================

RESULTATS_SIMULES = {
    # Prête-nom
    "prete_nom(abdou,salif)":          0.85,
    "prete_nom(salif,abdou)":          0.85,
    "prete_nom(abdou,fatima)":         0.60,
    "prete_nom(maitre_diallo,immo_sarl)": 0.75,
    # Spéculation
    "speculateur(fatima)":             0.80,
    "speculateur(moussa)":             0.45,
    "speculateur(abdou)":              0.30,
    # Accaparement
    "accapareur(abdou)":               0.90,
    "accapareur(fatima)":              0.10,
    # Conflit d'intérêt
    "conflit_interet(konate)":         0.95,
    "conflit_interet(traore)":         0.10,
    "conflit_interet(maitre_diallo)":  0.75,
    # Blanchiment
    "blanchiment(abdou)":              0.85,
    "blanchiment(fatima)":             0.52,
    "blanchiment(immo_sarl)":          0.50,
    # Fraude composite
    "fraude_composite(konate)":        0.92,
    "fraude_composite(abdou)":         0.88,
    "fraude_composite(fatima)":        0.78,
}

# ============================================================
# INFÉRENCE PROBLOG RÉELLE
# ============================================================

PROGRAMME_PROBLOG = """
% ── Faits de base ──
citoyen(abdou). citoyen(fatima). citoyen(moussa). citoyen(salif).
agent_public(konate). agent_public(traore).
promoteur(immo_sarl). notaire(maitre_diallo).

parcelle_urbaine(p1). parcelle_urbaine(p2). parcelle_urbaine(p3).
parcelle_urbaine(p4). parcelle_urbaine(p5).
parcelle_rurale(r1).  parcelle_rurale(r2).

possede(abdou,p1). possede(abdou,p2). possede(abdou,p3). possede(abdou,p4).
possede(fatima,p5). possede(moussa,r1). possede(moussa,r2).

lien_familial(abdou,fatima). lien_familial(fatima,abdou).
lien_familial(fatima,moussa). lien_familial(moussa,fatima).

partage_telephone(abdou,salif). partage_telephone(salif,abdou).
partage_adresse(immo_sarl,maitre_diallo). partage_adresse(maitre_diallo,immo_sarl).

vend_a(fatima,moussa). vend_a(moussa,abdou). vend_a(abdou,fatima).
lien_professionnel(maitre_diallo,immo_sarl).

traite(konate,d1). traite(traore,d2). traite(maitre_diallo,d2).
concerne_dossier(a1,d1). concerne_dossier(a2,d2).
beneficiaire(konate,a1). beneficiaire(fatima,a2). beneficiaire(immo_sarl,a2).

revente_rapide(fatima). plus_value_anormale(fatima). non_mis_en_valeur(moussa).

% ── Règles probabilistes ──
0.85::prete_nom(X,Y) :- partage_telephone(X,Y), X\\=Y, possede(X,_).
0.75::prete_nom(X,Y) :- partage_adresse(X,Y), X\\=Y.
0.60::prete_nom(X,Y) :- lien_familial(X,Y), possede(X,_), possede(Y,_).

0.80::speculateur(X) :- revente_rapide(X), plus_value_anormale(X).
0.65::speculateur(X) :- revente_rapide(X).
0.45::speculateur(X) :- non_mis_en_valeur(X).

0.90::accapareur(X) :- citoyen(X), possede(X,p1), possede(X,p2), possede(X,p3), possede(X,p4).

0.95::conflit_interet(X) :- agent_public(X), traite(X,D), concerne_dossier(A,D), beneficiaire(X,A).
0.75::conflit_interet(X) :- notaire(X), traite(X,D), concerne_dossier(A,D), beneficiaire(Y,A), lien_professionnel(X,Y).

0.85::blanchiment(X) :- vend_a(X,Y), vend_a(Y,Z), vend_a(Z,X), X\\=Y, Y\\=Z.

0.92::fraude_composite(X) :- conflit_interet(X), prete_nom(X,_).
0.88::fraude_composite(X) :- accapareur(X), blanchiment(X).
0.78::fraude_composite(X) :- speculateur(X), prete_nom(X,_).

% ── Requêtes ──
query(prete_nom(abdou,salif)).
query(prete_nom(abdou,fatima)).
query(prete_nom(maitre_diallo,immo_sarl)).
query(speculateur(fatima)).
query(speculateur(moussa)).
query(accapareur(abdou)).
query(conflit_interet(konate)).
query(conflit_interet(maitre_diallo)).
query(blanchiment(abdou)).
query(fraude_composite(konate)).
query(fraude_composite(abdou)).
query(fraude_composite(fatima)).
"""

def lancer_problog() -> dict:
    """Lance ProbLog et retourne les probabilités calculées."""
    try:
        prog   = PrologString(PROGRAMME_PROBLOG)
        db     = get_evaluatable().create_from(prog)
        result = db.evaluate()
        return {str(k): float(v) for k, v in result.items()}
    except Exception as e:
        print(f"  [AVERTISSEMENT] Erreur ProbLog : {e}")
        print("  Utilisation des résultats simulés.\n")
        return RESULTATS_SIMULES

# ============================================================
# AFFICHAGE & RAPPORT
# ============================================================

CATEGORIES = {
    "prete_nom":       "PRÊTE-NOM",
    "speculateur":     "SPÉCULATION",
    "accapareur":      "ACCAPAREMENT",
    "conflit_interet": "CONFLIT D'INTÉRÊT",
    "blanchiment":     "BLANCHIMENT",
    "fraude_composite":"FRAUDE COMPOSITE",
}

def afficher_resultats(resultats: dict):
    print(f"\n{'='*65}")
    print(f"  {BOLD}LANDGUARD — RAPPORT D'INFÉRENCE PROBABILISTE{RESET}")
    print(f"  Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*65}\n")

    # Regrouper par catégorie
    par_cat = {k: [] for k in CATEGORIES}
    for query_str, prob in sorted(resultats.items()):
        for cat in CATEGORIES:
            if query_str.startswith(cat):
                par_cat[cat].append((query_str, prob))

    for cat, label in CATEGORIES.items():
        items = par_cat[cat]
        if not items:
            continue
        print(f"  {BOLD}{'─'*55}{RESET}")
        print(f"  {BOLD}▶ {label}{RESET}")
        print(f"  {'─'*55}")
        for query_str, prob in items:
            niveau, couleur = classer_risque(prob)
            barre = generer_barre(prob)
            print(f"  {query_str:<40} {couleur}{prob:.2f}  {barre}  [{niveau}]{RESET}")
        print()

    # Synthèse : acteurs les plus dangereux
    print(f"  {'='*55}")
    print(f"  {BOLD}SYNTHÈSE — ACTEURS LES PLUS À RISQUE{RESET}")
    print(f"  {'='*55}")

    scores_acteurs: dict[str, float] = {}
    for query_str, prob in resultats.items():
        acteur = extraire_acteur(query_str)
        if acteur:
            scores_acteurs[acteur] = max(scores_acteurs.get(acteur, 0), prob)

    for acteur, score in sorted(scores_acteurs.items(), key=lambda x: -x[1]):
        niveau, couleur = classer_risque(score)
        print(f"  {acteur:<20} score max={couleur}{score:.2f}{RESET}  [{niveau}]")

    print(f"\n{'='*65}\n")

def generer_barre(prob: float, largeur: int = 15) -> str:
    """Génère une barre de progression ASCII."""
    plein = int(prob * largeur)
    return "█" * plein + "░" * (largeur - plein)

def extraire_acteur(query_str: str) -> str | None:
    """Extrait le premier argument d'un prédicat."""
    try:
        interieur = query_str[query_str.index("(") + 1 : query_str.index(")")]
        return interieur.split(",")[0].strip()
    except ValueError:
        return None

# ============================================================
# EXPORT FICHIER TEXTE
# ============================================================

def exporter_rapport(resultats: dict, chemin: str = "rapport_inference_prob.txt"):
    lignes = []
    lignes.append("=" * 65)
    lignes.append("  LANDGUARD — RAPPORT D'INFÉRENCE PROBABILISTE")
    lignes.append(f"  Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    lignes.append("=" * 65)
    lignes.append("")

    for query_str, prob in sorted(resultats.items()):
        niveau, _ = classer_risque(prob)
        lignes.append(f"  {query_str:<45} P={prob:.4f}  [{niveau}]")

    lignes.append("")
    lignes.append("ÉCHELLE DE RISQUE :")
    lignes.append("  FAIBLE   : P < 0.30")
    lignes.append("  MOYEN    : 0.30 ≤ P < 0.60")
    lignes.append("  ÉLEVÉ    : 0.60 ≤ P < 0.80")
    lignes.append("  CRITIQUE : P ≥ 0.80")
    lignes.append("")
    lignes.append("=" * 65)

    with open(chemin, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes))
    print(f"  Rapport exporté → {chemin}")

# ============================================================
# POINT D'ENTRÉE
# ============================================================

if __name__ == "__main__":
    print("\n  Chargement de LandGuard ProbLog Engine...")

    if PROBLOG_OK:
        print("  ProbLog détecté — inférence réelle en cours...\n")
        resultats = lancer_problog()
    else:
        print("  ProbLog non installé — utilisation des résultats simulés.")
        print("  (Pour l'installer : pip install problog)\n")
        resultats = RESULTATS_SIMULES

    afficher_resultats(resultats)
    exporter_rapport(resultats)