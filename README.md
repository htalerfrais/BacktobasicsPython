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

## Demo rapide (Kubernetes / Minikube)

1. Lancer toute la stack K8s:
   ```powershell
   .\k8s\start-stack.ps1
   ```
2. Ouvrir les UIs:
   - API: `http://<minikube-ip>:30500`
   - Flower: `http://<minikube-ip>:30555`
   - Prometheus: `http://<minikube-ip>:30900`
   - Grafana: `http://<minikube-ip>:30300`
3. Vérifier l'autoscaling:
   ```bash
   kubectl -n backtobasics get hpa -w
   ```
4. Générer de la charge (Locust en local):
   ```bash
   poetry run locust -f project/tests/load/locustfile.py --host http://<minikube-ip>:30500
   ```
5. Pendant le test, observer dans Grafana:
   - API/Celery/ML (latence, débit, erreurs)
   - K8s (pods/deployments, HPA current vs desired, CPU/mémoire)

## Dev local sans Docker

Voir [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) (Python 3.12, Poetry, `PYTHONPATH=project`).
