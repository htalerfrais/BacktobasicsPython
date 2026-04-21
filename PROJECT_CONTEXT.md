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
| Object Storage | Local → MinIO (semaine 6) |
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
│   ├── file_service.py                # Persistance fichiers (à remplacer par MinIO)
│   └── image_service.py               # Orchestration pipeline
├── domain/
│   ├── interfaces.py                  # ABCs : ImageProcessor
│   └── models.py                      # Dataclasses : ImageMetadata, ProcessedImage
├── infrastructure/
│   ├── api/
│   │   ├── endpoints.py               # POST /images/upload, POST+GET /images/process
│   │   └── schemas.py                 # Pydantic : ImageUploadResponse, TaskResponse, TaskStatusResponse
│   ├── celery/
│   │   ├── celery_app.py              # Config Celery (broker/backend Redis)
│   │   └── tasks.py                   # process_image_task — charge ML dans le worker uniquement
│   ├── logging_config.py              # app_logger → stdout + app.log
│   └── processors.py                  # DummyProcessor, PyTorchBackgroundRemover (Singleton)
└── utils/
    └── decorators.py                  # @time_logger
```

---

## Flux API principal

```
POST /images/process
  → FileService.save_file() : sauvegarde dans uploads/images/
  → process_image_task.delay(path, filename) [Celery]
  → retourne { task_id, status: "PENDING" }

GET /images/process/{task_id}
  → AsyncResult(task_id)
  → PENDING : { task_id, status, result: null }
  → SUCCESS : { task_id, status, result: ImageUploadResponse }
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

Volumes : `./uploads` → `/app/uploads` (api + worker) ; `minio_data` pour les données MinIO.

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

## État actuel — fin Semaine 5 ✅

### Implémenté
- Architecture hexagonale complète
- Pipeline ML PyTorch background removal (DeepLabV3)
- API FastAPI : upload + process async + poll status
- Celery + Redis, tâche `process_image_task`
- Docker Compose multi-services (api, worker, redis, flower)
- Dockerfile fonctionnel (Poetry, PYTHONPATH)
- `@time_logger`, logging stdout + fichier
- Locust load testing
- Tests unitaires réécrits (`test_api.py`) : 4 tests mockés couvrant upload, enqueue, poll PENDING, poll SUCCESS
- Ruff installé (comportement par défaut E+F)
- MLflow evaluation pipeline sur ECSSD
- GitHub Actions CI (Ruff + Pytest sur chaque push)

### Dette technique
- `test_model.py` : script standalone non-pytest, à supprimer ou réécrire
- `main.py` ne configure pas le logging Uvicorn/FastAPI globalement
- `FileService` encore basé sur le filesystem local (sera remplacé en S6)

---

## Roadmap restante

### Semaine 6 — Object Storage
1. Ajouter service `minio` dans `docker-compose.yml`
2. Remplacer `FileService` par client MinIO/boto3
3. `process_image_task` upload résultat dans bucket MinIO
4. `GET /images/process/{task_id}` retourne URL MinIO

**Pas dans S6 :** presigned URLs, batch processing

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
