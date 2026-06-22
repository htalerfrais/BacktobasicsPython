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

## Adapter le scale selon le cas d'usage ML

On dimensionne d'abord le **budget global** du cluster (CPU/RAM du nœud Minikube), puis on règle la **taille d'un worker** pour qu'il exécute une tâche ML de façon fiable. Tant que chaque pod reste dans ce cadre, on augmente le **débit** en ajoutant des workers (scale horizontal via HPA). En résumé : **worker plus gros = tâches plus lourdes** ; **plus de workers = plus de parallélisme**, dans la limite de ce que le nœud peut absorber.

### Configuration actuelle

Cas d'usage : **DeepLabV3 CPU**, images type COCO, traitement async Celery.

| Levier | Valeur | Fichier |
|--------|--------|---------|
| Nœud Minikube | 4 CPU / 7168 Mo | `k8s/start-stack.ps1` |
| Worker / pod | `concurrency=1`, request `500m`/`1Gi`, limit `2Gi` | `k8s/worker/01-deployment.yaml` |
| HPA worker | `min=1`, `max=3`, CPU `60%` | `k8s/worker/03-hpa.yaml` |
| API | 1 replica, request `100m`/`256Mi` | `k8s/api/01-deployment.yaml` |

`maxReplicas: 3` sur un nœud ~7 Go : compromis démo (scale visible sans saturer la RAM du cluster).

### Que régler selon le besoin

| Besoin | Action | Type de scale |
|--------|--------|---------------|
| Plus de débit (plus d'images en parallèle) | `maxReplicas` / `minReplicas` (HPA) | Horizontal |
| Tâche ML plus lourde (modèle, résolution, RAM) | `resources` du worker | Vertical (pod) |
| Cluster trop petit (plafond global) | `--cpus` / `--memory` Minikube | Vertical (nœud) |
| HPA réagit trop tard / trop tôt | `averageUtilization` | Réglage HPA |

Sous charge : HPA (`current/desired`), top CPU/mémoire worker, cluster % dans Grafana.
