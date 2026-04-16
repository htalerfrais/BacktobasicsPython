# BacktobasicsPython — Contexte Projet (Agent AI)

> Ce fichier est la source de vérité pour l'agent Cursor. Il décrit l'état du projet, les conventions, l'architecture et la roadmap révisée.

---

## Vue d'ensemble

Projet de **background removal as a service** : l'utilisateur uploade une image, un worker Celery exécute un pipeline PyTorch (DeepLabV3), et retourne l'image sans fond (RGBA PNG).

**Objectif dual :** apprendre des concepts backend/ML/infra tout en construisant un MVP fonctionnel et présentable.

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| API | FastAPI + Uvicorn |
| ML | PyTorch (DeepLabV3 ResNet50, CPU) |
| Async | Celery + Redis |
| Monitoring | Flower (Celery UI), Prometheus (à venir) |
| Containerisation | Docker + Docker Compose |
| Orchestration | Kubernetes (à venir) |
| Object Storage | Local → MinIO (à venir) |
| Qualité code | Ruff (à configurer), Pytest |
| Expériences ML | MLflow (à venir) |
| Frontend | React (à venir) |
| Load testing | Locust |

---

## Architecture

Pattern **hexagonale** (ports & adapters) :

```
project/src/
├── main.py                          # Entrypoint FastAPI
├── app/
│   └── services/
│       ├── file_service.py          # Gestion fichiers (lecture/écriture)
│       └── image_service.py         # Orchestration du pipeline
├── domain/
│   ├── interfaces.py                # ABCs : ImageProcessor, etc.
│   └── models.py                    # Dataclasses : ImageMetadata, ProcessedImage
├── infrastructure/
│   ├── api/
│   │   ├── endpoints.py             # Routes FastAPI (/images/upload, /images/process)
│   │   └── schemas.py               # Pydantic schemas (request/response)
│   ├── celery/
│   │   ├── celery_app.py            # Config Celery (broker/backend Redis)
│   │   └── tasks.py                 # Tâche process_image_task
│   ├── logging_config.py            # Logger app_logger → stdout + app.log
│   └── processors.py                # PyTorchBackgroundRemover (implémente ImageProcessor)
└── utils/
    └── decorators.py                # @time_logger (decorator de timing/logging)
```

---

## Services Docker Compose

| Service | Rôle | Port |
|---------|------|------|
| `redis` | Broker + backend Celery | 6379 |
| `api` | FastAPI app | 5000 |
| `worker` | Celery worker (exécute le ML) | — |
| `flower` | Dashboard Celery | 5555 |

Commandes clés :
```bash
docker-compose up --build          # Lancer tout
locust -f project/tests/load/locustfile.py --host=http://localhost:5000  # Load test
```

---

## Flux principal

```
POST /images/process
  → Sauvegarde fichier temporaire
  → process_image_task.delay(path, filename)  [Celery]
  → Retourne { task_id, status: "PENDING" }

GET /images/process/{task_id}
  → AsyncResult(task_id)
  → Si SUCCESS : retourne { filename, path, ... }
  → Si PENDING/FAILURE : retourne status
```

Le worker charge les modèles ML au démarrage (lazy via `autodiscover_tasks`).

---

## État actuel (début Semaine 5)

### Implémenté ✅
- Architecture hexagonale complète
- Pipeline ML PyTorch background removal (DeepLabV3)
- API FastAPI : upload + process async + poll status
- Celery + Redis intégrés, tâche `process_image_task`
- Docker Compose multi-services (api, worker, redis, flower)
- Dockerfile fonctionnel (Poetry, PYTHONPATH configuré)
- Decorators `@time_logger`, logging vers fichier + stdout
- Locust load testing (`POST /images/process`)
- Tests basiques (`test_api.py` : upload OK)

### À corriger / dette technique ⚠️
- `test_image_process_mocked` est **cassé** : attend une réponse synchrone `{filename, path}` alors que l'API retourne `{task_id, status}` depuis la migration Celery
- `test_model.py` n'est **pas** un vrai test pytest : c'est un script standalone qui duplique la logique de `processors.py`
- `main.py` ne configure pas le logging Uvicorn/FastAPI globalement
- Pas de config Ruff dans `pyproject.toml`

---

## Roadmap révisée (Semaines 5 → 8)

### Semaine 5 — Qualité logicielle & MLOps

**Concepts :** Ruff (linting/formatting), MLflow (tracking), CI/CD basics

**À implémenter :**
1. **Ruff** : configurer `[tool.ruff]` dans `pyproject.toml` (line-length, select, ignore), intégrer dans le workflow
2. **MLflow** : logger chaque inférence dans `tasks.py` — métriques : temps de traitement, version du modèle, dimensions image
3. **CI/CD** : GitHub Actions — pipeline qui lance Ruff + Pytest à chaque push

**Micro-feature :** Un push déclenche automatiquement lint + tests, et chaque inférence est tracée dans MLflow

**Pas dans la semaine 5 :**
- ~~Mocking Redis/S3 dans les tests~~ (complexité vs. valeur jugée faible)

---

### Semaine 6 — Object Storage

**Concepts :** Protocole S3, MinIO (S3 local), boto3

**À implémenter :**
1. **MinIO** : ajouter un service `minio` dans `docker-compose.yml`
2. Remplacer `FileService` (stockage local `uploads/`) par un client MinIO/boto3
3. `process_image_task` upload le résultat dans un bucket MinIO au lieu de l'écrire sur disque
4. L'endpoint `GET /images/process/{task_id}` retourne une URL du fichier dans MinIO

**Micro-feature :** Les images traitées sont stockées et accessibles depuis un bucket MinIO local

**Pas dans la semaine 6 :**
- ~~Presigned URLs~~ (peut être ajouté facilement si besoin)
- ~~Batch processing / Celery Canvas~~ (hors scope)

---

### Semaine 7 — Scaling & Infrastructure

**Concepts :** Kubernetes (Pods, Deployments, Services), Prometheus (métriques)

**À implémenter :**
1. **Prometheus** : exposer des métriques custom FastAPI (latence, nb requêtes, taux d'erreur) via `prometheus-fastapi-instrumentator` ou endpoint `/metrics`
2. **Kubernetes** : écrire les manifests YAML (Deployment + Service pour `api`, `worker`, `redis`)
3. Tester un déploiement local avec `minikube` ou `kind`

**Micro-feature :** L'application tourne dans Kubernetes, avec métriques Prometheus accessibles

**Pas dans la semaine 7 :**
- ~~GPU pass-through~~ (pas de GPU local)
- ~~Flower approfondissement~~ (déjà fonctionnel)

---

### Semaine 8 — Frontend React

**Concepts :** React fundamentals, appels API REST depuis le frontend, polling de statut

**À implémenter :**
1. Interface React simple : formulaire upload image, bouton process
2. Polling du statut via `GET /images/process/{task_id}` (toutes les 2s jusqu'à SUCCESS)
3. Affichage de l'image résultante (depuis MinIO ou URL directe)
4. UI propre (Tailwind ou équivalent)

**Micro-feature :** MVP complet — Upload → Traitement async → Polling → Affichage du résultat

**Pas dans la semaine 8 :**
- ~~WebSockets~~ (polling suffisant pour un MVP, WebSocket = complexité non justifiée ici)
- ~~Stripe / crédits~~ (hors scope)

---

## Conventions du projet

- **Langage :** Python 3.12, FastAPI async, Pydantic v2
- **Gestionnaire de paquets :** Poetry (`pyproject.toml`)
- **Tests :** Pytest, dans `project/tests/`
- **Style :** Ruff (à configurer), pas de commentaires évidents dans le code
- **PYTHONPATH :** `/app/project` (défini dans Dockerfile et Docker Compose)
- **Variables d'env :** `.env` (non commité) — contient `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`

---

## Variables d'environnement clés

```env
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

## Fichiers clés à connaître

| Fichier | Rôle |
|---------|------|
| `project/src/main.py` | Entrypoint FastAPI |
| `project/src/infrastructure/api/endpoints.py` | Routes HTTP |
| `project/src/infrastructure/celery/tasks.py` | Tâche ML Celery |
| `project/src/infrastructure/processors.py` | Pipeline PyTorch |
| `project/src/app/services/file_service.py` | Gestion fichiers (à remplacer par MinIO) |
| `docker-compose.yml` | Définition des services |
| `Dockerfile` | Build de l'image |
| `pyproject.toml` | Dépendances + config outils |
| `project/tests/test_api.py` | Tests API (partiellement cassés) |
