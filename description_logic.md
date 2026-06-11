# LandGuard — Modélisation en Logique de Description (DL)

## 1. Taxonomie des Concepts (TBox)

### Hiérarchie des Acteurs
```
Acteur ⊑ ⊤
Citoyen ⊑ Acteur
AgentPublic ⊑ Acteur
Promoteur ⊑ Acteur
Notaire ⊑ Acteur

Citoyen ⊓ AgentPublic ⊑ ⊥   (disjoint)
Citoyen ⊓ Promoteur ⊑ ⊥     (disjoint)
AgentPublic ⊓ Notaire ⊑ ⊥   (disjoint)
```

### Hiérarchie des Parcelles
```
Parcelle ⊑ ⊤
ParcelleUrbaine ⊑ Parcelle
ParcelleRurale ⊑ Parcelle
ParcelleUrbaine ⊓ ParcelleRurale ⊑ ⊥  (disjoint)
```

### Hiérarchie des Affectations
```
Affectation ⊑ ⊤
Attribution ⊑ Affectation
Revente ⊑ Affectation
Heritage ⊑ Affectation
```

### Hiérarchie des Dossiers
```
Dossier ⊑ ⊤
DossierActif ⊑ Dossier
DossierSuspect ⊑ Dossier
DossierActif ⊓ DossierSuspect ⊑ ⊥  (disjoint)
```

### Hiérarchie des Liens Sociaux
```
LienSocial ⊑ ⊤
LienFamilial ⊑ LienSocial
LienProfessionnel ⊑ LienSocial
LienFinancier ⊑ LienSocial
```

---

## 2. Rôles & Relations (RBox)

| Rôle              | Domaine      | Co-domaine   | Propriétés          |
|-------------------|--------------|--------------|---------------------|
| possede(X,Y)      | Acteur       | Parcelle     | —                   |
| traite(X,Y)       | AgentPublic  | Dossier      | —                   |
| beneficiaire(X,Y) | Acteur       | Affectation  | —                   |
| lienFamilial(X,Y) | Acteur       | Acteur       | symétrique          |
| vendA(X,Y)        | Acteur       | Acteur       | —                   |
| partageTelephone(X,Y) | Acteur   | Acteur       | symétrique          |
| partageAdresse(X,Y)   | Acteur   | Acteur       | symétrique          |
| partageIBAN(X,Y)      | Acteur   | Acteur       | symétrique          |
| concerneDossier(X,Y)  | Affectation | Dossier | —                  |
| localiseeSur(X,Y) | Parcelle     | Zone         | —                   |

---

## 3. Axiomes de Description Logic (TBox — 10 axiomes complexes)

### AX-01 : Accaparement Urbain
```
Citoyen ⊓ (≥4 possede.ParcelleUrbaine) ⊑ AccapareurUrbain
```
> Un citoyen qui possède au moins 4 parcelles urbaines est classifié comme accapareur urbain.

### AX-02 : Accaparement Rural
```
Citoyen ⊓ (≥6 possede.ParcelleRurale) ⊑ AccapareurRural
```
> Un citoyen qui possède au moins 6 parcelles rurales est classifié comme accapareur rural.

### AX-03 : Conflit d'Intérêt Direct
```
AgentPublic ⊓ ∃traite.Dossier ⊓ ∃beneficiaire.Affectation ⊑ ConflitInteretDirect
```
> Un agent public qui traite un dossier dont il est lui-même bénéficiaire est en conflit d'intérêt direct.

### AX-04 : Conflit d'Intérêt Indirect (via lien familial)
```
AgentPublic ⊓ ∃traite.Dossier ⊓ ∃lienFamilial.(∃beneficiaire.Affectation) ⊑ ConflitInteretIndirect
```
> Un agent public traitant un dossier dont un membre de sa famille est bénéficiaire est en conflit d'intérêt indirect.

### AX-05 : Prête-Nom (partage de téléphone)
```
Acteur ⊓ ∃partageTelephone.Acteur ⊓ (≥2 possede.Parcelle) ⊑ SuspectPreteNom
```
> Un acteur partageant un numéro de téléphone avec un autre et possédant plusieurs parcelles est suspect de prête-nom.

### AX-06 : Réseau de Fraude Familiale
```
Acteur ⊓ ∃lienFamilial.(∃lienFamilial.(∃possede.Parcelle)) ⊓ (≥2 possede.Parcelle) ⊑ ReseauFamilialSuspect
```
> Un acteur appartenant à un réseau familial multi-niveaux avec concentration de parcelles est suspect de réseau de fraude familiale.

### AX-07 : Spéculateur Foncier
```
Acteur ⊓ ∃vendA.Acteur ⊓ (≥3 possede.Parcelle) ⊑ SpeculateurFoncier
```
> Un acteur ayant vendu des parcelles et en possédant encore au moins 3 est classifié spéculateur foncier.

### AX-08 : Promoteur Fantôme
```
Promoteur ⊓ (≤0 partageAdresse.Acteur) ⊓ (≤0 partageTelephone.Acteur) ⊓ (≥5 possede.Parcelle) ⊑ PromoteurFantome
```
> Un promoteur sans adresse ni téléphone vérifiables mais possédant de nombreuses parcelles est un promoteur fantôme.

### AX-09 : Dossier Suspect
```
Dossier ⊓ ∃concerneDossier.(∃beneficiaire.(AgentPublic)) ⊑ DossierSuspect
```
> Tout dossier dont l'affectation bénéficie directement à un agent public est classé suspect.

### AX-10 : Blanchiment Foncier Circulaire
```
Acteur ⊓ ∃vendA.(∃vendA.(∃vendA.Self)) ⊑ ReseauBlanchimentCirculaire
```
> Un acteur impliqué dans une chaîne circulaire de reventes (A vend à B, B vend à C, C revend à A) est suspect de blanchiment foncier circulaire.

---

## 4. Contraintes d'Intégrité (CI — 8 contraintes)

### CI-1 : Interdiction d'auto-traitement
```
∀x : AgentPublic(x) ∧ traite(x, d) → ¬beneficiaire(x, a) ∧ concerneDossier(a, d)
```
> Un agent public ne peut pas traiter un dossier dont il est lui-même bénéficiaire.

### CI-2 : Maximum 3 parcelles urbaines par citoyen
```
∀x : Citoyen(x) → |{y | possede(x,y) ∧ ParcelleUrbaine(y)}| ≤ 3
```
> Un citoyen ordinaire ne peut posséder plus de 3 parcelles urbaines simultanément.

### CI-3 : Unicité du titre foncier
```
∀p : Parcelle(p) → |{x | possede(x,p)}| = 1
```
> Une parcelle ne peut appartenir qu'à un seul propriétaire à la fois.

### CI-4 : Délai minimal de revente (anti-spéculation)
```
∀x,p : possede(x,p) ∧ vendA(x,y) → dureeDetention(x,p) ≥ 365 jours
```
> Une parcelle ne peut pas être revendue moins d'un an après son acquisition.

### CI-5 : Partage de téléphone → suspicion de prête-nom
```
∀x,y : Acteur(x) ∧ Acteur(y) ∧ x≠y ∧ partageTelephone(x,y) → SuspectPreteNom(x) ∧ SuspectPreteNom(y)
```
> Deux acheteurs distincts partageant le même numéro de téléphone sont automatiquement signalés comme suspects de prête-nom.

### CI-6 : Interdiction de traitement familial
```
∀x,y : AgentPublic(x) ∧ lienFamilial(x,y) ∧ traite(x,d) → ¬beneficiaire(y, a) ∧ concerneDossier(a,d)
```
> Un agent public ne peut pas traiter un dossier dont un membre de sa famille est bénéficiaire.

### CI-7 : Partage d'adresse entre acheteurs non liés → suspicion
```
∀x,y : Acteur(x) ∧ Acteur(y) ∧ x≠y ∧ partageAdresse(x,y) ∧ ¬lienFamilial(x,y) → SuspectPreteNom(x) ∧ SuspectPreteNom(y)
```
> Deux acheteurs non apparentés partageant la même adresse sont suspects de coordination frauduleuse.

### CI-8 : Cumul de mandats de Notaire
```
∀x : Notaire(x) → |{d | traite(x,d)}| ≤ NB_MAX_DOSSIERS_SIMULTANES
```
> Un notaire ne peut pas instrumenter un nombre anormal de transactions simultanées (seuil paramétrable).

---

## 5. Résumé de la TBox

| Élément          | Nombre défini |
|------------------|---------------|
| Concepts atomiques | 16          |
| Sous-concepts (⊑) | 12          |
| Rôles/Relations  | 10            |
| Axiomes DL       | 10            |
| Contraintes CI   | 8             |
