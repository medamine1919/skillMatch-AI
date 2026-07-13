# Évaluation du moteur de scoring — SkillMatch AI

Jeu de test annoté : **17 paires (CV, offre)**. Seuil de présélection : **55/100**.

## Méthodologie

Chaque paire est annotée manuellement (vérité terrain) selon deux axes : *pertinence* du candidat pour l'offre et *appartenance hors-domaine*. Le moteur `compute_scoring` est exécuté sur des données structurées (`cv_data`/`req_data`), ce qui isole le modèle de scoring et rend l'évaluation reproductible.

## Résultats détaillés par cas

| Cas | Score | Décision | Retenu | Hors-domaine | Famille détectée |
|---|---|---|---|---|---|
| P1-dev_web | 62.6 | Moderate Fit | oui | non | Coach Développement Web |
| P2-ia_data | 51.2 | Weak Fit | non | non | Coach IA / Data |
| P3-robotique | 74.7 | Strong Fit | oui | non | Coach Robotique |
| P4-rh | 71.4 | Strong Fit | oui | non | Recruteur / RH |
| P5-finance | 71.9 | Strong Fit | oui | non | Financier / Comptable |
| P6-marketing | 69.2 | Moderate Fit | oui | non | Marketing / Community |
| P7-reception | 80.9 | Strong Fit | oui | non | Réceptionniste / Accueil |
| P8-ingenieur | 80.1 | Strong Fit | oui | non | Ingénieur / Développeur |
| O1-devweb_vs_finance | 2.7 | Weak Fit | non | oui | Financier / Comptable |
| O2-finance_vs_devweb | 3.1 | Weak Fit | non | oui | Coach Développement Web |
| O3-avocat_vs_ingenieur | 3.0 | Weak Fit | non | oui | Ingénieur / Développeur |
| O4-mecanicien_vs_ia | 3.2 | Weak Fit | non | oui | Coach IA / Data |
| O5-agriculteur_vs_marketing | 6.3 | Weak Fit | non | oui | Marketing / Community |
| O6-medecin_vs_devweb | 3.3 | Weak Fit | non | oui | Coach Développement Web |
| B1-ia_vs_devweb | 13.4 | Weak Fit | non | non | Coach Développement Web |
| B2-junior_vs_senior | 52.8 | Weak Fit | non | non | Ingénieur / Développeur |
| B3-hybride_recruteur_it | 31.9 | Weak Fit | non | non | Recruteur / RH + Ingénieur / Développeur |

## Métriques

**Présélection (pertinent vs non)**

| Métrique | Valeur |
|---|---|
| Exactitude | 76.5% |
| Précision | 100.0% |
| Rappel | 63.6% |
| F1-score | 77.8% |

Matrice de confusion : VP=7, FP=0, FN=4, VN=6


**Détection hors-domaine**

| Métrique | Valeur |
|---|---|
| Exactitude | 100.0% |
| Précision | 100.0% |
| Rappel | 100.0% |
| F1-score | 100.0% |

Matrice de confusion : VP=6, FP=0, FN=0, VN=11

## Séparation des scores

- Score moyen des profils **pertinents** : **60.0/100**
- Score moyen des profils **non pertinents** : **3.6/100**

> Un écart net entre ces deux moyennes démontre le pouvoir discriminant du modèle.
