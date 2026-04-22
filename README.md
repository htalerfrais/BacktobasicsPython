# BacktobasicsPython

API de suppression de fond d’image (FastAPI, Celery, MinIO, PyTorch). Détails : [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md).

## Démarrage (Docker)

```bash
docker compose up --build
```

## Interfaces (localhost, une fois la stack lancée)

| Interface | URL |
|-----------|-----|
| API (FastAPI) | http://localhost:5000 |
| Swagger (OpenAPI) | http://localhost:5000/docs |
| Métriques API (Prometheus) | http://localhost:5000/metrics |
| Métriques worker (Prometheus) | http://localhost:8000/metrics |
| Flower (Celery) | http://localhost:5555 |
| MinIO (API S3) | http://localhost:9000 |
| MinIO (console) | http://localhost:9001 |
| Prometheus | http://localhost:9090 (cibles : http://localhost:9090/targets) |
| Grafana | http://localhost:3000 |

## Locust (hors conteneur)

```bash
poetry run locust -f project/tests/load/locustfile.py --host http://localhost:5000
```

UI Locust : http://localhost:8089

## Dev local sans Docker

Voir [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) (Python 3.12, Poetry, `PYTHONPATH=project`).
