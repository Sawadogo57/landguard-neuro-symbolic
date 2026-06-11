% ============================================================
%  LandGuard Neuro-Symbolic AI
%  rules.pl — Règles logiques (Partie 2)
%  15 règles réparties en 4 catégories
% ============================================================

:- discontiguous regle_A/3, regle_B/3, regle_C/3, regle_D/3.
:- use_module(library(lists)).

% ============================================================
% CATÉGORIE A — ACCAPAREMENT & CONCENTRATION IMMOBILIÈRE
% ============================================================

% A1 : Accaparement urbain direct (≥4 parcelles urbaines)
regle_A(a1, X, Motif) :-
    citoyen(X),
    findall(P, (possede(X, P), parcelle_urbaine(P)), Ps),
    length(Ps, N), N >= 4,
    format(atom(Motif),
        "[A1] ~w possede ~w parcelles urbaines (seuil=4) => ACCAPAREMENT URBAIN", [X, N]).

% A2 : Accaparement rural direct (≥6 parcelles rurales)
regle_A(a2, X, Motif) :-
    citoyen(X),
    findall(P, (possede(X, P), parcelle_rurale(P)), Ps),
    length(Ps, N), N >= 6,
    format(atom(Motif),
        "[A2] ~w possede ~w parcelles rurales (seuil=6) => ACCAPAREMENT RURAL", [X, N]).

% A3 : Multipropriété familiale (somme des parcelles d'une famille ≥6)
regle_A(a3, X, Motif) :-
    citoyen(X),
    findall(M, lien_familial_base(X, M), Membres),
    findall(P, possede(X, P), PsX),
    findall(P, (member(M, Membres), possede(M, P)), PsF),
    append(PsX, PsF, Tous),
    sort(Tous, TousUniq),
    length(TousUniq, Total),
    Total >= 4,
    format(atom(Motif),
        "[A3] Famille de ~w controle ~w parcelles au total => MULTIPROPRIETE FAMILIALE",
        [X, Total]).

% A4 : Concentration dans une même zone (≥3 parcelles contiguës ou même zone)
regle_A(a4, X, Motif) :-
    acteur(X),
    findall(P, possede(X, P), Ps),
    findall(P, (member(P, Ps), parcelle_urbaine(P)), PsU),
    length(PsU, Nu),
    findall(P, (member(P, Ps), parcelle_rurale(P)), PsR),
    length(PsR, Nr),
    (Nu >= 3 ; Nr >= 3),
    format(atom(Motif),
        "[A4] ~w : ~w parcelles urbaines / ~w rurales => CONCENTRATION ZONALE SUSPECTE",
        [X, Nu, Nr]).

% ============================================================
% CATÉGORIE B — SPÉCULATION FONCIÈRE
% ============================================================

% B1 : Revente ultra-rapide (< 180 jours)
regle_B(b1, X, Motif) :-
    acteur(X),
    date_acquisition(X, P, DA),
    date_revente(X, P, DR),
    Duree is DR - DA,
    Duree < 180,
    format(atom(Motif),
        "[B1] ~w a revendu ~w en ~w jours (seuil=180) => REVENTE ULTRA-RAPIDE", [X, P, Duree]).

% B2 : Plus-value anormale (valeur revente > 2x valeur achat)
regle_B(b2, X, Motif) :-
    acteur(X),
    valeur(X-achat-P, VA),
    valeur(X-revente-P, VR),
    Ratio is VR / VA,
    Ratio > 2.0,
    format(atom(Motif),
        "[B2] ~w : ratio plus-value=~2f sur ~w (seuil=2.0) => PLUS-VALUE ANORMALE",
        [X, Ratio, P]).

% B3 : Spéculateur foncier (a vendu ET possède encore ≥3 parcelles)
regle_B(b3, X, Motif) :-
    acteur(X),
    vend_a(X, _),
    findall(P, possede(X, P), Ps),
    length(Ps, N), N >= 3,
    format(atom(Motif),
        "[B3] ~w a vendu des parcelles et en possede encore ~w => SPECULATEUR FONCIER",
        [X, N]).

% B4 : Non mise en valeur (parcelle possédée > 5 ans sans transaction ni construction)
regle_B(b4, X, Motif) :-
    acteur(X),
    possede(X, P),
    date_acquisition(X, P, DA),
    \+ date_revente(X, P, _),
    \+ vend_a(X, _),
    Inactivite is 2000 - DA,   % 2000 = jour courant simulé
    Inactivite > 1825,          % > 5 ans
    format(atom(Motif),
        "[B4] ~w : parcelle ~w inactive depuis ~w jours => NON-MISE EN VALEUR",
        [X, P, Inactivite]).

% ============================================================
% CATÉGORIE C — CONFLITS D'INTÉRÊTS
% ============================================================

% C1 : Auto-attribution (agent traite dossier dont il est bénéficiaire)
regle_C(c1, X, Motif) :-
    agent_public(X),
    traite(X, D),
    concerne_dossier(A, D),
    beneficiaire(X, A),
    format(atom(Motif),
        "[C1] Agent ~w traite le dossier ~w dont il est lui-meme beneficiaire => AUTO-ATTRIBUTION",
        [X, D]).

% C2 : Traitement de dossier familial (agent + parent bénéficiaire)
regle_C(c2, X, Motif) :-
    agent_public(X),
    traite(X, D),
    concerne_dossier(A, D),
    beneficiaire(Y, A),
    lien_familial(X, Y),
    X \= Y,
    format(atom(Motif),
        "[C2] Agent ~w traite le dossier ~w beneficiant son parent ~w => CONFLIT FAMILIAL",
        [X, D, Y]).

% C3 : Favoristisme répétitif (agent traite ≥3 dossiers en faveur d'un même acteur)
regle_C(c3, X, Motif) :-
    agent_public(X),
    findall(D, traite(X, D), Ds),
    length(Ds, N), N >= 3,
    format(atom(Motif),
        "[C3] Agent ~w a traite ~w dossiers (>=3) => FAVORITISME REPETE SUSPECT",
        [X, N]).

% C4 : Conflit d'intérêt via notaire lié (notaire instrumente pour son réseau)
regle_C(c4, X, Motif) :-
    notaire(X),
    traite(X, D),
    concerne_dossier(A, D),
    beneficiaire(Y, A),
    (lien_familial(X, Y) ; lien_professionnel(X, Y)),
    format(atom(Motif),
        "[C4] Notaire ~w instrumente le dossier ~w pour son contact ~w => CONFLIT NOTARIAL",
        [X, D, Y]).

% ============================================================
% CATÉGORIE D — RÉSEAUX & PRÊTE-NOMS
% ============================================================

% D1 : Prête-nom via partage de téléphone
regle_D(d1, X, Motif) :-
    acteur(X),
    partage_telephone(X, Y),
    X \= Y,
    findall(P, possede(X, P), PsX),
    findall(P, possede(Y, P), PsY),
    length(PsX, Nx), length(PsY, Ny),
    (Nx >= 1 ; Ny >= 1),
    format(atom(Motif),
        "[D1] ~w et ~w partagent un telephone (~w / ~w parcelles) => SUSPECT PRETE-NOM",
        [X, Y, Nx, Ny]).

% D2 : Coordination via adresse partagée entre non-apparentés
regle_D(d2, X, Motif) :-
    acteur(X),
    partage_adresse(X, Y),
    X \= Y,
    \+ lien_familial(X, Y),
    format(atom(Motif),
        "[D2] ~w et ~w partagent une adresse sans lien familial => COORDINATION SUSPECTE",
        [X, Y]).

% D3 : Réseau circulaire de reventes (A→B→B→A)
regle_D(d3, X, Motif) :-
    acteur(X),
    vend_a(X, Y), Y \= X,
    vend_a(Y, Z), Z \= Y, Z \= X,
    vend_a(Z, X),
    format(atom(Motif),
        "[D3] Circuit de revente : ~w->~w->~w->~w => RESEAU DE BLANCHIMENT CIRCULAIRE",
        [X, Y, Z, X]).

% D4 : IBAN partagé entre acheteurs distincts
regle_D(d4, X, Motif) :-
    acteur(X),
    partage_iban(X, Y),
    X \= Y,
    format(atom(Motif),
        "[D4] ~w et ~w partagent un IBAN => COORDINATION FINANCIERE SUSPECTE",
        [X, Y]).

% D5 : Réseau familial de prête-noms (famille + téléphones + multi-parcelles)
regle_D(d5, X, Motif) :-
    citoyen(X),
    lien_familial(X, Y),
    partage_telephone(X, Y),
    findall(P, (possede(X, P) ; possede(Y, P)), Ps),
    sort(Ps, PsU),
    length(PsU, N), N >= 3,
    format(atom(Motif),
        "[D5] ~w et son parent ~w : tel partage + ~w parcelles => RESEAU FAMILIAL PRETE-NOM",
        [X, Y, N]).