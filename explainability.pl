% ============================================================
%  LandGuard Neuro-Symbolic AI
%  explainability.pl — Module XAI (Partie 2)
%  Journalisation, traces logiques et explications textuelles
% ============================================================

:- use_module(library(lists)).

% ============================================================
% SECTION 1 — JOURNAL DES ALERTES (en mémoire)
% ============================================================

:- dynamic journal_alerte/5.
% journal_alerte(Timestamp, Acteur, RegleID, Categorie, Motif)

% Journaliser une alerte
journaliser(Acteur, RegleID, Categorie, Motif) :-
    get_time(TS),
    (journal_alerte(TS, Acteur, RegleID, Categorie, Motif) -> true
    ;   assertz(journal_alerte(TS, Acteur, RegleID, Categorie, Motif))).

% Vider le journal
vider_journal :-
    retractall(journal_alerte(_, _, _, _, _)).

% ============================================================
% SECTION 2 — AFFICHAGE DES TRACES LOGIQUES
% ============================================================

% Trace détaillée pour une règle déclenchée
trace_regle(a1, X) :-
    findall(P, (possede(X, P), parcelle_urbaine(P)), Ps), length(Ps, N),
    format("  TRACE A1 : citoyen(~w) | parcelles_urbaines=~w | seuil=4 | N=~w~n", [X, Ps, N]).

trace_regle(a2, X) :-
    findall(P, (possede(X, P), parcelle_rurale(P)), Ps), length(Ps, N),
    format("  TRACE A2 : citoyen(~w) | parcelles_rurales=~w | seuil=6 | N=~w~n", [X, Ps, N]).

trace_regle(a3, X) :-
    findall(M, lien_familial(X, M), Ms),
    format("  TRACE A3 : ~w | famille=~w | concentration_familiale~n", [X, Ms]).

trace_regle(a4, X) :-
    findall(P, possede(X, P), Ps),
    format("  TRACE A4 : ~w | toutes_parcelles=~w | concentration_zonale~n", [X, Ps]).

trace_regle(b1, X) :-
    findall(P-D,
        (date_acquisition(X,P,DA), date_revente(X,P,DR), D is DR-DA, D < 180),
        Cas),
    format("  TRACE B1 : ~w | reventes_rapides=~w~n", [X, Cas]).

trace_regle(b2, X) :-
    findall(P-R,
        (valeur(X-achat-P,VA), valeur(X-revente-P,VR), R is VR/VA, R > 2.0),
        Cas),
    format("  TRACE B2 : ~w | plus_values_anormales=~w~n", [X, Cas]).

trace_regle(b3, X) :-
    findall(P, possede(X, P), Ps), findall(Y, vend_a(X, Y), Ys),
    format("  TRACE B3 : ~w | possede=~w | a_vendu_a=~w~n", [X, Ps, Ys]).

trace_regle(b4, X) :-
    findall(P, (possede(X,P), \+ date_revente(X,P,_)), Ps),
    format("  TRACE B4 : ~w | parcelles_inactives=~w~n", [X, Ps]).

trace_regle(c1, X) :-
    findall(D-A,
        (traite(X,D), concerne_dossier(A,D), beneficiaire(X,A)),
        Cas),
    format("  TRACE C1 : agent_public(~w) | dossiers_auto_attribues=~w~n", [X, Cas]).

trace_regle(c2, X) :-
    findall(Y-D,
        (traite(X,D), concerne_dossier(A,D), beneficiaire(Y,A), lien_familial(X,Y)),
        Cas),
    format("  TRACE C2 : agent_public(~w) | dossiers_familiaux=~w~n", [X, Cas]).

trace_regle(c3, X) :-
    findall(D, traite(X, D), Ds),
    format("  TRACE C3 : agent_public(~w) | tous_dossiers=~w~n", [X, Ds]).

trace_regle(c4, X) :-
    findall(Y-D,
        (traite(X,D), concerne_dossier(A,D), beneficiaire(Y,A),
         (lien_familial(X,Y) ; lien_professionnel(X,Y))),
        Cas),
    format("  TRACE C4 : notaire(~w) | dossiers_conflit=~w~n", [X, Cas]).

trace_regle(d1, X) :-
    findall(Y, partage_telephone(X, Y), Ys),
    format("  TRACE D1 : ~w | partage_telephone_avec=~w~n", [X, Ys]).

trace_regle(d2, X) :-
    findall(Y, (partage_adresse(X,Y), \+ lien_familial(X,Y)), Ys),
    format("  TRACE D2 : ~w | partage_adresse_non_famille=~w~n", [X, Ys]).

trace_regle(d3, X) :-
    findall(Y-Z,
        (vend_a(X,Y), vend_a(Y,Z), vend_a(Z,X), X\=Y, Y\=Z),
        Cycles),
    format("  TRACE D3 : ~w | cycles_detectes=~w~n", [X, Cycles]).

trace_regle(d4, X) :-
    findall(Y, partage_iban(X, Y), Ys),
    format("  TRACE D4 : ~w | partage_iban_avec=~w~n", [X, Ys]).

trace_regle(d5, X) :-
    findall(Y, (lien_familial(X,Y), partage_telephone(X,Y)), Ys),
    format("  TRACE D5 : ~w | famille_et_tel_partage=~w~n", [X, Ys]).

% Trace générique pour règles sans trace spécifique
trace_regle(ID, X) :-
    format("  TRACE ~w : acteur=~w | (trace generique)~n", [ID, X]).

% ============================================================
% SECTION 3 — EXPLICATION TEXTUELLE NORMÉE
% ============================================================

% Textes d'explication par règle (format juridique/administratif)
explication_regle(a1,
    "ACCAPAREMENT URBAIN : L article CI-2 limite la possession a 3 parcelles urbaines \
par citoyen. Ce seuil est depasse, constituant une infraction aux regles de distribution equitable.").

explication_regle(a2,
    "ACCAPAREMENT RURAL : La concentration excessive de terres rurales nuit a la \
redistribution agraire equitable et viole les principes de la reforme fonciere.").

explication_regle(a3,
    "MULTIPROPRIETE FAMILIALE : Le contournement du plafond de propriete via des membres \
de la famille constitue une fraude structuree au dispositif anti-accaparement.").

explication_regle(a4,
    "CONCENTRATION ZONALE : La possession de plusieurs parcelles dans une meme zone \
geographique sugere une strategie de monopolisation fonciere locale.").

explication_regle(b1,
    "REVENTE ULTRA-RAPIDE : Une revente en moins de 180 jours apres acquisition constitue \
un indicateur fort de speculation sans mise en valeur reelle du bien.").

explication_regle(b2,
    "PLUS-VALUE ANORMALE : Un ratio de revente superieur a 2x le prix d achat sans \
justification travaux indique une manipulation artificielle des prix fonciers.").

explication_regle(b3,
    "SPECULATEUR FONCIER : La combinaison de reventes anterieures et d un portefeuille \
actuel important caracterise un profil de speculateur foncier systematique.").

explication_regle(b4,
    "NON-MISE EN VALEUR : Une parcelle detenue sans transaction ni construction depuis \
plus de 5 ans constitue une retention fonciere abusive au detriment de l interet public.").

explication_regle(c1,
    "AUTO-ATTRIBUTION (CI-1) : Violation directe de l article CI-1. Un agent public ne \
peut etre a la fois instructeur et beneficiaire d un meme dossier foncier.").

explication_regle(c2,
    "CONFLIT FAMILIAL (CI-6) : Violation de l article CI-6. Le traitement d un dossier \
au profit d un membre de la famille de l agent constitue un conflit d interet indirect.").

explication_regle(c3,
    "FAVORITISME REPETE : Le traitement systematique de dossiers beneficiant aux memes \
personnes par un agent public caracterise un abus de position et un favoritisme institutionnel.").

explication_regle(c4,
    "CONFLIT NOTARIAL : Un notaire instrumentant des actes au profit de son propre reseau \
relationnel viole les regles de neutralite et d independance professionnelle.").

explication_regle(d1,
    "SUSPECT PRETE-NOM (CI-5) : Violation de CI-5. Le partage d un meme numero de \
telephone entre deux proprietaires distincts constitue une forte presomption de prête-nom.").

explication_regle(d2,
    "COORDINATION SUSPECTE (CI-7) : Violation de CI-7. Une adresse commune entre \
personnes non apparentees suggere une coordination organisee dans un reseau de fraude.").

explication_regle(d3,
    "BLANCHIMENT CIRCULAIRE (AX-10) : Un circuit de reventes en boucle entre plusieurs \
acteurs constitue le schema classique de blanchiment de fonds par la pierre.").

explication_regle(d4,
    "COORDINATION FINANCIERE : Le partage d un meme IBAN entre acheteurs distincts \
suggere l existence d un compte commun utilise pour masquer l origine des fonds.").

explication_regle(d5,
    "RESEAU FAMILIAL PRETE-NOM : La combinaison lien familial + telephone partage + \
multi-propriete caracterise un reseau de prête-noms organise au sein d une cellule familiale.").

% ============================================================
% SECTION 4 — RAPPORT XAI COMPLET POUR UN ACTEUR
% ============================================================

expliquer_acteur(X) :-
    format("~n~`=t~65|~n"),
    format("  RAPPORT XAI — ACTEUR : ~w~n", [X]),
    format("~`=t~65|~n"),
    % Collecter toutes les alertes
    findall(cat_a-ID-M, regle_A(ID, X, M), AA),
    findall(cat_b-ID-M, regle_B(ID, X, M), AB),
    findall(cat_c-ID-M, regle_C(ID, X, M), AC),
    findall(cat_d-ID-M, regle_D(ID, X, M), AD),
    append([AA, AB, AC, AD], Toutes),
    (Toutes = [] ->
        format("  [PROPRE] Aucune anomalie detectee pour ~w.~n", [X])
    ;
        forall(
            member(Cat-ID-Motif, Toutes),
            (
                format("~n  [~w | ~w]~n", [Cat, ID]),
                format("  ALERTE  : ~w~n", [Motif]),
                format("  TRACE   : "),
                trace_regle(ID, X),
                (explication_regle(ID, Expl) ->
                    format("  EXPLICATION JURIDIQUE :~n    ~w~n", [Expl])
                ;   true),
                journaliser(X, ID, Cat, Motif)
            )
        )
    ),
    format("~`-t~65|~n").

% ============================================================
% SECTION 5 — EXPORT DU JOURNAL
% ============================================================

afficher_journal :-
    format("~n=== JOURNAL DES ALERTES ENREGISTREES ===~n"),
    (journal_alerte(_, _, _, _, _) ->
        forall(
            journal_alerte(TS, Acteur, ID, Cat, Motif),
            format("  [~2f] ~w | ~w | ~w | ~w~n", [TS, Acteur, ID, Cat, Motif])
        )
    ;
        format("  (journal vide)~n")
    ),
    format("=== FIN DU JOURNAL ===~n~n").

% ============================================================
% SECTION 6 — EXPLICATION GLOBALE (tous les acteurs suspects)
% ============================================================

expliquer_tous_suspects :-
    format("~n~`*t~65|~n"),
    format("  LANDGUARD XAI — EXPLICATIONS COMPLETES~n"),
    format("~`*t~65|~n"),
    findall(X, acteur(X), Acteurs),
    sort(Acteurs, ActeursUniq),
    forall(
        member(X, ActeursUniq),
        (
            findall(_, (regle_A(_,X,_) ; regle_B(_,X,_) ;
                        regle_C(_,X,_) ; regle_D(_,X,_)), Alertes),
            (Alertes \= [] -> expliquer_acteur(X) ; true)
        )
    ).
