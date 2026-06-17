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
ACCENT = "\033[96m"; GRIS   = "\033[90m"

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

# ── Mode demo (scénario fixe) ─────────────────────────────────

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
    afficher_resultat_demo(r)

# ── Mode demo interactif (saisie clavier examinateur) ─────────

def saisir_oui_non(question):
    while True:
        rep = input(f"  {question} [o/n] : ").strip().lower()
        if rep in ("o","oui","1"): return "1"
        if rep in ("n","non","0"): return "0"
        print(f"  {ORANGE}⚠ Entrez 'o' (oui) ou 'n' (non){RESET}")

def saisir_nombre(question, defaut, mini=0, maxi=999, entier=True):
    while True:
        rep = input(f"  {question} [défaut={defaut}] : ").strip()
        if rep == "": return str(defaut)
        try:
            val = int(rep) if entier else float(rep)
            if mini <= val <= maxi: return str(val)
            print(f"  {ORANGE}⚠ Valeur entre {mini} et {maxi}{RESET}")
        except ValueError:
            print(f"  {ORANGE}⚠ Entrez un nombre valide{RESET}")

def saisir_texte(question, defaut):
    rep = input(f"  {question} [défaut={defaut}] : ").strip()
    return rep if rep else defaut

def afficher_resultat_demo(r):
    col = COULEURS_ALERTE.get(r["alerte"], RESET)
    print(f"\n{'─'*70}")
    print(f"  {BOLD}RÉSULTAT DE L'ANALYSE{RESET}")
    print(f"{'─'*70}")
    print(f"\n  Acteur       : {BOLD}{r['nom']}{RESET}")
    print(f"  Description  : {r['description']}")
    print()

    # Prédiction neuronale
    print(f"  {BOLD}① Prédiction neuronale (PyTorch){RESET}")
    print(f"     Classe    : {BOLD}{r['classe_nn']}{RESET}  (confiance : {r['confiance_nn']:.2f})")
    print()

    # Règles symboliques
    print(f"  {BOLD}② Règles symboliques Prolog{RESET}")
    for k, v in r["regles"].items():
        sym = f"{VERT}✓{RESET}" if v else f"{GRIS}✗{RESET}"
        etat = f"{VERT}ACTIVE{RESET}" if v else f"{GRIS}inactive{RESET}"
        print(f"     [{sym}] {k:<28} → {etat}")
    print()

    # Traces XAI hybrides
    print(f"  {BOLD}③ Traces XAI neuro-symboliques{RESET}")
    if r["traces"]:
        for t in r["traces"]:
            print(f"     {VIOLET}↳ {t}{RESET}")
    else:
        print(f"     {GRIS}(aucune règle hybride activée){RESET}")
    print()

    # Verdict final
    print(f"  {'═'*66}")
    print(f"  {BOLD}  VERDICT FINAL : {col}{r['alerte']}{RESET}")
    print(f"  {'═'*66}\n")

    # Explication juridique du verdict
    explications = {
        "FRAUDE_CONFIRMEE": (
            f"  {ROUGE}⚠ FRAUDE CONFIRMÉE{RESET}\n"
            f"  Le système neuro-symbolique a détecté une fraude avérée.\n"
            f"  La prédiction neuronale EST corroborée par les règles logiques.\n"
            f"  Ce dossier doit être transmis au parquet pour investigation."
        ),
        "SUSPICION_ELEVEE": (
            f"  {ORANGE}⚠ SUSPICION ÉLEVÉE{RESET}\n"
            f"  Signal fort détecté — investigation administrative requise.\n"
            f"  Le dossier présente des indicateurs combinés suspects."
        ),
        "SIGNAL_NEURONAL": (
            f"  {JAUNE}⚡ SIGNAL NEURONAL{RESET}\n"
            f"  Le réseau neuronal détecte une anomalie comportementale.\n"
            f"  Surveillance accrue recommandée — pas de confirmation symbolique."
        ),
        "ATYPIQUE": (
            f"  {BLEU}ℹ ATYPIQUE{RESET}\n"
            f"  Comportement hors norme sans fraude avérée.\n"
            f"  Dossier à surveiller lors des prochaines transactions."
        ),
        "STANDARD": (
            f"  {VERT}✓ STANDARD{RESET}\n"
            f"  Aucune anomalie détectée. Dossier conforme aux normes foncières."
        ),
    }
    print(explications.get(r["alerte"], ""))
    print()

def demo_interactif(modele):
    print(f"\n{'='*70}")
    print(f"  {BOLD}{ROUGE}LANDGUARD — MODE DÉMO INTERACTIF{RESET}")
    print(f"  {GRIS}Soutenance | Scénario saisi par l'examinateur{RESET}")
    print(f"{'='*70}")
    print(f"\n  {BOLD}Veuillez saisir les informations du dossier à analyser.{RESET}")
    print(f"  {GRIS}(Appuyez sur Entrée pour garder la valeur par défaut){RESET}\n")
    print(f"  {'─'*68}")

    # ── Identité ──────────────────────────────────────────────
    print(f"\n  {BOLD}{ACCENT}[1/6] IDENTITÉ DU DOSSIER{RESET}")
    nom         = saisir_texte("Nom de l'acteur", "suspect_exam")
    type_acteur = saisir_texte("Type (citoyen/agent_public/promoteur/notaire)", "citoyen")

    # ── Parcelles ─────────────────────────────────────────────
    print(f"\n  {BOLD}{ACCENT}[2/6] PARCELLES{RESET}")
    nb_urb = saisir_nombre("Nb de parcelles urbaines", 0, 0, 20)
    nb_rur = saisir_nombre("Nb de parcelles rurales",  0, 0, 20)

    # ── Transactions ──────────────────────────────────────────
    print(f"\n  {BOLD}{ACCENT}[3/6] TRANSACTIONS{RESET}")
    freq   = saisir_nombre("Fréquence de revente (ex: 2.5 = 2.5 reventes/an)", 0.0, 0, 10, entier=False)
    ratio  = saisir_nombre("Ratio plus-value (ex: 2.4 = vendu 2.4x le prix d'achat)", 1.0, 0, 10, entier=False)
    age    = saisir_nombre("Âge depuis premier achat (années)", 5, 0, 30)

    # ── Réseau ────────────────────────────────────────────────
    print(f"\n  {BOLD}{ACCENT}[4/6] RÉSEAU & CONNEXIONS{RESET}")
    liens  = saisir_nombre("Nb de liens réseau suspects", 0, 0, 20)
    tel    = saisir_oui_non("Partage de numéro de téléphone avec un autre acteur ?")
    adr    = saisir_oui_non("Partage d'adresse avec un autre acteur ?")
    iban   = saisir_oui_non("Partage d'IBAN bancaire ?")
    fam    = saisir_oui_non("Lien familial suspect détecté ?")

    # ── Dossier administratif ─────────────────────────────────
    print(f"\n  {BOLD}{ACCENT}[5/6] DOSSIER ADMINISTRATIF{RESET}")
    propre = saisir_oui_non("L'acteur traite-t-il son propre dossier ? (auto-attribution)")
    famil  = saisir_oui_non("L'acteur traite-t-il un dossier familial ?")

    # ── Circuit ───────────────────────────────────────────────
    print(f"\n  {BOLD}{ACCENT}[6/6] CIRCUIT DE REVENTE{RESET}")
    circ   = saisir_oui_non("Circuit circulaire de reventes détecté ? (A→B→C→A)")

    # ── Description libre ─────────────────────────────────────
    print()
    desc = saisir_texte("Description libre du scénario", "Scénario saisi par l'examinateur")

    # ── Récapitulatif ─────────────────────────────────────────
    print(f"\n{'─'*70}")
    print(f"  {BOLD}RÉCAPITULATIF DU DOSSIER SAISI{RESET}")
    print(f"{'─'*70}")
    recap = [
        ("Nom",                   nom),
        ("Type acteur",           type_acteur),
        ("Parcelles urbaines",    nb_urb),
        ("Parcelles rurales",     nb_rur),
        ("Fréquence revente",     freq),
        ("Ratio plus-value",      ratio),
        ("Âge premier achat",     age),
        ("Liens réseau",          liens),
        ("Partage téléphone",     "Oui" if tel=="1" else "Non"),
        ("Partage adresse",       "Oui" if adr=="1" else "Non"),
        ("Partage IBAN",          "Oui" if iban=="1" else "Non"),
        ("Lien familial suspect", "Oui" if fam=="1" else "Non"),
        ("Auto-attribution",      "Oui" if propre=="1" else "Non"),
        ("Dossier familial",      "Oui" if famil=="1" else "Non"),
        ("Circuit circulaire",    "Oui" if circ=="1" else "Non"),
        ("Description",           desc),
    ]
    for k, v in recap:
        print(f"  {GRIS}{k:<26}{RESET} : {BOLD}{v}{RESET}")

    # ── Confirmation ──────────────────────────────────────────
    print()
    conf = input(f"  {BOLD}Lancer l'analyse ? [o/n] : {RESET}").strip().lower()
    if conf not in ("o","oui","1",""):
        print(f"\n  {ORANGE}Analyse annulée.{RESET}\n")
        return

    # ── Analyse ───────────────────────────────────────────────
    print(f"\n  {GRIS}Analyse en cours...{RESET}")
    import time; time.sleep(0.6)

    d = {
        "id": "EXAM", "nom": nom, "type_acteur": type_acteur,
        "nb_parcelles_urbaines": nb_urb, "nb_parcelles_rurales": nb_rur,
        "freq_revente": freq, "ratio_plus_value": ratio,
        "nb_liens_reseau": liens, "partage_telephone": tel,
        "partage_adresse": adr, "partage_iban": iban,
        "age_premier_achat": age, "lien_familial_suspect": fam,
        "traite_dossier_propre": propre, "traite_dossier_familial": famil,
        "circuit_revente": circ, "label": "inconnu",
        "description": desc,
    }

    r = evaluer_hybride_csv(modele, d)
    afficher_resultat_demo(r)

    # ── Relancer ? ────────────────────────────────────────────
    again = input(f"  Analyser un autre dossier ? [o/n] : ").strip().lower()
    if again in ("o","oui","1"):
        demo_interactif(modele)

# ── Point d'entrée ───────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LandGuard Pipeline")
    parser.add_argument("--acteur",           type=str)
    parser.add_argument("--demo",             action="store_true")
    parser.add_argument("--demo-interactif",  action="store_true")
    parser.add_argument("--dataset",          type=str, default="dataset.csv")
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

    # 2. Demo fixe
    if args.demo:
        demo(modele); sys.exit(0)

    # 2b. Demo interactif soutenance
    if getattr(args, 'demo_interactif', False):
        demo_interactif(modele); sys.exit(0)

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