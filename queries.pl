% ============================================================
%  LandGuard Neuro-Symbolic AI
%  queries.pl — Requêtes ProbLog & Classification du risque
%  Partie 3 — Raisonnement Probabiliste
% ============================================================
%
%  Ce fichier contient :
%   1. Les requêtes ProbLog (query/1)
%   2. Un script Python (en commentaire) pour lancer ProbLog
%      et classifier automatiquement les résultats
% ============================================================

% ── Requêtes par type de fraude ─────────────────────────────

% Prête-nom
query(prete_nom(abdou,   salif)).
query(prete_nom(salif,   abdou)).
query(prete_nom(abdou,   fatima)).
query(prete_nom(maitre_diallo, immo_sarl)).

% Spéculation
query(speculateur(fatima)).
query(speculateur(moussa)).
query(speculateur(abdou)).

% Accaparement
query(accapareur(abdou)).
query(accapareur(fatima)).

% Conflit d'intérêt
query(conflit_interet(konate)).
query(conflit_interet(traore)).
query(conflit_interet(maitre_diallo)).

% Blanchiment
query(blanchiment(abdou)).
query(blanchiment(fatima)).
query(blanchiment(immo_sarl)).

% Fraude composite
query(fraude_composite(konate)).
query(fraude_composite(abdou)).
query(fraude_composite(fatima)).

% ============================================================
%
%  CLASSIFICATION DU RISQUE (échelle à 4 niveaux)
%
%  Probabilité obtenue  →  Niveau de risque
%  ─────────────────────────────────────────
%  < 0.30               →  FAIBLE   (vert)
%  0.30 – 0.60          →  MOYEN    (jaune)
%  0.60 – 0.80          →  ÉLEVÉ    (orange)
%  > 0.80               →  CRITIQUE (rouge)
%
% ============================================================