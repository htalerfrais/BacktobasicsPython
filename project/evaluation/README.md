# Evaluation — Setup du dataset ECSSD

## Structure attendue

```
project/evaluation/
├── run_experiment.py
├── README.md              ← ce fichier
└── test_images/
    └── ECSSD/
        ├── images/                 ← 1000 fichiers .jpg
        └── ground_truth_mask/      ← 1000 fichiers .png (même nom que les images)
```

## Télécharger ECSSD

1. Va sur : https://www.cse.cuhk.edu.hk/leojia/projects/hsaliency/dataset.html
2. Télécharge les deux archives :
   - **"Images"** → contient les 1000 JPEGs
   - **"Ground Truth"** → contient les 1000 masques PNG binaires
3. Extrais chaque archive dans les dossiers correspondants ci-dessus

Les noms de fichiers images et masques sont identiques (ex: `0001.jpg` ↔ `0001.png`).

## Lancer l'évaluation

Depuis la racine du repo :

```powershell
poetry run python project/evaluation/run_experiment.py
```

Puis ouvrir l'UI MLflow pour visualiser les résultats :

```powershell
poetry run mlflow ui
```

Aller sur : http://localhost:5000

## Notes

- Le dossier `test_images/` est gitignored (trop lourd pour être versionné)
- Les résultats MLflow sont stockés dans `mlruns/` (aussi gitignored)
- Pour comparer un nouveau modèle : modifier `MODEL_NAME` et `processor` dans `run_experiment.py`, relancer
