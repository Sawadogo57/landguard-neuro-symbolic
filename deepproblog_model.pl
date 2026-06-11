% ============================================================
%  LandGuard Neuro-Symbolic AI
%  deepproblog_model.pl — Couche Neuro-Symbolique (Partie 4)
%
%  Ce fichier définit :
%   1. Les prédicats neuronaux (nn/4) — pont vers PyTorch
%   2. Les règles hybrides combinant neural + logique
%   3. Les requêtes d'inférence neuro-symbolique
%
%  Exécution via le script Python deepproblog_runner.py
% ============================================================

% ============================================================
% SECTION 1 — PRÉDICATS NEURONAUX (nn/4)
% ============================================================
%
%  Syntaxe DeepProbLog :
%  nn(nom_modele, [inputs], Output, [classes])
%
%  Le réseau PyTorch (fraud_model) prend en entrée
%  un vecteur de features et prédit une distribution
%  sur les 4 classes de fraude.

nn(fraud_model, [X], Classe, [standard, atypique, speculateur, fraudeur_probable]) :-
    acteur(X).

% ============================================================
% SECTION 2 — FAITS DE BASE
% ============================================================

acteur(abdou). acteur(fatima). acteur(moussa). acteur(salif).
acteur(konate). acteur(traore). acteur(immo_sarl). acteur(maitre_diallo).

citoyen(abdou). citoyen(fatima). citoyen(moussa). citoyen(salif).
agent_public(konate). agent_public(traore).
promoteur(immo_sarl). notaire(maitre_diallo).

parcelle_urbaine(p1). parcelle_urbaine(p2). parcelle_urbaine(p3).
parcelle_urbaine(p4). parcelle_urbaine(p5).
parcelle_rurale(r1). parcelle_rurale(r2).

possede(abdou, p1). possede(abdou, p2).
possede(abdou, p3). possede(abdou, p4).
possede(fatima, p5).
possede(moussa, r1). possede(moussa, r2).
possede(immo_sarl, r1).

lien_familial_base(abdou, fatima).
lien_familial_base(fatima, moussa).
lien_familial(X, Y) :- lien_familial_base(X, Y).
lien_familial(X, Y) :- lien_familial_base(Y, X), X \= Y.

partage_telephone(abdou, salif). partage_telephone(salif, abdou).
partage_adresse(immo_sarl, maitre_diallo).
lien_professionnel(maitre_diallo, immo_sarl).

vend_a(fatima, moussa). vend_a(moussa, abdou). vend_a(abdou, fatima).

traite(konate, d1). traite(traore, d2). traite(maitre_diallo, d2).
concerne_dossier(a1, d1). concerne_dossier(a2, d2).
beneficiaire(konate, a1). beneficiaire(fatima, a2). beneficiaire(immo_sarl, a2).

revente_rapide(fatima). plus_value_anormale(fatima). non_mis_en_valeur(moussa).

% ============================================================
% SECTION 3 — RÈGLES SYMBOLIQUES PURES (Prolog)
% ============================================================

% Accaparement détecté symboliquement
accaparement_urbain(X) :-
    citoyen(X),
    findall(P, (possede(X, P), parcelle_urbaine(P)), Ps),
    length(Ps, N), N >= 4.

% Conflit d'intérêt direct
conflit_direct(X) :-
    agent_public(X),
    traite(X, D),
    concerne_dossier(A, D),
    beneficiaire(X, A).

% Réseau de prête-noms
prete_nom_symbolique(X) :-
    partage_telephone(X, Y), X \= Y,
    possede(X, _).

% Blanchiment circulaire
blanchiment_circulaire(X) :-
    vend_a(X, Y), vend_a(Y, Z), vend_a(Z, X),
    X \= Y, Y \= Z, X \= Z.

% Spéculation symbolique
speculation_symbolique(X) :-
    revente_rapide(X), plus_value_anormale(X).

% ============================================================
% SECTION 4 — RÈGLES HYBRIDES NEURO-SYMBOLIQUES
% ============================================================

% HY-01 : Fraude confirmée = prédiction neuronale FRAUDEUR + accaparement logique
fraude_confirmee(X) :-
    nn(fraud_model, [X], fraudeur_probable, _),
    accaparement_urbain(X).

% HY-02 : Fraude confirmée = prédiction neuronale FRAUDEUR + conflit d'intérêt logique
fraude_confirmee(X) :-
    nn(fraud_model, [X], fraudeur_probable, _),
    conflit_direct(X).

% HY-03 : Fraude confirmée = prédiction neuronale FRAUDEUR + blanchiment symbolique
fraude_confirmee(X) :-
    nn(fraud_model, [X], fraudeur_probable, _),
    blanchiment_circulaire(X).

% HY-04 : Suspicion élevée = prédiction SPÉCULATEUR + spéculation symbolique
suspicion_elevee(X) :-
    nn(fraud_model, [X], speculateur, _),
    speculation_symbolique(X).

% HY-05 : Suspicion élevée = prédiction ATYPIQUE + prête-nom symbolique
suspicion_elevee(X) :-
    nn(fraud_model, [X], atypique, _),
    prete_nom_symbolique(X).

% HY-06 : Réseau de fraude = deux acteurs en fraude_confirmee + liés
reseau_fraude(X, Y) :-
    fraude_confirmee(X),
    fraude_confirmee(Y),
    X \= Y,
    (lien_familial(X, Y) ; partage_telephone(X, Y) ; vend_a(X, Y)).

% HY-07 : Alerte globale = fraude_confirmee OU suspicion_elevee
alerte_globale(X, fraude_confirmee) :- fraude_confirmee(X).
alerte_globale(X, suspicion_elevee) :- suspicion_elevee(X), \+ fraude_confirmee(X).

% HY-08 : Fraude composite — signal neuronal fort + accaparement + prête-nom
fraude_confirmee(X) :-
    (nn(fraud_model, [X], speculateur, _) ; nn(fraud_model, [X], fraudeur_probable, _)),
    accaparement_urbain(X),
    prete_nom_symbolique(X).

% ============================================================
% SECTION 5 — REQUÊTES NEURO-SYMBOLIQUES
% ============================================================

query(fraude_confirmee(abdou)).
query(fraude_confirmee(fatima)).
query(fraude_confirmee(konate)).
query(fraude_confirmee(maitre_diallo)).

query(suspicion_elevee(fatima)).
query(suspicion_elevee(moussa)).
query(suspicion_elevee(salif)).

query(reseau_fraude(abdou, fatima)).
query(reseau_fraude(abdou, salif)).

query(alerte_globale(abdou, _)).
query(alerte_globale(konate, _)).
query(alerte_globale(fatima, _)).