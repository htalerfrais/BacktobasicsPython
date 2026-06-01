# BacktobasicsPython

API de suppression de fond d’image (FastAPI, Celery, MinIO, PyTorch). Détails : [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md).

## Démarrage (Docker)

```bash
docker compose up --build
```

## Interfaces (localhost, une fois la stack lancée)


| Interface                     | URL                                                                                                                      |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| API (FastAPI)                 | [http://localhost:5000](http://localhost:5000)                                                                           |
| Swagger (OpenAPI)             | [http://localhost:5000/docs](http://localhost:5000/docs)                                                                 |
| Métriques API (Prometheus)    | [http://localhost:5000/metrics](http://localhost:5000/metrics)                                                           |
| Métriques worker (Prometheus) | [http://localhost:8000/metrics](http://localhost:8000/metrics)                                                           |
| Flower (Celery)               | [http://localhost:5555](http://localhost:5555)                                                                           |
| MinIO (API S3)                | [http://localhost:9000](http://localhost:9000)                                                                           |
| MinIO (console)               | [http://localhost:9001](http://localhost:9001)                                                                           |
| Prometheus                    | [http://localhost:9090](http://localhost:9090) (cibles : [http://localhost:9090/targets](http://localhost:9090/targets)) |
| Grafana                       | [http://localhost:3000](http://localhost:3000)                                                                           |


## Locust (hors conteneur)

```bash
poetry run locust -f project/tests/load/locustfile.py --host http://localhost:5000
```

UI Locust : [http://localhost:8089](http://localhost:8089)

## Demo rapide (Kubernetes / Minikube)

1. Lancer toute la stack K8s :
   ```powershell
   .\k8s\start-stack.ps1
   ```
   Le script ouvre des **tunnels** (`minikube service --url`) vers api/docs, Flower, Grafana et la console MinIO — **garder ces terminaux ouverts**.

2. **Accès UI (Windows, driver Docker)** : préférer les URLs `http://127.0.0.1:xxxxx` affichées par les tunnels. Les NodePorts (`http://<minikube-ip>:30500`, etc.) ne sont en général **pas** joignables depuis le navigateur hôte.

3. Vérifier l'autoscaling :
   ```powershell
   minikube kubectl -- get hpa -n backtobasics -w
   ```

4. Générer de la charge (Locust en local, host = URL tunnel API **sans** `/docs`) :
   ```powershell
   poetry run locust -f project/tests/load/locustfile.py --host http://127.0.0.1:<port_tunnel_api>
   ```
   Images de test : `project/tests/load/assets/coco_samples/` (gitignored — à télécharger localement).

5. Pendant le test, observer dans Grafana (dashboard **Backtobasics — Métriques**, 9 panels) :
   - App : latence HTTP, durée Celery p99, inférence ML, confiance masque
   - K8s : pods par phase, HPA worker, top CPU/mémoire, charge cluster

Détails K8s : [k8s/README.md](k8s/README.md).

## Dev local sans Docker

Voir [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) (Python 3.12, Poetry, `PYTHONPATH=project`).