% ============================================================
%  LandGuard Neuro-Symbolic AI
%  probabilistic_rules.pl — Règles Probabilistes (Partie 3)
%  Raisonnement sous incertitude avec ProbLog
% ============================================================
%
%  INSTALLATION PROBLOG :
%  pip install problog
%  Exécution : python -m problog probabilistic_rules.pl
% ============================================================

% ============================================================
% SECTION 1 — FAITS DE BASE (instances terrain)
% ============================================================

% Acteurs
citoyen(abdou). citoyen(fatima). citoyen(moussa). citoyen(salif).
agent_public(konate). agent_public(traore).
promoteur(immo_sarl).
notaire(maitre_diallo).

% Parcelles
parcelle_urbaine(p1). parcelle_urbaine(p2).
parcelle_urbaine(p3). parcelle_urbaine(p4). parcelle_urbaine(p5).
parcelle_rurale(r1).  parcelle_rurale(r2).

% Propriétés
possede(abdou,  p1). possede(abdou,  p2).
possede(abdou,  p3). possede(abdou,  p4).
possede(fatima, p5).
possede(moussa, r1). possede(moussa, r2).

% Liens sociaux (faits bruts, symétrie gérée manuellement)
lien_familial_base(abdou,  fatima).
lien_familial_base(fatima, moussa).

lien_familial(X, Y) :- lien_familial_base(X, Y).
lien_familial(X, Y) :- lien_familial_base(Y, X), X \= Y.

% Coordinations
partage_telephone(abdou,  salif).
partage_telephone(salif,  abdou).
partage_adresse(immo_sarl, maitre_diallo).

% Transactions
vend_a(fatima,  moussa).
vend_a(moussa,  abdou).
vend_a(abdou,   fatima).   % circuit circulaire
lien_professionnel(maitre_diallo, immo_sarl).

% Dossiers
traite(konate,        d1).
traite(traore,        d2).
traite(maitre_diallo, d2).
concerne_dossier(a1, d1). concerne_dossier(a2, d2).
beneficiaire(konate,    a1).
beneficiaire(fatima,    a2).
beneficiaire(immo_sarl, a2).

% Données chiffrées (pour règles B)
revente_rapide(fatima).          % revendu en 50 jours
plus_value_anormale(fatima).     % ratio 2.4x
non_mis_en_valeur(moussa).       % parcelles rurales inactives

% ============================================================
% SECTION 2 — RÈGLES PROBABILISTES (clauses incertaines)
% ============================================================

% ── Groupe 1 : Prête-nom ────────────────────────────────────

% P=0.85 : Partage de téléphone entre acheteurs distincts → prête-nom très probable
0.85::prete_nom(X, Y) :- 
    partage_telephone(X, Y), 
    X \= Y,
    possede(X, _).

% P=0.75 : Partage d'adresse entre non-apparentés → coordination suspecte
0.75::prete_nom(X, Y) :- 
    partage_adresse(X, Y), 
    X \= Y,
    \+ lien_familial(X, Y).

% P=0.60 : Lien familial direct + multi-propriété → prête-nom familial
0.60::prete_nom(X, Y) :- 
    lien_familial(X, Y),
    possede(X, _),
    possede(Y, _).

% ── Groupe 2 : Spéculation ──────────────────────────────────

% P=0.80 : Revente rapide + plus-value anormale → spéculation avérée
0.80::speculateur(X) :- 
    revente_rapide(X), 
    plus_value_anormale(X).

% P=0.65 : Revente rapide seule → spéculation probable
0.65::speculateur(X) :- 
    revente_rapide(X),
    \+ plus_value_anormale(X).

% P=0.55 : Plus-value anormale seule → spéculation possible
0.55::speculateur(X) :- 
    plus_value_anormale(X),
    \+ revente_rapide(X).

% P=0.45 : Non mise en valeur prolongée → rétention spéculative possible
0.45::speculateur(X) :- 
    non_mis_en_valeur(X).

% ── Groupe 3 : Accaparement ─────────────────────────────────

% P=0.90 : ≥4 parcelles urbaines → accaparement quasi-certain
0.90::accapareur(X) :- 
    citoyen(X),
    findall(P, (possede(X,P), parcelle_urbaine(P)), Ps),
    length(Ps, N), N >= 4.

% P=0.70 : Réseau familial cumulant ≥4 parcelles → accaparement familial probable
0.70::accapareur(X) :- 
    citoyen(X),
    lien_familial(X, Y),
    possede(X, _), possede(Y, _),
    findall(P, (possede(X,P) ; possede(Y,P)), Ps),
    sort(Ps, PsU), length(PsU, N), N >= 4.

% ── Groupe 4 : Conflit d'intérêt ────────────────────────────

% P=0.95 : Auto-attribution directe → conflit d'intérêt quasi-certain
0.95::conflit_interet(X) :- 
    agent_public(X),
    traite(X, D),
    concerne_dossier(A, D),
    beneficiaire(X, A).

% P=0.80 : Traitement de dossier familial → conflit indirect fort
0.80::conflit_interet(X) :- 
    agent_public(X),
    traite(X, D),
    concerne_dossier(A, D),
    beneficiaire(Y, A),
    lien_familial(X, Y), X \= Y.

% P=0.75 : Notaire lié professionnellement au bénéficiaire → conflit probable
0.75::conflit_interet(X) :- 
    notaire(X),
    traite(X, D),
    concerne_dossier(A, D),
    beneficiaire(Y, A),
    lien_professionnel(X, Y).

% ── Groupe 5 : Blanchiment ──────────────────────────────────

% P=0.85 : Circuit circulaire de reventes → blanchiment probable
0.85::blanchiment(X) :- 
    vend_a(X, Y), vend_a(Y, Z), vend_a(Z, X),
    X \= Y, Y \= Z, X \= Z.

% P=0.65 : Accaparement + prête-nom détecté → blanchiment possible
0.65::blanchiment(X) :- 
    accapareur(X),
    prete_nom(X, _).

% P=0.50 : Promoteur sans identité stable avec beaucoup de parcelles
0.50::blanchiment(X) :- 
    promoteur(X),
    findall(P, possede(X,P), Ps),
    length(Ps, N), N >= 3.

% ── Groupe 6 : Fraude composite ─────────────────────────────

% P=0.92 : Conflit + prête-nom → fraude composite sévère
0.92::fraude_composite(X) :- 
    conflit_interet(X),
    prete_nom(X, _).

% P=0.88 : Accaparement + blanchiment → fraude composite grave
0.88::fraude_composite(X) :- 
    accapareur(X),
    blanchiment(X).

% P=0.78 : Spéculation + prête-nom → fraude composite probable
0.78::fraude_composite(X) :- 
    speculateur(X),
    prete_nom(X, _).

% ── Groupe 7 : Score global de fraude ───────────────────────

% Fraude globale = union pondérée de tous les signaux
fraude_globale(X) :- prete_nom(X, _).
fraude_globale(X) :- speculateur(X).
fraude_globale(X) :- accapareur(X).
fraude_globale(X) :- conflit_interet(X).
fraude_globale(X) :- blanchiment(X).
fraude_globale(X) :- fraude_composite(X).

% ============================================================
% SECTION 3 — REQUÊTES D'INFÉRENCE (query/1)
% ============================================================

% Requêtes individuelles par acteur et type de fraude
query(prete_nom(abdou,   salif)).
query(prete_nom(salif,   abdou)).
query(prete_nom(abdou,   fatima)).
query(prete_nom(maitre_diallo, immo_sarl)).

query(speculateur(fatima)).
query(speculateur(moussa)).
query(speculateur(abdou)).

query(accapareur(abdou)).
query(accapareur(fatima)).

query(conflit_interet(konate)).
query(conflit_interet(traore)).
query(conflit_interet(maitre_diallo)).

query(blanchiment(abdou)).
query(blanchiment(fatima)).
query(blanchiment(immo_sarl)).

query(fraude_composite(konate)).
query(fraude_composite(abdou)).
query(fraude_composite(fatima)).