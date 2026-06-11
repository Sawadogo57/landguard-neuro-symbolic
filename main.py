"""
LandGuard Neuro-Symbolic AI
main.py — Pipeline d'orchestration principal (Partie 5)

Usage :
    python main.py                     # analyse complète du dataset
    python main.py --acteur abdou      # analyse d'un acteur spécifique
    python main.py --demo              # scénario de démonstration examinateur
"""

import os, sys, csv, argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from neural_model import (
    FraudDetectorNet, entrainer, charger, predire,
    sauvegarder, CLASSES, WEIGHTS_PATH
)

RESET  = "\033[0m"; BOLD = "\033[1m"
ROUGE  = "\033[91m"; ORANGE = "\033[33m"
JAUNE  = "\033[93m"; VERT = "\033[92m"
BLEU   = "\033[94m"; VIOLET = "\033[95m"

COULEURS_ALERTE = {
    "FRAUDE_CONFIRMEE": ROUGE,
    "SUSPICION_ELEVEE": ORANGE,
    "SIGNAL_NEURONAL":  JAUNE,
    "ATYPIQUE":         BLEU,
    "STANDARD":         VERT,
}

# ── Chargement dataset ───────────────────────────────────────

def charger_dataset(chemin="dataset.csv"):
    dossiers = []
    with open(chemin, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            dossiers.append({k: row[k] for k in row})
    return dossiers

def features_depuis_dossier(d):
    nb = int(d["nb_parcelles_urbaines"]) + int(d["nb_parcelles_rurales"])
    return [nb, float(d["freq_revente"]), float(d["ratio_plus_value"]),
            int(d["nb_liens_reseau"]), int(d["partage_telephone"]), int(d["age_premier_achat"])]

# ── Règles symboliques ───────────────────────────────────────

def regles_symboliques(d):
    return {
        "accaparement_urbain":    int(d["nb_parcelles_urbaines"]) >= 4,
        "conflit_direct":         int(d["traite_dossier_propre"]) == 1,
        "prete_nom":              int(d["partage_telephone"]) == 1,
        "blanchiment_circulaire": int(d["circuit_revente"]) == 1,
        "speculation":            float(d["freq_revente"]) >= 1.5 and float(d["ratio_plus_value"]) >= 2.0,
        "lien_familial_suspect":  int(d["lien_familial_suspect"]) == 1,
        "traite_familial":        int(d["traite_dossier_familial"]) == 1,
        "iban_partage":           int(d["partage_iban"]) == 1,
    }

# ── Règles hybrides ──────────────────────────────────────────

def evaluer_hybride_csv(modele, d):
    features = features_depuis_dossier(d)
    res_nn   = predire(modele, features)
    classe   = res_nn["classe"]
    regles   = regles_symboliques(d)
    traces   = []
    fraude = suspicion = False

    if classe == "fraudeur_probable" and regles["accaparement_urbain"]:
        fraude = True; traces.append("HY-01: nn=fraudeur ∧ accaparement_urbain → fraude_confirmee")
    if classe == "fraudeur_probable" and regles["conflit_direct"]:
        fraude = True; traces.append("HY-02: nn=fraudeur ∧ conflit_direct → fraude_confirmee")
    if classe == "fraudeur_probable" and regles["blanchiment_circulaire"]:
        fraude = True; traces.append("HY-03: nn=fraudeur ∧ blanchiment_circulaire → fraude_confirmee")
    if classe == "speculateur" and regles["speculation"]:
        suspicion = True; traces.append("HY-04: nn=speculateur ∧ speculation → suspicion_elevee")
    if classe == "atypique" and regles["prete_nom"]:
        suspicion = True; traces.append("HY-05: nn=atypique ∧ prete_nom → suspicion_elevee")
    if classe in ("speculateur","fraudeur_probable") and regles["accaparement_urbain"] and regles["prete_nom"]:
        fraude = True; traces.append("HY-08: nn∈{spec,fraud} ∧ accaparement ∧ prete_nom → fraude_confirmee")

    alerte = ("FRAUDE_CONFIRMEE" if fraude else
              "SUSPICION_ELEVEE" if suspicion else
              "SIGNAL_NEURONAL"  if classe in ("fraudeur_probable","speculateur") else
              "ATYPIQUE"         if classe == "atypique" else "STANDARD")

    return {"id": d["id"], "nom": d["nom"], "label_reel": d["label"],
            "classe_nn": classe, "confiance_nn": res_nn["confiance"],
            "alerte": alerte, "traces": traces, "regles": regles,
            "description": d["description"]}

# ── Alignement label/alerte ──────────────────────────────────

def aligne(label, alerte):
    m = {"standard":           ["STANDARD", "SIGNAL_NEURONAL", "ATYPIQUE"],
         "speculateur":        ["SIGNAL_NEURONAL","SUSPICION_ELEVEE","FRAUDE_CONFIRMEE"],
         "accaparement":       ["SIGNAL_NEURONAL","SUSPICION_ELEVEE","FRAUDE_CONFIRMEE"],
         "conflit_interet":    ["ATYPIQUE","SUSPICION_ELEVEE","FRAUDE_CONFIRMEE","SIGNAL_NEURONAL"],
         "fraude_sophistiquee":["SUSPICION_ELEVEE","FRAUDE_CONFIRMEE","SIGNAL_NEURONAL","ATYPIQUE"]}
    return alerte in m.get(label, [])

# ── Affichage ────────────────────────────────────────────────

def afficher(resultats):
    print(f"\n{'='*70}")
    print(f"  {BOLD}LANDGUARD — RÉSULTATS PIPELINE{RESET}  ({len(resultats)} dossiers)")
    print(f"{'='*70}")
    for r in resultats:
        col = COULEURS_ALERTE.get(r["alerte"], RESET)
        ok  = f"{VERT}✓{RESET}" if aligne(r["label_reel"], r["alerte"]) else f"{ROUGE}✗{RESET}"
        print(f"  {r['id']:<6} {r['nom']:<24} {col}{r['alerte']:<18}{RESET} "
              f"nn={r['classe_nn']:<20} [{ok}]")
        for t in r["traces"]:
            print(f"         {VIOLET}↳ {t}{RESET}")

# ── Rapport ──────────────────────────────────────────────────

def rapport(resultats, chemin="rapport_final.txt"):
    compteurs = {k:0 for k in COULEURS_ALERTE}
    corrects  = sum(1 for r in resultats if aligne(r["label_reel"], r["alerte"]))
    for r in resultats:
        compteurs[r["alerte"]] += 1

    lignes = ["="*70,
              "  LANDGUARD — RAPPORT FINAL CONSOLIDE",
              f"  Date : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
              f"  Dossiers : {len(resultats)}",
              "="*70]
    for r in resultats:
        lignes += [f"\n[{r['id']}] {r['nom']}  |  label={r['label_reel']}  |  alerte={r['alerte']}",
                   f"  NN={r['classe_nn']} conf={r['confiance_nn']:.2f}  |  {r['description']}"]
        for t in r["traces"]:
            lignes.append(f"  → {t}")
        actives = [k for k,v in r["regles"].items() if v]
        if actives: lignes.append(f"  Règles: {', '.join(actives)}")

    precision = corrects/len(resultats)*100
    lignes += ["\n"+"="*70, "  SYNTHESE FINALE", "="*70]
    for k,n in compteurs.items():
        lignes.append(f"  {k:<22}: {n}")
    lignes.append(f"\n  Precision : {precision:.1f}% ({corrects}/{len(resultats)})")

    with open(chemin,"w",encoding="utf-8") as f:
        f.write("\n".join(lignes))

    print(f"\n  {'─'*40}")
    for k, n in compteurs.items():
        col = COULEURS_ALERTE.get(k, RESET)
        print(f"  {col}{k:<22}{RESET}: {n}")
    print(f"\n  {BOLD}Précision : {precision:.1f}%{RESET} ({corrects}/{len(resultats)})")
    print(f"  Rapport → {chemin}\n")

# ── Mode demo ────────────────────────────────────────────────

def demo(modele):
    print(f"\n{'='*70}")
    print(f"  {BOLD}{ROUGE}DEMO — SCÉNARIO INCONNU EXAMINATEUR{RESET}")
    print(f"{'='*70}\n")
    d = {"id":"DEMO","nom":"suspect_inconnu","type_acteur":"citoyen",
         "nb_parcelles_urbaines":"5","nb_parcelles_rurales":"0",
         "freq_revente":"1.8","ratio_plus_value":"2.5","nb_liens_reseau":"7",
         "partage_telephone":"1","partage_adresse":"1","partage_iban":"0",
         "age_premier_achat":"2","lien_familial_suspect":"1",
         "traite_dossier_propre":"0","traite_dossier_familial":"0",
         "circuit_revente":"1","label":"fraude_sophistiquee",
         "description":"Accaparement + réseau + blanchiment (inédit)"}
    r = evaluer_hybride_csv(modele, d)
    col = COULEURS_ALERTE.get(r["alerte"], RESET)
    print(f"  Acteur      : {r['nom']}")
    print(f"  Description : {r['description']}")
    print(f"  NN          : {r['classe_nn']} ({r['confiance_nn']:.2f})")
    print(f"  Alerte      : {col}{BOLD}{r['alerte']}{RESET}\n")
    for k,v in r["regles"].items():
        sym = f"{VERT}✓{RESET}" if v else "✗"
        print(f"  [{sym}] {k}")
    if r["traces"]:
        print()
        for t in r["traces"]:
            print(f"  {VIOLET}↳ {t}{RESET}")

# ── Point d'entrée ───────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LandGuard Pipeline")
    parser.add_argument("--acteur",  type=str)
    parser.add_argument("--demo",    action="store_true")
    parser.add_argument("--dataset", type=str, default="dataset.csv")
    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"  {BOLD}LANDGUARD NEURO-SYMBOLIC AI — PIPELINE{RESET}")
    print(f"{'='*70}")

    # 1. Modèle
    if os.path.exists(WEIGHTS_PATH):
        print(f"\n  [1/4] Chargement modèle → {WEIGHTS_PATH}")
        modele = charger(WEIGHTS_PATH)
    else:
        print(f"\n  [1/4] Entraînement en cours...")
        modele, _ = entrainer(epochs=200, verbose=False)
        sauvegarder(modele)

    # 2. Demo
    if args.demo:
        demo(modele); sys.exit(0)

    # 3. Dataset
    print(f"\n  [2/4] Chargement dataset → {args.dataset}")
    dataset = charger_dataset(args.dataset)
    print(f"        {len(dataset)} dossiers")

    # 4. Acteur unique
    if args.acteur:
        d = next((x for x in dataset if x["nom"] == args.acteur), None)
        if not d: print(f"  Acteur '{args.acteur}' introuvable."); sys.exit(1)
        r = evaluer_hybride_csv(modele, d)
        col = COULEURS_ALERTE.get(r["alerte"], RESET)
        print(f"\n  {r['nom']} → {col}{BOLD}{r['alerte']}{RESET} ({r['classe_nn']} {r['confiance_nn']:.2f})")
        for t in r["traces"]: print(f"  {VIOLET}↳ {t}{RESET}")
        sys.exit(0)

    # 5. Pipeline complet
    print(f"\n  [3/4] Pipeline neuro-symbolique...")
    resultats = [evaluer_hybride_csv(modele, d) for d in dataset]

    print(f"\n  [4/4] Rapport...\n")
    afficher(resultats)
    rapport(resultats)