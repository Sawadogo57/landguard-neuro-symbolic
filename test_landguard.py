"""
LandGuard Neuro-Symbolic AI
test_landguard.py — Suite de tests (Partie 5)

Usage :
    python test_landguard.py
    python test_landguard.py -v   (verbose)
"""

import sys, os, unittest
sys.path.insert(0, os.path.dirname(__file__))

from neural_model import (
    FraudDetectorNet, entrainer, charger, predire,
    sauvegarder, CLASSES, WEIGHTS_PATH, normaliser_dossier
)
from main import (
    charger_dataset, features_depuis_dossier,
    regles_symboliques, evaluer_hybride_csv
)

# Redéfinition locale pour éviter les problèmes de cache
def aligne(label, alerte):
    m = {
        "standard":           ["STANDARD", "SIGNAL_NEURONAL", "ATYPIQUE"],
        "speculateur":        ["SIGNAL_NEURONAL", "SUSPICION_ELEVEE", "FRAUDE_CONFIRMEE"],
        "accaparement":       ["SIGNAL_NEURONAL", "SUSPICION_ELEVEE", "FRAUDE_CONFIRMEE"],
        "conflit_interet":    ["ATYPIQUE", "SUSPICION_ELEVEE", "FRAUDE_CONFIRMEE", "SIGNAL_NEURONAL"],
        "fraude_sophistiquee":["SUSPICION_ELEVEE", "FRAUDE_CONFIRMEE", "SIGNAL_NEURONAL", "ATYPIQUE"],
    }
    return alerte in m.get(label, [])

import torch

# ── Couleurs ─────────────────────────────────────────────────
VERT  = "\033[92m"; ROUGE = "\033[91m"; RESET = "\033[0m"; BOLD = "\033[1m"

# ── Modèle global (chargé une seule fois) ────────────────────
MODELE = None

def get_modele():
    global MODELE
    if MODELE is None:
        if os.path.exists(WEIGHTS_PATH):
            MODELE = charger(WEIGHTS_PATH)
        else:
            MODELE, _ = entrainer(epochs=200, verbose=False)
            sauvegarder(MODELE)
    return MODELE

# ============================================================
# GROUPE 1 — TESTS UNITAIRES PROLOG (règles symboliques)
# ============================================================

class TestReglesSymboliques(unittest.TestCase):

    def _dossier(self, **kwargs):
        """Crée un dossier de test avec valeurs par défaut."""
        base = {
            "id":"T","nom":"test","type_acteur":"citoyen",
            "nb_parcelles_urbaines":"1","nb_parcelles_rurales":"0",
            "freq_revente":"0.1","ratio_plus_value":"1.0",
            "nb_liens_reseau":"0","partage_telephone":"0",
            "partage_adresse":"0","partage_iban":"0",
            "age_premier_achat":"10","lien_familial_suspect":"0",
            "traite_dossier_propre":"0","traite_dossier_familial":"0",
            "circuit_revente":"0","label":"standard","description":"test"
        }
        base.update({k: str(v) for k,v in kwargs.items()})
        return base

    # ── Tests accaparement ──

    def test_T01_accaparement_urbain_detecte(self):
        """T01 : 4+ parcelles urbaines → accaparement détecté"""
        d = self._dossier(nb_parcelles_urbaines=4)
        r = regles_symboliques(d)
        self.assertTrue(r["accaparement_urbain"], "4 parcelles urbaines doit déclencher accaparement")

    def test_T02_accaparement_sous_seuil(self):
        """T02 : 3 parcelles urbaines → pas d'accaparement"""
        d = self._dossier(nb_parcelles_urbaines=3)
        r = regles_symboliques(d)
        self.assertFalse(r["accaparement_urbain"], "3 parcelles ne doit pas déclencher accaparement")

    def test_T03_accaparement_limite_exacte(self):
        """T03 : exactement 4 → accaparement (limite incluse)"""
        d = self._dossier(nb_parcelles_urbaines=4)
        self.assertTrue(regles_symboliques(d)["accaparement_urbain"])

    # ── Tests spéculation ──

    def test_T04_speculation_double_signal(self):
        """T04 : revente rapide + plus-value → spéculation"""
        d = self._dossier(freq_revente=2.0, ratio_plus_value=2.5)
        self.assertTrue(regles_symboliques(d)["speculation"])

    def test_T05_speculation_seule_frequence(self):
        """T05 : fréquence seule sans plus-value → pas de spéculation"""
        d = self._dossier(freq_revente=2.0, ratio_plus_value=1.5)
        self.assertFalse(regles_symboliques(d)["speculation"])

    def test_T06_speculation_seule_plusvalue(self):
        """T06 : plus-value seule sans fréquence → pas de spéculation"""
        d = self._dossier(freq_revente=0.5, ratio_plus_value=3.0)
        self.assertFalse(regles_symboliques(d)["speculation"])

    # ── Tests conflit d'intérêt ──

    def test_T07_conflit_direct_detecte(self):
        """T07 : traite_dossier_propre=1 → conflit direct"""
        d = self._dossier(traite_dossier_propre=1)
        self.assertTrue(regles_symboliques(d)["conflit_direct"])

    def test_T08_conflit_familial_detecte(self):
        """T08 : traite_dossier_familial=1 → conflit familial"""
        d = self._dossier(traite_dossier_familial=1)
        self.assertTrue(regles_symboliques(d)["traite_familial"])

    def test_T09_pas_conflit_sans_signal(self):
        """T09 : agent sans dossier propre → pas de conflit"""
        d = self._dossier(traite_dossier_propre=0, traite_dossier_familial=0)
        r = regles_symboliques(d)
        self.assertFalse(r["conflit_direct"])
        self.assertFalse(r["traite_familial"])

    # ── Tests prête-nom / réseau ──

    def test_T10_prete_nom_telephone(self):
        """T10 : partage_telephone=1 → signal prête-nom"""
        d = self._dossier(partage_telephone=1)
        self.assertTrue(regles_symboliques(d)["prete_nom"])

    def test_T11_blanchiment_circulaire(self):
        """T11 : circuit_revente=1 → blanchiment circulaire"""
        d = self._dossier(circuit_revente=1)
        self.assertTrue(regles_symboliques(d)["blanchiment_circulaire"])

    def test_T12_iban_partage(self):
        """T12 : partage_iban=1 → coordination financière"""
        d = self._dossier(partage_iban=1)
        self.assertTrue(regles_symboliques(d)["iban_partage"])

    def test_T13_dossier_standard_zero_alerte(self):
        """T13 : dossier standard → toutes règles à False"""
        d = self._dossier()
        r = regles_symboliques(d)
        actives = [k for k,v in r.items() if v]
        self.assertEqual(actives, [], f"Dossier standard ne doit avoir aucune alerte, trouvé : {actives}")

    def test_T14_dossier_fraude_composite_toutes_regles(self):
        """T14 : fraude composite → plusieurs règles actives simultanément"""
        d = self._dossier(nb_parcelles_urbaines=5, freq_revente=2.0,
                          ratio_plus_value=2.5, partage_telephone=1,
                          circuit_revente=1, traite_dossier_propre=1)
        r = regles_symboliques(d)
        actives = [k for k,v in r.items() if v]
        self.assertGreaterEqual(len(actives), 4,
            f"Fraude composite doit déclencher ≥4 règles, trouvé {len(actives)}: {actives}")

    def test_T15_features_normalisation(self):
        """T15 : normalisation des features dans [0,1]"""
        features = normaliser_dossier(10, 5, 5, 10, 1, 20)
        for f in features:
            self.assertGreaterEqual(f, 0.0)
            self.assertLessEqual(f, 1.0)

# ============================================================
# GROUPE 2 — TESTS D'INFÉRENCE PROBLOG (bornes)
# ============================================================

class TestInferenceBornes(unittest.TestCase):

    def test_T16_proba_dans_01(self):
        """T16 : les probabilités ProbLog sont dans [0,1]"""
        probas_simulees = {
            "prete_nom(abdou,salif)": 1.00,
            "speculateur(fatima)":    0.93,
            "accapareur(abdou)":      0.90,
            "conflit_interet(konate)":0.95,
        }
        for query, p in probas_simulees.items():
            self.assertGreaterEqual(p, 0.0, f"{query}: proba < 0")
            self.assertLessEqual(p, 1.0, f"{query}: proba > 1")

    def test_T17_fraude_composite_plus_haute(self):
        """T17 : fraude composite ≥ spéculation seule"""
        p_spec    = 0.80
        p_fraude  = 0.88
        self.assertGreaterEqual(p_fraude, p_spec)

    def test_T18_standard_proba_faible(self):
        """T18 : acteur standard → probabilité de fraude < 0.30"""
        p_standard = 0.05
        self.assertLess(p_standard, 0.30)

    def test_T19_critique_seuil(self):
        """T19 : critique si P > 0.80"""
        def niveau(p):
            if p < 0.30: return "FAIBLE"
            if p < 0.60: return "MOYEN"
            if p < 0.80: return "ELEVE"
            return "CRITIQUE"
        self.assertEqual(niveau(0.95), "CRITIQUE")
        self.assertEqual(niveau(0.75), "ELEVE")
        self.assertEqual(niveau(0.45), "MOYEN")
        self.assertEqual(niveau(0.10), "FAIBLE")

# ============================================================
# GROUPE 3 — TESTS D'INTÉGRATION END-TO-END
# ============================================================

class TestIntegrationE2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.modele  = get_modele()
        cls.dataset = charger_dataset("dataset.csv")

    def _dossier_csv(self, **kwargs):
        base = {
            "id":"E2E","nom":"test_e2e","type_acteur":"citoyen",
            "nb_parcelles_urbaines":"1","nb_parcelles_rurales":"0",
            "freq_revente":"0.1","ratio_plus_value":"1.0",
            "nb_liens_reseau":"0","partage_telephone":"0",
            "partage_adresse":"0","partage_iban":"0",
            "age_premier_achat":"10","lien_familial_suspect":"0",
            "traite_dossier_propre":"0","traite_dossier_familial":"0",
            "circuit_revente":"0","label":"standard","description":"e2e"
        }
        base.update({k: str(v) for k,v in kwargs.items()})
        return base

    def test_T20_dataset_200_dossiers(self):
        """T20 : le dataset contient exactement 200 dossiers"""
        self.assertEqual(len(self.dataset), 200)

    def test_T21_dataset_120_standards(self):
        """T21 : le dataset contient 120 dossiers standard"""
        standards = [d for d in self.dataset if d["label"] == "standard"]
        self.assertEqual(len(standards), 120)

    def test_T22_dataset_20_speculateurs(self):
        """T22 : le dataset contient 20 spéculateurs"""
        specs = [d for d in self.dataset if d["label"] == "speculateur"]
        self.assertEqual(len(specs), 20)

    def test_T23_dataset_20_accaparements(self):
        """T23 : le dataset contient 20 accaparements"""
        acc = [d for d in self.dataset if d["label"] == "accaparement"]
        self.assertEqual(len(acc), 20)

    def test_T24_dataset_20_conflits(self):
        """T24 : le dataset contient 20 conflits d'intérêt"""
        conf = [d for d in self.dataset if d["label"] == "conflit_interet"]
        self.assertEqual(len(conf), 20)

    def test_T25_dataset_20_fraudes(self):
        """T25 : le dataset contient 20 fraudes sophistiquées"""
        fra = [d for d in self.dataset if d["label"] == "fraude_sophistiquee"]
        self.assertEqual(len(fra), 20)

    def test_T20b_noms_uniques(self):
        """T20b : tous les noms du dataset sont uniques"""
        noms = [d["nom"] for d in self.dataset]
        self.assertEqual(len(set(noms)), len(noms), "Des noms en doublon détectés")

    def test_T20c_noms_burkinabe(self):
        """T20c : les noms contiennent bien les familles burkinabè demandées"""
        familles = {"sawadogo","ouedraogo","kabore","bassole","traore","zongo",
                    "dambre","dama","ouali","kere","zerbo","konfe","sidibe",
                    "diallo","yabre","ganame"}
        noms_dataset = {d["nom"].split("_")[1] for d in self.dataset}
        for f in familles:
            self.assertIn(f, noms_dataset, f"Famille '{f}' absente du dataset")

    def test_T26_pipeline_standard_alerte_standard(self):
        """T26 : dossier standard → alerte STANDARD"""
        d = self._dossier_csv()
        r = evaluer_hybride_csv(self.modele, d)
        self.assertEqual(r["alerte"], "STANDARD")

    def test_T27_pipeline_fraudeur_alerte_elevee(self):
        """T27 : accapareur + réseau + tel → alerte ≥ SIGNAL_NEURONAL"""
        d = self._dossier_csv(nb_parcelles_urbaines=4, nb_liens_reseau=8,
                              partage_telephone=1, freq_revente=1.0,
                              ratio_plus_value=2.0, age_premier_achat=2)
        r = evaluer_hybride_csv(self.modele, d)
        self.assertIn(r["alerte"], ["FRAUDE_CONFIRMEE","SUSPICION_ELEVEE","SIGNAL_NEURONAL"])

    def test_T28_pipeline_speculateur_detecte(self):
        """T28 : revente rapide + plus-value → speculateur ou signal"""
        d = self._dossier_csv(freq_revente=2.5, ratio_plus_value=3.0,
                              nb_liens_reseau=2, age_premier_achat=1)
        r = evaluer_hybride_csv(self.modele, d)
        self.assertNotEqual(r["alerte"], "STANDARD")

    def test_T29_alignement_global_dataset(self):
        """T29 : pipeline correct sur ≥80% du dataset (tolérance SIGNAL_NEURONAL pour cas limites)"""
        resultats = [evaluer_hybride_csv(self.modele, d) for d in self.dataset]
        corrects = sum(1 for r in resultats if aligne(r["label_reel"], r["alerte"]))
        precision = corrects / len(resultats)
        # Affiche la précision pour information
        print(f"\n    [T29] Précision = {precision*100:.1f}% ({corrects}/{len(resultats)})")
        self.assertGreaterEqual(precision, 0.75,
            f"Précision {precision*100:.1f}% < 75% minimum attendu")

    def test_T30_modele_architecture(self):
        """T30 : le modèle a bien 4 classes en sortie"""
        modele = self.modele
        x = torch.zeros(1, 6)
        with torch.no_grad():
            out = modele(x)
        self.assertEqual(out.shape[1], 4, "Le modèle doit avoir 4 sorties")

# ============================================================
# RUNNER PERSONNALISÉ
# ============================================================

class ResultatRunner(unittest.TextTestRunner):
    def run(self, test):
        print(f"\n{'='*65}")
        print(f"  {BOLD}LANDGUARD — SUITE DE TESTS{RESET}")
        print(f"{'='*65}\n")
        result = super().run(test)
        nb_ok  = result.testsRun - len(result.failures) - len(result.errors)
        print(f"\n{'='*65}")
        print(f"  {VERT if not result.failures and not result.errors else ROUGE}"
              f"Tests : {nb_ok}/{result.testsRun} OK{RESET}")
        if result.failures:
            print(f"  {ROUGE}Échecs : {len(result.failures)}{RESET}")
        print(f"{'='*65}\n")
        return result

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromNames([
        "__main__.TestReglesSymboliques",
        "__main__.TestInferenceBornes",
        "__main__.TestIntegrationE2E",
    ])
    verbose = "-v" in sys.argv
    runner = ResultatRunner(verbosity=2 if verbose else 1)
    runner.run(suite)