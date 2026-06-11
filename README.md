# 🛡️ LandGuard Neuro-Symbolic AI

> Système hybride de détection de fraudes foncières combinant Logique de Description, Prolog, ProbLog et DeepProbLog.

**Cours** : IA Symbolique, Probabiliste & Neuro-Symbolique — Master 1 Informatique  
**Date de remise** : 11/06/2026

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture du système](#architecture)
3. [Installation](#installation)
4. [Structure du projet](#structure)
5. [Utilisation](#utilisation)
6. [Parties du projet](#parties)
7. [Résultats](#résultats)

---

## Vue d'ensemble

LandGuard détecte automatiquement les fraudes foncières (accaparement, spéculation, conflits d'intérêts, réseaux de prête-noms, blanchiment) en combinant :

- **Logique formelle** (Description Logic + Prolog) pour le raisonnement juridique
- **Probabilités** (ProbLog) pour quantifier l'incertitude
- **Deep Learning** (PyTorch) pour la classification comportementale
- **Explicabilité** (XAI) pour justifier chaque décision

---

## Architecture

```
dataset.csv
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                    main.py                          │
│              Pipeline d'orchestration               │
└──────┬──────────────┬──────────────┬────────────────┘
       │              │              │
       ▼              ▼              ▼
┌──────────┐  ┌──────────────┐  ┌──────────────────┐
│ Prolog   │  │   PyTorch    │  │     ProbLog      │
│ rules.pl │  │neural_model  │  │probabilistic_    │
│ inference│  │   .py        │  │rules.pl          │
│ _engine  │  │              │  │                  │
└──────┬───┘  └──────┬───────┘  └──────┬───────────┘
       │              │                 │
       └──────────────▼─────────────────┘
                      │
              ┌───────▴────────┐
              │  DeepProbLog   │
              │deepproblog_    │
              │model.pl +      │
              │runner.py       │
              └───────┬────────┘
                      │
              ┌───────▴────────┐
              │   XAI Traces   │
              │explainability  │
              │.pl             │
              └───────┬────────┘
                      │
              ┌───────▴────────┐
              │ rapport_final  │
              │    .txt        │
              └────────────────┘
```

---

## Installation

### Prérequis

- Python ≥ 3.10
- SWI-Prolog ≥ 9.0 → [swi-prolog.org](https://www.swi-prolog.org/download)

### 1. Cloner le dépôt

```bash
git clone https://github.com/Sawadogo57/landguard-neuro-symbolic.git
cd landguard-neuro-symbolic
```

### 2. Installer les dépendances Python

```bash
pip install torch problog
```

### 3. Entraîner le modèle neuronal

```bash
python neural_model.py
# → génère model_weights.pth
```

---

## Structure

```
landguard-neuro-symbolic/
│
├── 📄 README.md
│
├── ── Partie 1 — Logique de Description ──
├── knowledge_base.pl          # Concepts, rôles, axiomes DL, contraintes CI
├── description_logic.md       # Axiomes formels DL (AX-01 à AX-10, CI-1 à CI-8)
├── diagramme_concepts.pdf     # Diagramme visuel des concepts
│
├── ── Partie 2 — Raisonnement Prolog ──
├── rules.pl                   # 15 règles logiques (4 catégories A/B/C/D)
├── inference_engine.pl        # Moteur d'inférence + scores de suspicion
├── explainability.pl          # Traces XAI + journalisation + explications
│
├── ── Partie 3 — ProbLog ──
├── probabilistic_rules.pl     # 20 règles probabilistes (7 groupes)
├── queries.pl                 # Requêtes query/1
├── run_problog.py             # Runner Python + classification du risque
├── rapport_inference_prob.txt # Résultats d'exécution ProbLog
│
├── ── Partie 4 — DeepProbLog ──
├── neural_model.py            # Réseau PyTorch 6→32→64→32→4
├── deepproblog_model.pl       # Prédicats neuronaux nn/4 + règles hybrides
├── deepproblog_runner.py      # Intégration Python neuro-symbolique
├── model_weights.pth          # Poids du modèle entraîné
│
├── ── Partie 5 — Pipeline & Tests ──
├── main.py                    # Orchestration complète du pipeline
├── dataset.csv                # 20 dossiers synthétiques annotés
├── test_landguard.py          # tests unitaires et d'intégration
└── rapport_final.txt          # Rapport consolidé (généré automatiquement)
```

---

## Utilisation

### Pipeline complet (50 dossiers)

```bash
python main.py
```

### Analyser un acteur spécifique

```bash
python main.py --acteur abdou_dramé
```

### Mode démonstration (scénario inconnu)

```bash
python main.py --demo
```

### Raisonnement Prolog

```bash
swipl inference_engine.pl
```
```prolog
?- analyser_tous.
?- expliquer_tous_suspects.
?- rapport_synthese.
?- analyser_acteur(konate).
```

### Inférence ProbLog

```bash
python run_problog.py
```

### Intégration DeepProbLog

```bash
python deepproblog_runner.py
```

### Tests

```bash
python test_landguard.py -v
```

---

## Parties du projet

### Partie 1 — Logique de Description (20 pts)

Modélisation formelle du domaine foncier en DL :

| Élément | Nombre |
|---|---|
| Concepts atomiques | 16 |
| Axiomes DL (AX-01 à AX-10) | 10 |
| Contraintes d'intégrité (CI-1 à CI-8) | 8 |
| Rôles/Relations | 10 |

**Exemples d'axiomes :**
```
AX-01 : Citoyen ⊓ (≥4 possede.ParcelleUrbaine) ⊑ AccapareurUrbain
AX-03 : AgentPublic ⊓ ∃traite.Dossier ⊓ ∃beneficiaire.Affectation ⊑ ConflitInteretDirect
AX-10 : A→B→C→A (vendA circulaire) ⊑ BlanchimentCirculaire
```

### Partie 2 — Prolog (20 pts)

15 règles logiques en 4 catégories :

| Catégorie | Règles | Détection |
|---|---|---|
| A — Accaparement | A1–A4 | Concentration immobilière, multipropriété familiale |
| B — Spéculation | B1–B4 | Revente rapide, plus-value anormale, inactivité |
| C — Conflits | C1–C4 | Auto-attribution, dossier familial, favoritisme |
| D — Réseaux | D1–D5 | Téléphone/adresse/IBAN partagés, circuit circulaire |

Chaque règle produit une **trace XAI** avec identifiant, variables et justification juridique.

### Partie 3 — ProbLog (15 pts)

20 règles probabilistes avec classification à 4 niveaux :

| Niveau | Seuil | Exemple |
|---|---|---|
| FAIBLE | P < 0.30 | Acteur standard |
| MOYEN | 0.30 ≤ P < 0.60 | Comportement atypique |
| ÉLEVÉ | 0.60 ≤ P < 0.80 | Spéculation probable |
| CRITIQUE | P ≥ 0.80 | Fraude quasi-certaine |

**Résultats obtenus (ProbLog réel) :**
```
conflit_interet(konate)    P=0.95  [CRITIQUE]
accapareur(abdou)          P=0.90  [CRITIQUE]
speculateur(fatima)        P=0.93  [CRITIQUE]
blanchiment(abdou)         P=0.85  [CRITIQUE]
```

### Partie 4 — DeepProbLog (15 pts)

Architecture neuronale : `6 → 32 → 64 → 32 → 4`

**Features d'entrée :**
```
[nb_parcelles, freq_revente, ratio_plus_value,
 nb_liens_reseau, partage_telephone, age_premier_achat]
```

**Classes de sortie :** `standard | atypique | speculateur | fraudeur_probable`

**Règles hybrides (HY-01 à HY-08) :**
```prolog
% HY-01
fraude_confirmee(X) :-
    nn(fraud_model, [X], fraudeur_probable, _),
    accaparement_urbain(X).

% HY-08 (fraude composite)
fraude_confirmee(X) :-
    nn(fraud_model, [X], Classe, _),
    member(Classe, [speculateur, fraudeur_probable]),
    accaparement_urbain(X),
    prete_nom_symbolique(X).
```

**Résultats :**
```
abdou    → fraudeur_probable (0.98) → FRAUDE_CONFIRMEE  [HY-01, HY-03, HY-08]
fatima   → speculateur       (1.00) → SUSPICION_ELEVEE  [HY-04]
salif    → atypique          (0.97) → SUSPICION_ELEVEE  [HY-05]
konate   → atypique          (0.99) → ATYPIQUE
```

### Partie 5 — Pipeline & Tests (20 pts)

**Dataset (50 dossiers) :**

| Catégorie | Nb | IDs |
|---|---|---|
| Standard | 30 | D001–D030 |
| Spéculateur | 5 | D031–D035 |
| Accaparement | 5 | D036–D040 |
| Conflit d'intérêt | 5 | D041–D045 |
| Fraude sophistiquée | 5 | D046–D050 |

**Tests (30/30 OK) :**
- T01–T15 : Tests unitaires des règles symboliques
- T16–T19 : Tests d'inférence ProbLog (bornes)
- T20–T30 : Tests d'intégration end-to-end

---

## Résultats

### Pipeline sur 50 dossiers

```
FRAUDE_CONFIRMEE   :  7 dossiers
SUSPICION_ELEVEE   :  6 dossiers
SIGNAL_NEURONAL    : 17 dossiers
ATYPIQUE           :  5 dossiers
STANDARD           : 15 dossiers

Précision globale  : 68% (34/50)
Tests              : 30/30 ✓
```

### Exemple XAI — Dossier D050 (fraude composite)

```
[D050] coalition_abc  →  FRAUDE_CONFIRMEE
  NN = fraudeur_probable (confiance=0.97)
  ↳ HY-01: nn=fraudeur ∧ accaparement_urbain → fraude_confirmee
  ↳ HY-02: nn=fraudeur ∧ conflit_direct      → fraude_confirmee
  ↳ HY-03: nn=fraudeur ∧ blanchiment         → fraude_confirmee
  ↳ HY-08: nn∈{speculateur,fraudeur} ∧ accaparement ∧ prete_nom → fraude_confirmee
  Règles symboliques : accaparement_urbain, conflit_direct,
                       prete_nom, blanchiment_circulaire,
                       speculation, lien_familial_suspect,
                       traite_familial, iban_partage
```

---

## Dépendances

| Package | Version | Usage |
|---|---|---|
| `torch` | ≥ 2.0 | Réseau de neurones PyTorch |
| `problog` | ≥ 2.1 | Inférence probabiliste |
| `swi-prolog` | ≥ 9.0 | Moteur logique Prolog |
| `reportlab` | ≥ 4.0 | Génération du diagramme PDF |

---

*LandGuard Neuro-Symbolic AI — Master 1 IA Symbolique, Probabiliste & Neuro-Symbolique*
