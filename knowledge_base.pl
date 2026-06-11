% ============================================================
%  LandGuard Neuro-Symbolic AI
%  knowledge_base.pl — Base de connaissances (Partie 1)
%  Déclarations des concepts, rôles et contraintes DL en Prolog
% ============================================================

:- discontiguous acteur/1, citoyen/1, agent_public/1, promoteur/1, notaire/1.
:- discontiguous parcelle/1, parcelle_urbaine/1, parcelle_rurale/1.
:- discontiguous affectation/1, attribution/1, revente/1, heritage/1.
:- discontiguous dossier/1, dossier_actif/1, dossier_suspect/1.
:- discontiguous lien_social/2, lien_familial/2, lien_professionnel/2, lien_financier/2.
:- discontiguous possede/2, traite/2, beneficiaire/2, vend_a/2.
:- discontiguous partage_telephone/2, partage_adresse/2, partage_iban/2.
:- discontiguous concerne_dossier/2, date_acquisition/3, date_revente/3, valeur/2.

% ============================================================
% SECTION 1 — TAXONOMIE DES ACTEURS
% ============================================================

% Tout citoyen, agent public, promoteur ou notaire est un acteur
acteur(X) :- citoyen(X).
acteur(X) :- agent_public(X).
acteur(X) :- promoteur(X).
acteur(X) :- notaire(X).

% Contrainte de disjonction (vérification)
acteur_type_unique(X) :-
    acteur(X),
    (citoyen(X) -> T1 = 1 ; T1 = 0),
    (agent_public(X) -> T2 = 1 ; T2 = 0),
    (promoteur(X) -> T3 = 1 ; T3 = 0),
    (notaire(X) -> T4 = 1 ; T4 = 0),
    Total is T1 + T2 + T3 + T4,
    (Total > 1 ->
        format("[ERREUR-CI] ~w appartient à plusieurs types d'acteurs !~n", [X])
    ;   true).

% ============================================================
% SECTION 2 — TAXONOMIE DES PARCELLES
% ============================================================

parcelle(X) :- parcelle_urbaine(X).
parcelle(X) :- parcelle_rurale(X).

% ============================================================
% SECTION 3 — TAXONOMIE DES AFFECTATIONS
% ============================================================

affectation(X) :- attribution(X).
affectation(X) :- revente(X).
affectation(X) :- heritage(X).

% ============================================================
% SECTION 4 — TAXONOMIE DES DOSSIERS
% ============================================================

dossier(X) :- dossier_actif(X).
dossier(X) :- dossier_suspect(X).

% ============================================================
% SECTION 5 — TAXONOMIE DES LIENS SOCIAUX
% ============================================================

lien_social(X, Y) :- lien_familial(X, Y).
lien_social(X, Y) :- lien_professionnel(X, Y).
lien_social(X, Y) :- lien_financier(X, Y).

% Symétrie des liens — via prédicats "_base" pour éviter la récursion infinie
:- discontiguous lien_familial_base/2, partage_telephone_base/2.
:- discontiguous partage_adresse_base/2, partage_iban_base/2.

lien_familial(X, Y)     :- lien_familial_base(X, Y).
lien_familial(X, Y)     :- lien_familial_base(Y, X), X \= Y.
partage_telephone(X, Y) :- partage_telephone_base(X, Y).
partage_telephone(X, Y) :- partage_telephone_base(Y, X), X \= Y.
partage_adresse(X, Y)   :- partage_adresse_base(X, Y).
partage_adresse(X, Y)   :- partage_adresse_base(Y, X), X \= Y.
partage_iban(X, Y)      :- partage_iban_base(X, Y).
partage_iban(X, Y)      :- partage_iban_base(Y, X), X \= Y.

% ============================================================
% SECTION 6 — AXIOMES DE DESCRIPTION LOGIC (AX-01 à AX-10)
% ============================================================

% AX-01 : Accaparement urbain (≥4 parcelles urbaines)
accapareur_urbain(X) :-
    citoyen(X),
    findall(P, (possede(X, P), parcelle_urbaine(P)), Ps),
    length(Ps, N),
    N >= 4.

% AX-02 : Accaparement rural (≥6 parcelles rurales)
accapareur_rural(X) :-
    citoyen(X),
    findall(P, (possede(X, P), parcelle_rurale(P)), Ps),
    length(Ps, N),
    N >= 6.

% AX-03 : Conflit d'intérêt direct
conflit_interet_direct(X) :-
    agent_public(X),
    traite(X, D),
    concerne_dossier(A, D),
    beneficiaire(X, A).

% AX-04 : Conflit d'intérêt indirect (via lien familial)
conflit_interet_indirect(X) :-
    agent_public(X),
    traite(X, D),
    concerne_dossier(A, D),
    beneficiaire(Y, A),
    lien_familial(X, Y),
    X \= Y.

% AX-05 : Suspect prête-nom (partage de téléphone + multi-propriété)
suspect_prete_nom(X) :-
    acteur(X),
    partage_telephone(X, Y),
    X \= Y,
    findall(P, possede(X, P), Ps),
    length(Ps, N),
    N >= 2.

% AX-06 : Réseau familial suspect (famille de famille avec parcelles)
reseau_familial_suspect(X) :-
    acteur(X),
    lien_familial(X, Y),
    lien_familial(Y, Z),
    X \= Z,
    possede(Z, _),
    findall(P, possede(X, P), Ps),
    length(Ps, N),
    N >= 2.

% AX-07 : Spéculateur foncier (a vendu + possède encore ≥3 parcelles)
speculateur_foncier(X) :-
    acteur(X),
    vend_a(X, _),
    findall(P, possede(X, P), Ps),
    length(Ps, N),
    N >= 3.

% AX-08 : Promoteur fantôme (pas d'adresse/tel vérifiable + ≥5 parcelles)
promoteur_fantome(X) :-
    promoteur(X),
    \+ partage_adresse(X, _),
    \+ partage_telephone(X, _),
    findall(P, possede(X, P), Ps),
    length(Ps, N),
    N >= 5.

% AX-09 : Dossier suspect (bénéficiaire = agent public)
marquer_dossier_suspect(D) :-
    dossier(D),
    concerne_dossier(A, D),
    beneficiaire(AP, A),
    agent_public(AP).

% AX-10 : Blanchiment circulaire (A -> B -> C -> A)
reseau_blanchiment_circulaire(X) :-
    acteur(X),
    vend_a(X, Y),
    vend_a(Y, Z),
    vend_a(Z, X),
    X \= Y, Y \= Z, X \= Z.

% ============================================================
% SECTION 7 — CONTRAINTES D'INTÉGRITÉ (CI-1 à CI-8)
% ============================================================

% CI-1 : Un agent ne peut traiter son propre dossier
verifier_ci1 :-
    forall(
        (agent_public(X), traite(X, D), concerne_dossier(A, D), beneficiaire(X, A)),
        format("[VIOLATION CI-1] Agent ~w traite son propre dossier ~w !~n", [X, D])
    ).

% CI-2 : Max 3 parcelles urbaines par citoyen
verifier_ci2 :-
    forall(
        citoyen(X),
        (
            findall(P, (possede(X, P), parcelle_urbaine(P)), Ps),
            length(Ps, N),
            (N > 3 ->
                format("[VIOLATION CI-2] Citoyen ~w possède ~w parcelles urbaines (max 3) !~n", [X, N])
            ;   true)
        )
    ).

% CI-3 : Unicité du titre (une parcelle = un seul propriétaire)
verifier_ci3 :-
    forall(
        parcelle(P),
        (
            findall(X, possede(X, P), Xs),
            length(Xs, N),
            (N > 1 ->
                format("[VIOLATION CI-3] Parcelle ~w a ~w propriétaires : ~w !~n", [P, N, Xs])
            ;   true)
        )
    ).

% CI-4 : Délai minimal de revente (≥365 jours)
verifier_ci4 :-
    forall(
        (possede(X, P), date_acquisition(X, P, DA), date_revente(X, P, DR)),
        (
            Duree is DR - DA,
            (Duree < 365 ->
                format("[VIOLATION CI-4] ~w a revendu ~w en ~w jours (min 365) !~n", [X, P, Duree])
            ;   true)
        )
    ).

% CI-5 : Partage de téléphone → suspicion de prête-nom
verifier_ci5 :-
    forall(
        (partage_telephone(X, Y), X \= Y),
        format("[ALERTE CI-5] ~w et ~w partagent le même téléphone → suspect prête-nom~n", [X, Y])
    ).

% CI-6 : Interdiction de traitement familial
verifier_ci6 :-
    forall(
        (agent_public(X), lien_familial(X, Y), traite(X, D),
         concerne_dossier(A, D), beneficiaire(Y, A)),
        format("[VIOLATION CI-6] Agent ~w traite un dossier bénéficiant à son parent ~w !~n", [X, Y])
    ).

% CI-7 : Partage d'adresse entre non-apparentés → suspicion
verifier_ci7 :-
    forall(
        (partage_adresse(X, Y), X \= Y, \+ lien_familial(X, Y)),
        format("[ALERTE CI-7] ~w et ~w partagent une adresse sans lien familial → suspect~n", [X, Y])
    ).

% CI-8 : Cumul excessif de dossiers pour un notaire
nb_max_dossiers_notaire(10).

verifier_ci8 :-
    nb_max_dossiers_notaire(Max),
    forall(
        notaire(X),
        (
            findall(D, traite(X, D), Ds),
            length(Ds, N),
            (N > Max ->
                format("[VIOLATION CI-8] Notaire ~w gère ~w dossiers (max ~w) !~n", [X, N, Max])
            ;   true)
        )
    ).

% ============================================================
% SECTION 8 — VÉRIFICATION GLOBALE DE TOUTES LES CONTRAINTES
% ============================================================

verifier_toutes_contraintes :-
    format("~n=== VÉRIFICATION DES CONTRAINTES D'INTÉGRITÉ ===~n"),
    verifier_ci1,
    verifier_ci2,
    verifier_ci3,
    verifier_ci4,
    verifier_ci5,
    verifier_ci6,
    verifier_ci7,
    verifier_ci8,
    format("=== FIN DE VÉRIFICATION ===~n~n").

% ============================================================
% SECTION 9 — FAITS EXEMPLES (Instances de démonstration)
% ============================================================

% Acteurs
citoyen(abdou).
citoyen(fatima).
citoyen(moussa).
citoyen(salif).
agent_public(konate).
agent_public(traore).
promoteur(immo_sarl).
notaire(maitre_diallo).

% Parcelles
parcelle_urbaine(p1). parcelle_urbaine(p2). parcelle_urbaine(p3).
parcelle_urbaine(p4). parcelle_urbaine(p5).
parcelle_rurale(r1). parcelle_rurale(r2).

% Possessions (abdou accapare les urbaines → AX-01)
possede(abdou, p1). possede(abdou, p2).
possede(abdou, p3). possede(abdou, p4).
possede(fatima, p5).
possede(moussa, r1). possede(moussa, r2).

% Liens familiaux
lien_familial_base(abdou, fatima).
lien_familial_base(fatima, moussa).

% Partage de téléphone (suspect prête-nom → AX-05 / CI-5)
partage_telephone_base(abdou, salif).

% Dossiers et affectations
dossier_actif(d1). dossier_actif(d2).
attribution(a1). revente(a2).
concerne_dossier(a1, d1).
concerne_dossier(a2, d2).

% Traitement et bénéficiaires
traite(konate, d1).
beneficiaire(konate, a1).   % → Conflit d'intérêt direct (AX-03)

traite(traore, d2).
beneficiaire(fatima, a2).   % traore traite, fatima (parent de ?) est bénéficiaire

% Reventes
vend_a(fatima, moussa).
vend_a(moussa, salif).
vend_a(salif, abdou).  % → Blanchiment circulaire si abdou vend à fatima
vend_a(abdou, fatima). % boucle : AX-10 activé
vend_a(moussa, abdou). % circuit court : abdou→fatima→moussa→abdou ✓ (AX-10)

% Dates (format numérique simplifié : jours depuis époque)
date_acquisition(fatima, p5, 1000).
date_revente(fatima, p5, 1050).   % → 50 jours : violation CI-4

% Valeurs (achat / revente) pour tester B2
valeur(fatima-achat-p5, 5000).
valeur(fatima-revente-p5, 12000). % ratio = 2.4 → plus-value anormale

% Liens professionnels (pour tester C4)
lien_professionnel(maitre_diallo, immo_sarl).
beneficiaire(immo_sarl, a2).
traite(maitre_diallo, d2).