"""
LandGuard Neuro-Symbolic AI
neural_model.py — Réseau de neurones PyTorch (Partie 4)

Entrée  : 6 features numériques par dossier
Sortie  : distribution sur 4 classes
          [standard, atypique, speculateur, fraudeur_probable]

Usage :
    pip install torch
    python neural_model.py
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import json
import os

# ============================================================
# SECTION 1 — FEATURES & CLASSES
# ============================================================

# 6 features d'entrée (normalisées entre 0 et 1)
FEATURES = [
    "nb_parcelles",        # nombre de parcelles possédées
    "frequence_revente",   # nb reventes / nb années
    "ratio_plus_value",    # valeur_revente / valeur_achat
    "nb_liens_reseau",     # nb connexions sociales suspectes
    "partage_telephone",   # 0 ou 1 (binaire)
    "age_premier_achat",   # années depuis premier achat (normalisé)
]

# 4 classes de sortie
CLASSES = ["standard", "atypique", "speculateur", "fraudeur_probable"]
NB_CLASSES = len(CLASSES)
NB_FEATURES = len(FEATURES)

# ============================================================
# SECTION 2 — ARCHITECTURE DU RÉSEAU
# ============================================================

class FraudDetectorNet(nn.Module):
    """
    Réseau de neurones fully-connected pour la détection de fraude.
    Architecture : 6 → 32 → 64 → 32 → 4
    """
    def __init__(self, input_dim=NB_FEATURES, hidden_dims=[32, 64, 32], output_dim=NB_CLASSES):
        super(FraudDetectorNet, self).__init__()

        layers = []
        prev_dim = input_dim
        for h in hidden_dims:
            layers += [
                nn.Linear(prev_dim, h),
                nn.BatchNorm1d(h),
                nn.ReLU(),
                nn.Dropout(0.2),
            ]
            prev_dim = h
        layers.append(nn.Linear(prev_dim, output_dim))
        # Pas de softmax ici → utilisé dans CrossEntropyLoss

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)

    def predict_proba(self, x):
        """Retourne les probabilités softmax (pour DeepProbLog)."""
        with torch.no_grad():
            logits = self.forward(x)
            return torch.softmax(logits, dim=-1)

    def predict_class(self, x):
        """Retourne la classe prédite et sa probabilité."""
        proba = self.predict_proba(x)
        idx = torch.argmax(proba, dim=-1).item()
        return CLASSES[idx], proba[0][idx].item(), proba[0].tolist()

# ============================================================
# SECTION 3 — DATASET SYNTHÉTIQUE
# ============================================================
#
# Features : [nb_parcelles, freq_revente, ratio_pv, nb_liens, tel_partage, age_achat]
# Échelle BRUTE (la normalisation est faite dans FraudDataset) :
#   nb_parcelles   : 0–10    (nombre de parcelles)
#   freq_revente   : 0–5     (reventes par an)
#   ratio_pv       : 1.0–5.0 (ratio plus-value)
#   nb_liens       : 0–10    (connexions suspectes)
#   tel_partage    : 0 ou 1
#   age_achat      : 0–20    (années depuis premier achat)

DONNEES_BRUTES = [
    # ── STANDARD (label=0) — peu de parcelles, pas de revente, ratio ~1 ──
    ([1, 0.0, 1.0, 0, 0, 10], 0),
    ([2, 0.1, 1.1, 1, 0, 12], 0),
    ([1, 0.0, 1.0, 0, 0,  8], 0),
    ([2, 0.0, 1.2, 1, 0, 15], 0),
    ([1, 0.1, 1.0, 0, 0,  9], 0),
    ([3, 0.1, 1.1, 1, 0, 11], 0),
    ([1, 0.0, 1.0, 0, 0, 16], 0),
    ([2, 0.1, 1.0, 0, 0, 13], 0),
    ([1, 0.0, 1.1, 1, 0, 10], 0),
    ([2, 0.0, 1.0, 0, 0,  9], 0),
    ([3, 0.1, 1.2, 1, 0, 12], 0),
    ([1, 0.0, 1.0, 0, 0, 14], 0),
    ([2, 0.1, 1.1, 0, 0, 10], 0),
    ([1, 0.0, 1.0, 1, 0,  8], 0),
    ([3, 0.0, 1.0, 0, 0, 11], 0),
    # ── ATYPIQUE (label=1) — quelques signaux, sans fraude avérée ──
    ([0, 0.0, 1.0, 3, 0,  8], 1),   # konate : conflit intérêt
    ([0, 0.0, 1.0, 2, 0, 10], 1),   # maitre_diallo : lien pro
    ([0, 0.0, 1.0, 3, 1,  2], 1),   # salif : tel partagé + liens
    ([4, 0.2, 1.5, 2, 0,  6], 1),
    ([3, 0.3, 1.4, 3, 0,  8], 1),
    ([5, 0.2, 1.6, 2, 1,  6], 1),
    ([4, 0.3, 1.5, 3, 0, 10], 1),
    ([3, 0.2, 1.7, 2, 1,  8], 1),
    ([5, 0.3, 1.4, 3, 0,  6], 1),
    ([4, 0.2, 1.6, 2, 0,  8], 1),
    # ── SPÉCULATEUR (label=2) — reventes fréquentes + plus-values ──
    ([1, 2.0, 2.4, 2, 0,  2], 2),   # fatima : revente 50j, ratio 2.4
    ([6, 0.6, 2.5, 3, 0,  4], 2),
    ([7, 0.7, 2.8, 4, 0,  4], 2),
    ([8, 0.6, 3.0, 3, 0,  2], 2),
    ([6, 0.8, 2.6, 4, 0,  4], 2),
    ([7, 0.6, 2.9, 3, 0,  2], 2),
    ([8, 0.7, 2.7, 4, 0,  4], 2),
    ([6, 0.8, 3.0, 3, 0,  2], 2),
    ([7, 0.6, 2.5, 4, 1,  4], 2),
    ([6, 0.8, 3.0, 4, 0,  4], 2),
    # ── FRAUDEUR_PROBABLE (label=3) — accaparement + réseau + tel ──
    ([4, 1.0, 2.0, 8, 1,  2], 3),   # abdou exact
    ([4, 0.8, 2.0, 8, 1,  2], 3),
    ([5, 1.0, 2.2, 8, 1,  2], 3),
    ([4, 0.9, 2.0, 9, 1,  2], 3),
    ([5, 0.8, 2.0, 8, 1,  2], 3),
    ([4, 1.0, 2.0, 7, 1,  3], 3),
    ([5, 0.9, 2.2, 8, 1,  2], 3),
    ([4, 1.0, 1.8, 9, 1,  2], 3),
    ([5, 0.8, 2.0, 8, 1,  3], 3),
    ([4, 1.0, 2.0, 8, 1,  2], 3),   # abdou doublé pour renforcer
    ([4, 0.9, 2.0, 8, 1,  2], 3),
    ([5, 1.0, 2.0, 9, 1,  2], 3),
]

# Normalisation des features brutes
def normaliser(row):
    x = row[0]
    return [
        x[0] / 10.0,   # nb_parcelles
        x[1] / 5.0,    # freq_revente
        (x[2] - 1.0) / 4.0,  # ratio_pv centré sur 1.0
        x[3] / 10.0,   # nb_liens
        float(x[4]),   # tel_partage
        (20.0 - x[5]) / 20.0,  # age_achat inversé (récent = plus suspect)
    ], row[1]

DONNEES_SYNTHÉTIQUES = [normaliser(r) for r in DONNEES_BRUTES]

# Features brutes des acteurs terrain (même échelle que DONNEES_BRUTES)
FEATURES_ACTEURS_BRUTES = {
    "abdou":         [4,  1.0, 1.0, 8, 1,  2],  # → FRAUDEUR_PROBABLE
    "fatima":        [1,  2.0, 2.4, 2, 0,  2],  # → SPECULATEUR
    "moussa":        [2,  0.1, 1.0, 1, 0, 10],  # → STANDARD
    "konate":        [0,  0.0, 1.0, 3, 0,  8],  # → ATYPIQUE
    "traore":        [0,  0.0, 1.0, 0, 0,  8],  # → STANDARD
    "salif":         [0,  0.0, 1.0, 3, 1,  2],  # → ATYPIQUE
    "immo_sarl":     [6,  0.2, 1.5, 3, 0,  4],  # → SPECULATEUR/ATYPIQUE
    "maitre_diallo": [0,  0.0, 1.0, 2, 0, 10],  # → ATYPIQUE
}

def normaliser_acteur(features_brutes):
    x = features_brutes
    return [
        x[0] / 10.0,
        x[1] / 5.0,
        (x[2] - 1.0) / 4.0,
        x[3] / 10.0,
        float(x[4]),
        (20.0 - x[5]) / 20.0,
    ]

class FraudDataset(Dataset):
    def __init__(self, data):
        self.X = torch.tensor([d[0] for d in data], dtype=torch.float32)
        self.y = torch.tensor([d[1] for d in data], dtype=torch.long)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

# ============================================================
# SECTION 4 — ENTRAÎNEMENT
# ============================================================

def entrainer(epochs=200, lr=0.005, batch_size=16, verbose=True):
    dataset    = FraudDataset(DONNEES_SYNTHÉTIQUES)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model     = FraudDetectorNet()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=50, gamma=0.5)

    if verbose:
        print("  Entraînement du réseau de neurones...")
        print(f"  Données : {len(dataset)} exemples | Epochs : {epochs} | LR : {lr}\n")

    pertes = []
    for epoch in range(epochs):
        model.train()
        perte_epoch = 0.0
        for X_batch, y_batch in dataloader:
            optimizer.zero_grad()
            logits = model(X_batch)
            loss   = criterion(logits, y_batch)
            loss.backward()
            optimizer.step()
            perte_epoch += loss.item()

        scheduler.step()
        pertes.append(perte_epoch)

        if verbose and (epoch + 1) % 50 == 0:
            print(f"  Epoch {epoch+1:3d}/{epochs} | Perte : {perte_epoch:.4f}")

    # Évaluation finale
    model.eval()
    correct = 0
    with torch.no_grad():
        X_all = dataset.X
        y_all = dataset.y
        preds = torch.argmax(model(X_all), dim=1)
        correct = (preds == y_all).sum().item()
        accuracy = correct / len(y_all)

    if verbose:
        print(f"\n  Accuracy finale : {accuracy*100:.1f}% ({correct}/{len(y_all)})")

    return model, pertes

# ============================================================
# SECTION 5 — SAUVEGARDE / CHARGEMENT
# ============================================================

WEIGHTS_PATH = "model_weights.pth"

def sauvegarder(model, chemin=WEIGHTS_PATH):
    torch.save({
        "model_state_dict": model.state_dict(),
        "classes":  CLASSES,
        "features": FEATURES,
        "architecture": {"input": NB_FEATURES, "hidden": [32, 64, 32], "output": NB_CLASSES},
    }, chemin)
    print(f"\n  Modèle sauvegardé → {chemin}")

def charger(chemin=WEIGHTS_PATH):
    checkpoint = torch.load(chemin, map_location="cpu")
    model = FraudDetectorNet()
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model

# ============================================================
# SECTION 6 — PRÉDICTION SUR UN DOSSIER
# ============================================================

def normaliser_dossier(nb_parcelles, freq_revente, ratio_pv, nb_liens, tel, age_achat):
    """Normalise les valeurs brutes d'un dossier terrain."""
    return [
        min(nb_parcelles / 10.0, 1.0),
        min(freq_revente  / 5.0,  1.0),
        min(ratio_pv      / 5.0,  1.0),
        min(nb_liens      / 10.0, 1.0),
        float(tel),
        min(age_achat     / 20.0, 1.0),
    ]

def predire(model, features_brutes: list) -> dict:
    """
    Prédit la classe d'un dossier.
    features_brutes = [nb_parcelles, freq_revente, ratio_pv, nb_liens, tel, age_achat]
    """
    features_norm = normaliser_dossier(*features_brutes)
    x = torch.tensor([features_norm], dtype=torch.float32)
    classe, confiance, probas = model.predict_class(x)
    return {
        "classe":     classe,
        "confiance":  round(confiance, 4),
        "probas":     {c: round(p, 4) for c, p in zip(CLASSES, probas)},
        "features":   dict(zip(FEATURES, features_brutes)),
    }

# ============================================================
# SECTION 7 — POINT D'ENTRÉE
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  LANDGUARD — MODULE NEURONAL (Partie 4)")
    print("="*55 + "\n")

    # Entraîner
    model, pertes = entrainer(epochs=200, verbose=True)

    # Sauvegarder
    sauvegarder(model)

    # Tests de prédiction — valeurs BRUTES (même échelle que le dataset)
    # [nb_parcelles, freq_revente, ratio_pv, nb_liens, tel, age_achat]
    print("\n  === PRÉDICTIONS SUR LES ACTEURS ===\n")
    dossiers_test = {
        "abdou":         [4, 1.0, 2.0, 8, 1,  2],  # → FRAUDEUR_PROBABLE
        "fatima":        [1, 2.0, 2.4, 2, 0,  2],  # → SPECULATEUR
        "moussa":        [2, 0.1, 1.0, 1, 0, 10],  # → STANDARD
        "konate":        [0, 0.0, 1.0, 3, 0,  8],  # → ATYPIQUE
        "maitre_diallo": [0, 0.0, 1.0, 2, 0, 10],  # → ATYPIQUE
        "salif":         [0, 0.0, 1.0, 3, 1,  2],  # → ATYPIQUE
        "immo_sarl":     [3, 0.5, 1.5, 3, 0,  3],  # → SPECULATEUR/ATYPIQUE
    }

    for acteur, features_brutes in dossiers_test.items():
        res = predire(model, features_brutes)
        print(f"  {acteur:<15} → {res['classe']:<20} (confiance: {res['confiance']:.2f})")
        for cls, p in res["probas"].items():
            barre = "█" * int(p * 20)
            print(f"    {cls:<22} {p:.3f} {barre}")
        print()