% ============================================================
%  LandGuard Neuro-Symbolic AI
%  inference_engine.pl — Moteur d'inférence (Partie 2)
%  Charge les règles, les applique et produit les alertes
% ============================================================

:- use_module(library(lists)).

% Charger les dépendances
:- ensure_loaded('knowledge_base.pl').
:- ensure_loaded('rules.pl').
:- ensure_loaded('explainability.pl').

% ============================================================
% SECTION 1 — ÉVALUATION D'UN ACTEUR
% ============================================================

% Évalue toutes les règles pour un acteur X et retourne la liste des alertes
evaluer_acteur(X, Alertes) :-
    findall(alerte(cat_a, ID, X, M), regle_A(ID, X, M), AlertesA),
    findall(alerte(cat_b, ID, X, M), regle_B(ID, X, M), AlertesB),
    findall(alerte(cat_c, ID, X, M), regle_C(ID, X, M), AlertesC),
    findall(alerte(cat_d, ID, X, M), regle_D(ID, X, M), AlertesD),
    append([AlertesA, AlertesB, AlertesC, AlertesD], Alertes).

% ============================================================
% SECTION 2 — SCORE DE SUSPICION
% ============================================================

% Poids par catégorie (modifiable)
poids_categorie(cat_a, 3).   % Accaparement    → impact élevé
poids_categorie(cat_b, 2).   % Spéculation     → impact moyen
poids_categorie(cat_c, 4).   % Conflit intérêt → impact très élevé
poids_categorie(cat_d, 3).   % Réseau/prête-nom → impact élevé

% Calculer le score de suspicion total pour un acteur
score_suspicion(X, Score) :-
    evaluer_acteur(X, Alertes),
    findall(W,
        (member(alerte(Cat, _, _, _), Alertes), poids_categorie(Cat, W)),
        Poids),
    sumlist(Poids, Score).

% Niveau de risque selon le score
niveau_risque(Score, faible)   :- Score =:= 0.
niveau_risque(Score, moyen)    :- Score > 0,  Score =< 5.
niveau_risque(Score, eleve)    :- Score > 5,  Score =< 10.
niveau_risque(Score, critique) :- Score > 10.

% ============================================================
% SECTION 3 — ANALYSE COMPLÈTE D'UN ACTEUR
% ============================================================

analyser_acteur(X) :-
    format("~n~`=t~60|~n"),
    format("  ANALYSE : ~w~n", [X]),
    format("~`=t~60|~n"),
    evaluer_acteur(X, Alertes),
    (Alertes = [] ->
        format("  [OK] Aucune alerte detectee.~n")
    ;
        length(Alertes, NbAlertes),
        format("  Alertes detectees : ~w~n", [NbAlertes]),
        forall(
            member(alerte(Cat, ID, _, Motif), Alertes),
            (
                journaliser(X, ID, Cat, Motif),
                format("  >> ~w~n", [Motif])
            )
        )
    ),
    score_suspicion(X, Score),
    niveau_risque(Score, Niveau),
    format("~n  Score de suspicion : ~w | Niveau : ~w~n", [Score, Niveau]),
    format("~`-t~60|~n").

% ============================================================
% SECTION 4 — ANALYSE GLOBALE (tous les acteurs)
% ============================================================

analyser_tous :-
    format("~n~`*t~60|~n"),
    format("  LANDGUARD — ANALYSE GLOBALE DU SYSTEME~n"),
    format("~`*t~60|~n~n"),
    findall(X, acteur(X), Acteurs),
    sort(Acteurs, ActeursUniq),
    forall(member(X, ActeursUniq), analyser_acteur(X)),
    format("~n~`*t~60|~n"),
    format("  FIN D ANALYSE~n"),
    format("~`*t~60|~n~n").

% ============================================================
% SECTION 5 — RAPPORT DE SYNTHÈSE
% ============================================================

rapport_synthese :-
    format("~n=== RAPPORT DE SYNTHESE ===~n~n"),
    findall(X, acteur(X), Acteurs),
    sort(Acteurs, ActeursUniq),
    forall(
        member(X, ActeursUniq),
        (
            score_suspicion(X, Score),
            niveau_risque(Score, Niveau),
            (Score > 0 ->
                format("  [~w] ~w — Score: ~w~n", [Niveau, X, Score])
            ;   true)
        )
    ),
    % Acteurs critiques
    findall(X-S,
        (acteur(X), score_suspicion(X, S), S > 10),
        Critiques),
    (Critiques \= [] ->
        format("~n  !! ACTEURS CRITIQUES : ~w !!~n", [Critiques])
    ;   format("~n  Aucun acteur critique.~n")),
    format("~n=== FIN DU RAPPORT ===~n").

% ============================================================
% SECTION 6 — RECHERCHE PAR CATÉGORIE
% ============================================================

% Tous les acteurs déclenchant des règles d'accaparement
suspects_accaparement(Xs) :-
    findall(X, (acteur(X), regle_A(_, X, _)), Xs0),
    sort(Xs0, Xs).

% Tous les acteurs déclenchant des règles de spéculation
suspects_speculation(Xs) :-
    findall(X, (acteur(X), regle_B(_, X, _)), Xs0),
    sort(Xs0, Xs).

% Tous les acteurs en conflit d'intérêt
suspects_conflit(Xs) :-
    findall(X, (acteur(X), regle_C(_, X, _)), Xs0),
    sort(Xs0, Xs).

% Tous les acteurs de réseaux suspects
suspects_reseau(Xs) :-
    findall(X, (acteur(X), regle_D(_, X, _)), Xs0),
    sort(Xs0, Xs).

% Pour lancer l'analyse : taper dans l'interpréteur => ?- analyser_tous.