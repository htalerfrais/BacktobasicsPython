# BacktobasicsPython — Contexte Projet (Agent AI)

> Source de vérité complète. Version condensée dans `.cursor/rules/project-context.mdc` (auto-injectée).

---

## Vue d'ensemble

**Background removal as a service** : l'utilisateur uploade une image, un worker Celery exécute un pipeline PyTorch (DeepLabV3 ResNet50), et retourne l'image sans fond (RGBA PNG).

**Objectif dual :** apprendre des concepts backend/ML/infra tout en construisant un MVP fonctionnel et présentable.

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| API | FastAPI + Uvicorn |
| ML | PyTorch (DeepLabV3 ResNet50, CPU) |
| Async | Celery + Redis |
| Monitoring | Flower (dashboard Celery) |
| Containerisation | Docker + Docker Compose |
| Object Storage | MinIO (S3-compatible) via `S3Storage` (boto3) |
| Qualité code | Ruff (E+F defaults), Pytest |
| Model evaluation | MLflow (dev only, hors prod) |
| Load testing | Locust |
| CI | GitHub Actions |

---

## Architecture hexagonale (ports & adapters)

```
project/src/
├── main.py                            # Entrypoint FastAPI
├── app/services/
│   ├── file_service.py                # Façade storage (délègue à StoragePort)
│   └── image_service.py               # Orchestration pipeline ML
├── domain/
│   ├── interfaces.py                  # ABCs : ImageProcessor, StoragePort
│   └── models.py                      # Dataclasses : ImageMetadata (object_key), ProcessedImage
├── infrastructure/
│   ├── api/
│   │   ├── endpoints.py               # POST /images/upload, POST+GET /images/process
│   │   └── schemas.py                 # Pydantic : ImageUploadResponse, TaskResponse, TaskStatusResponse
│   ├── celery/
│   │   ├── celery_app.py              # Config Celery (broker/backend Redis)
│   │   └── tasks.py                   # process_image_task — lit/écrit via S3Storage
│   ├── logging_config.py              # app_logger → stdout + app.log
│   ├── processors.py                  # DummyProcessor, PyTorchBackgroundRemover (Singleton)
│   └── storage.py                     # S3Storage (implémente StoragePort via boto3/MinIO)
└── utils/
    └── decorators.py                  # @time_logger
```

---

## Flux API principal

```
POST /images/process
  → FileService.save(data, key="inputs/<filename>") → S3Storage → MinIO
  → process_image_task.delay(object_key, filename) [Celery]
  → retourne { task_id, status: "PENDING" }

Worker (process_image_task) :
  → FileService.get(input_key) ← S3Storage ← MinIO
  → pipeline ML (DeepLabV3)
  → FileService.save(result, key="outputs/proc_<stem>.png") → MinIO

GET /images/process/{task_id}
  → AsyncResult(task_id)
  → PENDING : { task_id, status, result: null }
  → SUCCESS : { task_id, status, result: { object_key, filename, ... } }
  → FAILURE : HTTP 500
```

Le worker charge PyTorchBackgroundRemover **une seule fois** au démarrage (Singleton + lazy via `autodiscover_tasks`).

---

## Services Docker Compose

| Service | Rôle | Port |
|---------|------|------|
| `redis` | Broker + backend Celery | 6379 |
| `minio` | Stockage objet (API S3-compatible) | 9000 (API), 9001 (console web) |
| `minio-init` | Crée le bucket `MINIO_BUCKET` au démarrage | — |
| `api` | FastAPI app | 5000 |
| `worker` | Celery worker (ML) | — |
| `flower` | Dashboard Celery | 5555 |

Volume : `minio_data` pour les données MinIO (stockage objet). Le bind mount `uploads/` a été supprimé — api et worker n'écrivent plus sur disque.

Variables d’environnement : voir `.env.example` (copier vers `.env`). Inclut Celery + MinIO (`MINIO_ROOT_*`, `MINIO_BUCKET`, `MINIO_ENDPOINT` pour le code boto3 à venir).

---

## Gestion des dépendances (Poetry)

- Venv : `.venv/` à la racine — toujours `poetry add`, jamais `pip install`
- Ajouter dep : `poetry add <pkg>` / dep dev : `poetry add --group dev <pkg>`
- `torch`/`torchvision` via source custom CPU (`pytorch-src` dans `pyproject.toml`)
- Groups : `dev` contient `pytest`, `ruff`, `mlflow`
- Tests en local : `.venv\Scripts\python.exe -m pytest project/tests/ -v`
- PYTHONPATH : `project/` en local (via Poetry), `/app/project` en Docker

---

## CI (GitHub Actions)

Fichier : `.github/workflows/ci.yml`
- Déclenché sur push/PR vers `main`
- Steps : checkout → Python 3.12 → Poetry → cache venv → `poetry install --with dev` → Ruff → Pytest
- `PYTHONPATH: project` injecté pour les tests
- Premier run lent (~10 min, torch à télécharger) — subsequent runs rapides via cache `poetry.lock`

---

## Evaluation ML (MLflow)

Scope : **développement uniquement** — pas dans la prod, pas dans les workers Celery.

Fichier : `project/evaluation/run_experiment.py`
- Un run MLflow = évaluation complète d'un modèle sur ECSSD (1000 images, ground truth masks)
- Logs : `model_name`, `device`, `n_images` (params) + `mean_iou`, `std_iou`, `min/max_iou`, `avg_inference_time_s` (metrics) + output images (artifacts)
- Tracking URI : `project/evaluation/mlruns/` (gitignored)
- Dataset : `project/evaluation/test_images/ECSSD/` (gitignored)
- `MAX_IMAGES` en haut du script pour limiter le nombre d'images testées
- Lancer : `poetry run python project/evaluation/run_experiment.py`
- UI : `poetry run mlflow ui` → http://localhost:5000

---

## État actuel — fin Semaine 6 ✅

### Implémenté
- Architecture hexagonale complète
- Pipeline ML PyTorch background removal (DeepLabV3)
- API FastAPI : upload + process async + poll status
- Celery + Redis, tâche `process_image_task`
- Docker Compose 6 services : redis, minio, minio-init, api, worker, flower
- Dockerfile fonctionnel (Poetry, PYTHONPATH)
- `@time_logger`, logging stdout + fichier
- Locust load testing
- Tests unitaires (`test_api.py`) : 4 tests mockés avec `dependency_overrides`
- Ruff installé (comportement par défaut E+F)
- MLflow evaluation pipeline sur ECSSD
- GitHub Actions CI (Ruff + Pytest sur chaque push)
- `StoragePort` ABC dans le domain, `S3Storage` dans l'infrastructure
- `FileService` refactorisé comme façade sur `StoragePort`
- `ImageMetadata.path` → `object_key`
- Bind mount `uploads/` supprimé — tout passe par MinIO

### Dette technique
- `test_model.py` : script standalone non-pytest, à supprimer ou réécrire
- `main.py` ne configure pas le logging Uvicorn/FastAPI globalement
- Pas de tests d'intégration MinIO (à faire avec `testcontainers` ou manuellement)

---

## Roadmap restante

### Semaine 7 — Scaling & Infrastructure
1. Prometheus : endpoint `/metrics` FastAPI via `prometheus-fastapi-instrumentator`
2. Kubernetes : manifests YAML (Deployment + Service pour api, worker, redis)
3. Déploiement local minikube ou kind

**Pas dans S7 :** GPU pass-through, Flower approfondissement

### Semaine 8 — Frontend React
1. Interface React : upload, bouton process
2. Polling statut `GET /images/process/{task_id}` (toutes les 2s)
3. Affichage résultat depuis MinIO
4. UI propre (Tailwind)

**Pas dans S8 :** WebSockets, Stripe

---

## Conventions

- Python 3.12, Pydantic v2, FastAPI async
- Pas de commentaires évidents dans le code
- Tests dans `project/tests/`
- `.env` non commité : `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- Gitignored : `uploads/`, `data/`, `.venv/`, `mlruns/`, `project/evaluation/test_images/`, `mlflow.db`
