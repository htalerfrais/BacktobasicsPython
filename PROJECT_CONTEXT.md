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
| Monitoring | Prometheus + Grafana + Flower (dashboard Celery) |
| Métriques custom | `prometheus_client` (Histograms dans `infrastructure/metrics.py`) |
| Containerisation | Docker + Docker Compose |
| Orchestration | Kubernetes (Minikube en local) — manifests dans `k8s/` |
| Object Storage | MinIO (S3-compatible) via `S3Storage` (boto3) |
| Qualité code | Ruff (E+F defaults), Pytest |
| Model evaluation | MLflow (dev only, hors prod) |
| Load testing | Locust |
| CI | GitHub Actions |

---

## Architecture hexagonale (ports & adapters)

```
project/src/
├── main.py                            # Entrypoint FastAPI + Prometheus instrumentator
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
│   │   └── tasks.py                   # process_image_task — métriques Celery + start_http_server(8000)
│   ├── logging_config.py              # app_logger → stdout + app.log
│   ├── metrics.py                     # Définitions Prometheus : CELERY_*, ML_INFERENCE_DURATION, ML_MASK_CONFIDENCE
│   ├── processors.py                  # DummyProcessor, PyTorchBackgroundRemover (Singleton + métriques ML)
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
  → pipeline ML (DeepLabV3) → _inference() → ML_INFERENCE_DURATION.observe()
  → _postprocess() → ML_MASK_CONFIDENCE.observe()
  → FileService.save(result, key="outputs/proc_<stem>.png") → MinIO
  → CELERY_TASK_DURATION.observe() + CELERY_TASKS_TOTAL.inc()

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
| `api` | FastAPI app + `/metrics` Prometheus | 5000 |
| `worker` | Celery worker (ML) + metrics HTTP server | 8000 (metrics) |
| `flower` | Dashboard Celery | 5555 |
| `prometheus` | Scrape `/metrics` api:5000 + worker:8000 | 9090 |
| `grafana` | Dashboards (provisionnés depuis `monitoring/`) | 3000 |

Volumes : `minio_data`, `grafana_data`. Config monitoring dans `monitoring/` (gitcommité sauf `k8s/secrets/`).

---

## Métriques Prometheus

Définies dans `project/src/infrastructure/metrics.py` :

| Métrique | Type | Source | Description |
|----------|------|--------|-------------|
| `http_request_duration_seconds` | Histogram | API (auto) | Latence par endpoint (prometheus-fastapi-instrumentator) |
| `http_requests_total` | Counter | API (auto) | Requêtes par method/handler/status |
| `celery_task_duration_seconds` | Histogram | Worker | Durée end-to-end de `process_image_task` |
| `celery_tasks_total` | Counter | Worker | Tâches terminées, label `status` (success/failure) |
| `ml_inference_duration_seconds` | Histogram | Worker | Durée forward pass DeepLabV3 uniquement |
| `ml_mask_confidence` | Histogram | Worker | Confiance softmax moyenne sur pixels foreground |

Dashboard Grafana : `monitoring/grafana/dashboards/backtobasics.json` (provisionné automatiquement).

---

## Kubernetes (Minikube — local)

Structure `k8s/` :

```
k8s/
├── namespace.yaml
├── configmaps/
│   ├── app-env.yaml             # Variables non secrètes (Celery, MinIO endpoint, bucket)
│   └── prometheus-config.yaml  # prometheus.yml (cibles api:5000 + worker:8000)
├── secrets/                     # GITIGNORE — ne jamais commiter
│   └── minio.yaml               # MINIO_ROOT_USER / MINIO_ROOT_PASSWORD (voir secrets/README.md)
├── redis/                       # Deployment + Service ClusterIP
├── minio/                       # PVC + Deployment + Service + Job init bucket
├── api/                         # Deployment (imagePullPolicy: Never) + Service NodePort 30500
├── worker/                      # Deployment (concurrency=1) + Service ClusterIP 8000
├── flower/                      # Deployment + Service NodePort 30555
├── prometheus/                  # Deployment + Service NodePort 30900
└── grafana/                     # PVC + ConfigMap provisioning + Deployment + Service NodePort 30300
```

Commandes d'application (ordre) : voir `k8s/README.md`.

NodePorts exposés depuis Minikube :

| Service | NodePort |
|---------|----------|
| api | 30500 |
| flower | 30555 |
| prometheus | 30900 |
| grafana | 30300 |

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

## État actuel — fin Semaine 7 ✅

### Implémenté
- Architecture hexagonale complète
- Pipeline ML PyTorch background removal (DeepLabV3)
- API FastAPI : upload + process async + poll status
- Celery + Redis, tâche `process_image_task`
- Docker Compose 8 services : redis, minio, minio-init, api, worker, flower, prometheus, grafana
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
- **S7 — Prometheus** : 6 métriques (HTTP auto + Celery + ML inference + ML confidence)
- **S7 — Grafana** : dashboard provisionné automatiquement (`backtobasics.json`)
- **S7 — Kubernetes** : manifests complets dans `k8s/` (namespace, configmaps, secrets, redis, minio, api, worker, flower, prometheus, grafana)

### Dette technique
- `test_model.py` : script standalone non-pytest, à supprimer ou réécrire
- `main.py` ne configure pas le logging Uvicorn/FastAPI globalement
- Pas de tests d'intégration MinIO (à faire avec `testcontainers` ou manuellement)
- K8s non testé en conditions réelles (Minikube local uniquement)

---

## Roadmap restante

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
- `.env` non commité : `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `MINIO_*`
- `k8s/secrets/` non commité : credentials Kubernetes (voir `k8s/secrets/README.md`)
- Gitignored : `data/`, `.venv/`, `mlruns/`, `project/evaluation/test_images/`, `mlflow.db`, `k8s/secrets/`
