# BacktobasicsPython — Contexte Projet (Agent AI)

> Source de vérité complète. Version condensée dans `.cursor/rules/project-context.mdc` (auto-injectée).
>
> **Agents :** après tout changement notable (architecture, stack, roadmap semaines, conventions, monitoring, K8s), vérifier si `PROJECT_CONTEXT.md` doit être mis à jour ; si oui, le modifier puis **réaligner** `.cursor/rules/project-context.mdc` pour que le résumé injecté reste fidèle.

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
| Monitoring | Prometheus + Grafana (dashboard démo) + Flower (UI Celery) + kube-state-metrics (K8s) |
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

**Scrape Prometheus (Compose et K8s)** — `monitoring/prometheus.yml` (Compose) / `k8s/configmaps/prometheus-config.yaml` (K8s) :

| Job | Cible | Rôle |
|-----|-------|------|
| `fastapi` | `api:5000` | HTTP auto (instrumentator) |
| `celery-worker` | `worker:8000` | Métriques custom Celery + ML |
| `kube-state-metrics` | `kube-state-metrics:8080` | État K8s (pods, HPA, deployments…) — **K8s uniquement** |
| `kubernetes-cadvisor` | proxy API → `/metrics/cadvisor` | CPU/RAM pods (cAdvisor) — **K8s uniquement** |
| `kubernetes-nodes` | proxy API → `/metrics` | Kubelet — scrapé, non affiché Grafana |

**Limitation scrape worker (K8s)** : Prometheus cible le Service `worker:8000` (ClusterIP) → **un pod worker par scrape**, pas agrégation multi-replicas. Les panels K8s cAdvisor/HPA couvrent le scale-out.

**Dashboard Grafana** : `monitoring/grafana/dashboards/backtobasics.json` (+ miroir dans `k8s/grafana/02-configmap-provisioning.yaml`).

Panels **affichés** (9, orientés démo LinkedIn) :

| Panel | Métriques |
|-------|-----------|
| HTTP — latence p50/p90/p99 | `http_request_duration_seconds_bucket` |
| Celery — durée tâche p99 | `celery_task_duration_seconds_bucket` |
| ML — inférence p50/p90/p99 | `ml_inference_duration_seconds_bucket` |
| ML — confiance masque | `ml_mask_confidence_*` |
| K8s — pods par phase | `kube_pod_status_phase` |
| K8s — HPA worker | `kube_horizontalpodautoscaler_status_*` |
| K8s — top CPU / mémoire pods | `container_cpu_usage_seconds_total`, `container_memory_working_set_bytes` |
| K8s — CPU / mémoire cluster % | cAdvisor `id="/kubepods"` ÷ `kube_node_status_allocatable` |

Toujours **scrapées** mais **retirées du dashboard** : débit HTTP (`http_requests_total`), compteur Celery (`celery_tasks_total`), deployments desired/available, endpoints services.

**cAdvisor Minikube (K8s ≥1.38)** : label `container` souvent vide ; filtrer avec `pod!=""` (pas `container!=""`). Panel cluster % : utiliser `scalar(sum(...))` au dénominateur (sinon PromQL retourne vide).

---

## Kubernetes (Minikube — local)

Structure `k8s/` :

```
k8s/
├── namespace.yaml
├── configmaps/
│   ├── app-env.yaml              # Celery, MinIO (sans PROMETHEUS_MULTIPROC_DIR — worker only)
│   └── prometheus-config.yaml   # 5 jobs scrape (cf. tableau ci-dessus)
├── secrets/                      # GITIGNORE
│   └── minio.yaml
├── redis/
├── minio/                        # PVC + Deployment + Service + Job init
├── api/                          # NodePort 30500
├── worker/                       # ClusterIP :8000 metrics, HPA 1→3 @ 60% CPU, PROMETHEUS_MULTIPROC_DIR
├── kube-state-metrics/           # RBAC + Deployment + Service (image officielle k8s)
├── flower/                       # NodePort 30555, enableServiceLinks: false
├── prometheus/                   # RBAC nodes/proxy + SA, NodePort 30900
├── grafana/                      # provisioning ConfigMap, anonymous Viewer, NodePort 30300
└── start-stack.ps1               # Minikube + build + apply + tunnels UI
```

Commandes d'application (ordre) : `k8s/README.md`.
Automatisation : `.\k8s\start-stack.ps1` (params `-MinikubeCpus`, `-MinikubeMemoryMb`).

**Accès UI (Windows, driver Docker)** : les NodePorts (`192.168.49.x:30xxx`) ne sont en général **pas** joignables depuis le navigateur hôte → utiliser **`minikube service <svc> -n backtobasics --url`** (tunnels `127.0.0.1:xxxxx`, terminaux à garder ouverts). Le script ouvre api/docs, flower, grafana, minio console.

NodePorts (référence) :

| Service | NodePort |
|---------|----------|
| api | 30500 |
| flower | 30555 |
| prometheus | 30900 |
| grafana | 30300 |

**HPA worker** (`k8s/worker/03-hpa.yaml`) : `minReplicas: 1`, `maxReplicas: 3`, CPU 60%, scale-down lent (300s stabilization).

**Ressources Minikube** : `--cpus` / `--memory` au `minikube start` (défaut script : 4 CPU / 7168 Mo). Modifier nécessite `minikube delete` puis recréation.

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
- **S7 — Prometheus** : métriques app (HTTP auto + Celery + ML) ; scrape K8s (kube-state-metrics, cAdvisor, kubelet)
- **S7 — Grafana** : dashboard `backtobasics.json` — **9 panels démo** (app + K8s/HPA/ressources)
- **S7 — Kubernetes** : manifests `k8s/` (kube-state-metrics, prometheus RBAC, HPA worker, script `start-stack.ps1`)
- **S7 — Locust** : images COCO dans `project/tests/load/assets/coco_samples/` (gitignored)

### Dette technique
- `test_model.py` : script standalone non-pytest, à supprimer ou réécrire
- `main.py` ne configure pas le logging Uvicorn/FastAPI globalement
- Pas de tests d'intégration MinIO (à faire avec `testcontainers` ou manuellement)
- Scrape worker K8s : un replica à la fois via Service (pas pod SD)
- Worker OOM possible sous Locust + HPA max sur nœud Minikube limité en RAM
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
- `k8s/secrets/` non commité : credentials dans `minio.yaml` local ; voir ordre de déploiement dans `k8s/README.md`
- Gitignored : `data/`, `.venv/`, `mlruns/`, `project/evaluation/test_images/`, `mlflow.db`, `k8s/secrets/`, `project/tests/load/assets/`
