"""
LandGuard Neuro-Symbolic AI
deepproblog_runner.py — Intégration Neuro-Symbolique complète (Partie 4)

Ce script :
  1. Charge / entraîne le réseau PyTorch
  2. Simule l'intégration DeepProbLog (prédicats neuronaux)
  3. Applique les règles hybrides neuro-symboliques
  4. Génère des explications XAI complètes

Usage :
    python deepproblog_runner.py
"""

import os
import sys
import torch

# ── Import du module neuronal ────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from neural_model import (
    FraudDetectorNet, entrainer, charger, predire,
    sauvegarder, CLASSES, FEATURES, WEIGHTS_PATH
)

# ============================================================
# SECTION 1 — BASE DE CONNAISSANCES SYMBOLIQUE (Python)
# ============================================================

# Faits logiques (miroir de deepproblog_model.pl)
FAITS = {
    "citoyen":       {"abdou", "fatima", "moussa", "salif"},
    "agent_public":  {"konate", "traore"},
    "promoteur":     {"immo_sarl"},
    "notaire":       {"maitre_diallo"},
    "parcelles_urbaines": {
        "abdou": ["p1","p2","p3","p4"],
        "fatima": ["p5"],
        "moussa": [],
    },
    "lien_familial": [("abdou","fatima"), ("fatima","moussa")],
    "partage_telephone": [("abdou","salif"), ("salif","abdou")],
    "partage_adresse":   [("immo_sarl","maitre_diallo")],
    "lien_professionnel":[("maitre_diallo","immo_sarl")],
    "vend_a":        [("fatima","moussa"), ("moussa","abdou"), ("abdou","fatima")],
    "traite_dossier":{
        "konate":       [("d1","a1")],
        "traore":       [("d2","a2")],
        "maitre_diallo":[("d2","a2")],
    },
    "beneficiaire":  {"konate":"a1", "fatima":"a2", "immo_sarl":"a2"},
    "revente_rapide":     {"fatima"},
    "plus_value_anormale":{"fatima"},
    "non_mis_en_valeur":  {"moussa"},
}

# Features BRUTES par acteur — même échelle que le dataset d'entraînement
# [nb_parcelles, freq_revente, ratio_pv, nb_liens, tel(0/1), age_achat]
FEATURES_ACTEURS = {
    "abdou":         [4, 1.0, 2.0, 8, 1,  2],  # 4 parc urb + réseau + tel → FRAUDEUR
    "fatima":        [1, 2.0, 2.4, 2, 0,  2],  # revente 50j + ratio 2.4x → SPECULATEUR
    "moussa":        [2, 0.1, 1.0, 1, 0, 10],  # rural inactif → STANDARD
    "konate":        [0, 0.0, 1.0, 3, 0,  8],  # conflit intérêt → ATYPIQUE
    "traore":        [0, 0.0, 1.0, 0, 0,  8],  # aucun signal → STANDARD
    "salif":         [0, 0.0, 1.0, 3, 1,  2],  # tel partagé → ATYPIQUE
    "immo_sarl":     [3, 0.5, 1.5, 3, 0,  3],  # promoteur → ATYPIQUE/SPECULATEUR
    "maitre_diallo": [0, 0.0, 1.0, 2, 0, 10],  # notaire lié → ATYPIQUE
}

# ============================================================
# SECTION 2 — RÈGLES SYMBOLIQUES PURES
# ============================================================

def accaparement_urbain(acteur: str) -> bool:
    nb = len(FAITS["parcelles_urbaines"].get(acteur, []))
    return acteur in FAITS["citoyen"] and nb >= 4

def conflit_direct(acteur: str) -> bool:
    if acteur not in FAITS["agent_public"]:
        return False
    for (dossier, affectation) in FAITS["traite_dossier"].get(acteur, []):
        if FAITS["beneficiaire"].get(acteur) == affectation:
            return True
    return False

def prete_nom_symbolique(acteur: str) -> bool:
    for (a, b) in FAITS["partage_telephone"]:
        if a == acteur:
            return True
    return False

def blanchiment_circulaire(acteur: str) -> bool:
    for (a, b) in FAITS["vend_a"]:
        if a == acteur:
            for (b2, c) in FAITS["vend_a"]:
                if b2 == b and b != acteur:
                    for (c2, d) in FAITS["vend_a"]:
                        if c2 == c and d == acteur and c != acteur:
                            return True
    return False

def speculation_symbolique(acteur: str) -> bool:
    return (acteur in FAITS["revente_rapide"] and
            acteur in FAITS["plus_value_anormale"])

def lien_social(a: str, b: str) -> bool:
    paires = (FAITS["lien_familial"] + FAITS["partage_telephone"] +
              [(x,y) for (x,y) in FAITS["vend_a"]])
    return (a,b) in paires or (b,a) in paires

# ============================================================
# SECTION 3 — PRÉDICAT NEURONAL (pont PyTorch ↔ Prolog)
# ============================================================

def predicat_neuronal(modele, acteur: str) -> dict:
    """
    Simule nn(fraud_model, [X], Classe, [...]).
    Utilise predire() qui normalise automatiquement les valeurs brutes.
    """
    features = FEATURES_ACTEURS.get(acteur, [0, 0.0, 1.0, 0, 0, 5])
    return predire(modele, features)

# ============================================================
# SECTION 4 — RÈGLES HYBRIDES NEURO-SYMBOLIQUES
# ============================================================

def evaluer_hybride(modele, acteur: str) -> dict:
    """
    Applique toutes les règles hybrides HY-01 à HY-07.
    Retourne un dictionnaire de résultats avec traces XAI.
    """
    res_neural = predicat_neuronal(modele, acteur)
    classe_nn  = res_neural["classe"]
    probas_nn  = res_neural["probas"]
    traces     = []

    resultats = {
        "acteur":          acteur,
        "prediction_nn":   classe_nn,
        "probas_nn":       probas_nn,
        "confiance_nn":    res_neural["confiance"],
        "fraude_confirmee": False,
        "suspicion_elevee": False,
        "regles_activees":  [],
        "traces_xai":       [],
    }

    # HY-01 : FRAUDEUR + accaparement
    if classe_nn == "fraudeur_probable" and accaparement_urbain(acteur):
        resultats["fraude_confirmee"] = True
        resultats["regles_activees"].append("HY-01")
        resultats["traces_xai"].append(
            f"[HY-01] nn({acteur})=fraudeur_probable ∧ accaparement_urbain({acteur}) "
            f"→ fraude_confirmee({acteur})"
        )

    # HY-02 : FRAUDEUR + conflit direct
    if classe_nn == "fraudeur_probable" and conflit_direct(acteur):
        resultats["fraude_confirmee"] = True
        resultats["regles_activees"].append("HY-02")
        resultats["traces_xai"].append(
            f"[HY-02] nn({acteur})=fraudeur_probable ∧ conflit_direct({acteur}) "
            f"→ fraude_confirmee({acteur})"
        )

    # HY-03 : FRAUDEUR + blanchiment
    if classe_nn == "fraudeur_probable" and blanchiment_circulaire(acteur):
        resultats["fraude_confirmee"] = True
        resultats["regles_activees"].append("HY-03")
        resultats["traces_xai"].append(
            f"[HY-03] nn({acteur})=fraudeur_probable ∧ blanchiment_circulaire({acteur}) "
            f"→ fraude_confirmee({acteur})"
        )

    # HY-08 : SPÉCULATEUR + accaparement + réseau → fraude composite
    if classe_nn in ("speculateur", "fraudeur_probable") and \
       accaparement_urbain(acteur) and prete_nom_symbolique(acteur):
        resultats["fraude_confirmee"] = True
        resultats["regles_activees"].append("HY-08")
        resultats["traces_xai"].append(
            f"[HY-08] nn({acteur})∈{{speculateur,fraudeur_probable}} ∧ "
            f"accaparement_urbain({acteur}) ∧ prete_nom_symbolique({acteur}) "
            f"→ fraude_confirmee({acteur}) [fraude composite]"
        )

    # HY-04 : SPÉCULATEUR + spéculation symbolique
    if classe_nn == "speculateur" and speculation_symbolique(acteur):
        resultats["suspicion_elevee"] = True
        resultats["regles_activees"].append("HY-04")
        resultats["traces_xai"].append(
            f"[HY-04] nn({acteur})=speculateur ∧ speculation_symbolique({acteur}) "
            f"→ suspicion_elevee({acteur})"
        )

    # HY-05 : ATYPIQUE + prête-nom
    if classe_nn == "atypique" and prete_nom_symbolique(acteur):
        resultats["suspicion_elevee"] = True
        resultats["regles_activees"].append("HY-05")
        resultats["traces_xai"].append(
            f"[HY-05] nn({acteur})=atypique ∧ prete_nom_symbolique({acteur}) "
            f"→ suspicion_elevee({acteur})"
        )

    # HY-07 : Alerte globale
    if resultats["fraude_confirmee"]:
        resultats["alerte"] = "FRAUDE_CONFIRMEE"
    elif resultats["suspicion_elevee"]:
        resultats["alerte"] = "SUSPICION_ELEVEE"
    elif classe_nn in ("fraudeur_probable", "speculateur"):
        resultats["alerte"] = "SIGNAL_NEURONAL"
    elif classe_nn == "atypique":
        resultats["alerte"] = "ATYPIQUE"
    else:
        resultats["alerte"] = "STANDARD"

    return resultats

# ============================================================
# SECTION 5 — RÉSEAU DE FRAUDE (HY-06)
# ============================================================

def detecter_reseau_fraude(modele, acteurs: list) -> list:
    """Détecte les paires d'acteurs formant un réseau de fraude (HY-06)."""
    evaluations = {a: evaluer_hybride(modele, a) for a in acteurs}
    fraudeurs   = [a for a, r in evaluations.items() if r["fraude_confirmee"]]
    reseau      = []
    for i, a in enumerate(fraudeurs):
        for b in fraudeurs[i+1:]:
            if lien_social(a, b):
                reseau.append((a, b))
    return reseau

# ============================================================
# SECTION 6 — AFFICHAGE XAI COMPLET
# ============================================================

RESET  = "\033[0m"
BOLD   = "\033[1m"
ROUGE  = "\033[91m"
ORANGE = "\033[33m"
JAUNE  = "\033[93m"
VERT   = "\033[92m"
BLEU   = "\033[94m"
VIOLET = "\033[95m"

COULEURS_ALERTE = {
    "FRAUDE_CONFIRMEE": ROUGE,
    "SUSPICION_ELEVEE": ORANGE,
    "SIGNAL_NEURONAL":  JAUNE,
    "ATYPIQUE":         BLEU,
    "STANDARD":         VERT,
}

COULEURS_CLASSE = {
    "fraudeur_probable": ROUGE,
    "speculateur":       ORANGE,
    "atypique":          BLEU,
    "standard":          VERT,
}

def afficher_rapport_xai(resultats_tous: list, reseau: list):
    print(f"\n{'='*65}")
    print(f"  {BOLD}LANDGUARD — RAPPORT NEURO-SYMBOLIQUE (XAI){RESET}")
    print(f"{'='*65}\n")

    for r in resultats_tous:
        acteur  = r["acteur"]
        alerte  = r["alerte"]
        col_a   = COULEURS_ALERTE.get(alerte, RESET)
        col_nn  = COULEURS_CLASSE.get(r["prediction_nn"], RESET)

        print(f"  {BOLD}{'─'*60}{RESET}")
        print(f"  {BOLD}ACTEUR : {acteur.upper():<20}{RESET}  "
              f"Alerte : {col_a}{BOLD}{alerte}{RESET}")
        print(f"  {'─'*60}")

        # Prédiction neuronale
        print(f"  {BOLD}① Prédiction neuronale{RESET}")
        print(f"     Classe : {col_nn}{r['prediction_nn']}{RESET}  "
              f"(confiance : {r['confiance_nn']:.2f})")
        for cls, p in r["probas_nn"].items():
            col = COULEURS_CLASSE.get(cls, RESET)
            barre = "█" * int(p * 20) + "░" * (20 - int(p * 20))
            print(f"     {cls:<22} {col}{p:.3f} {barre}{RESET}")

        # Règles logiques activées
        print(f"\n  {BOLD}② Règles symboliques activées{RESET}")
        regles_sym = {
            "accaparement_urbain":   accaparement_urbain(acteur),
            "conflit_direct":        conflit_direct(acteur),
            "prete_nom_symbolique":  prete_nom_symbolique(acteur),
            "blanchiment_circulaire":blanchiment_circulaire(acteur),
            "speculation_symbolique":speculation_symbolique(acteur),
        }
        for regle, active in regles_sym.items():
            symbole = f"{VERT}✓{RESET}" if active else f"  "
            print(f"     [{symbole}] {regle}")

        # Traces XAI hybrides
        if r["traces_xai"]:
            print(f"\n  {BOLD}③ Traces XAI neuro-symboliques{RESET}")
            for trace in r["traces_xai"]:
                print(f"     {VIOLET}{trace}{RESET}")
        else:
            print(f"\n  {BOLD}③ Traces XAI{RESET} : aucune règle hybride activée")

        print()

    # Réseau de fraude
    print(f"  {'='*60}")
    print(f"  {BOLD}RÉSEAU DE FRAUDE DÉTECTÉ (HY-06){RESET}")
    print(f"  {'='*60}")
    if reseau:
        for (a, b) in reseau:
            print(f"  {ROUGE}⚠ {a} ↔ {b} : réseau de fraude confirmé{RESET}")
    else:
        print(f"  {VERT}Aucun réseau de fraude détecté.{RESET}")

    print(f"\n{'='*65}\n")

# ============================================================
# SECTION 7 — POINT D'ENTRÉE
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*65)
    print("  LANDGUARD — INTÉGRATION NEURO-SYMBOLIQUE (Partie 4)")
    print("="*65)

    # Charger ou entraîner le modèle
    if os.path.exists(WEIGHTS_PATH):
        print(f"\n  Chargement du modèle depuis {WEIGHTS_PATH}...")
        modele = charger(WEIGHTS_PATH)
    else:
        print("\n  Modèle introuvable — entraînement en cours...")
        modele, _ = entrainer(epochs=200, verbose=True)
        sauvegarder(modele)

    acteurs = list(FEATURES_ACTEURS.keys())

    # Évaluer tous les acteurs
    print("\n  Évaluation neuro-symbolique en cours...\n")
    resultats_tous = [evaluer_hybride(modele, a) for a in acteurs]

    # Détecter le réseau de fraude
    reseau = detecter_reseau_fraude(modele, acteurs)

    # Afficher le rapport XAI
    afficher_rapport_xai(resultats_tous, reseau)

    # Résumé final
    print("  RÉSUMÉ FINAL")
    print("  " + "─"*40)
    for r in sorted(resultats_tous, key=lambda x: (
        0 if x["alerte"]=="FRAUDE_CONFIRMEE" else
        1 if x["alerte"]=="SUSPICION_ELEVEE" else
        2 if x["alerte"]=="SIGNAL_NEURONAL"  else
        3 if x["alerte"]=="ATYPIQUE" else 4
    )):
        col = COULEURS_ALERTE.get(r["alerte"], RESET)
        print(f"  {r['acteur']:<18} {col}{r['alerte']}{RESET}")
    print()