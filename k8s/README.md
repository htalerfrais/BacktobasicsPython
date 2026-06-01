# Kubernetes (Minikube)

Ce dossier contient les manifests Kubernetes du projet `backtobasics`.

## Arborescence

- Un dossier par composant (`redis/`, `minio/`, `api/`, `worker/`, `flower/`, `prometheus/`, `grafana/`, `kube-state-metrics/`).
- Fichiers séparés (`deployment`, `service`, `pvc`, `job`, `hpa`) pour faciliter la revue et les `kubectl apply -f <dossier>/`.
- Préfixes `01-`, `02-`, `03-`... pour expliciter l'ordre d'application.
- `start-stack.ps1` : automatisation Minikube + build + apply + tunnels UI.

---

## Prérequis (session Minikube fraîche)

```bash
minikube start --cpus=4 --memory=7168
kubectl get nodes

# requis pour HPA
minikube addons enable metrics-server
kubectl top nodes
```

Construire l'image dans le daemon Docker de Minikube (sinon `imagePullPolicy: Never` ne trouve pas l'image) :

```powershell
minikube -p minikube docker-env --shell powershell | Invoke-Expression
docker build -t backtobasics:latest .
```

Script PowerShell (automatisation du démarrage + déploiement complet) :

```powershell
.\k8s\start-stack.ps1
```

Le script :
- démarre Minikube seulement s'il n'est pas déjà `Running` (défaut : 4 CPU / 7168 Mo — params `-MinikubeCpus`, `-MinikubeMemoryMb`)
- active `metrics-server` et attend `minikube kubectl -- top nodes`
- build `backtobasics:latest` dans le daemon Docker de Minikube
- applique les manifests dans l'ordre ci-dessous
- attend les rollouts principaux
- ouvre des tunnels UI (api/docs, flower, grafana, minio console) via `minikube service --url`

---

## Ordre de déploiement (complet)

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmaps/

# Secret MinIO : source de vérité = k8s/secrets/minio.yaml (gitignoré). Éditer puis ré-appliquer pour mettre à jour.
kubectl apply -f k8s/secrets/minio.yaml

kubectl apply -f k8s/redis/
kubectl apply -f k8s/minio/
kubectl apply -f k8s/api/
kubectl apply -f k8s/worker/
kubectl apply -f k8s/kube-state-metrics/
kubectl apply -f k8s/flower/
kubectl apply -f k8s/prometheus/
kubectl apply -f k8s/grafana/
```

Attendre les déploiements principaux :

```bash
kubectl -n backtobasics rollout status deployment/api
kubectl -n backtobasics rollout status deployment/worker
kubectl -n backtobasics rollout status deployment/kube-state-metrics
kubectl -n backtobasics rollout status deployment/prometheus
kubectl -n backtobasics rollout status deployment/grafana
```

---

## HPA worker

Le HPA est défini dans `k8s/worker/03-hpa.yaml` :

- cible : `Deployment/worker`
- CPU target : `60%`
- bornes : `minReplicas: 1`, `maxReplicas: 5`
- `behavior` : scale-down ralenti pour éviter l'effet yoyo en démo

Vérification HPA :

```bash
kubectl -n backtobasics get hpa
kubectl -n backtobasics get hpa -w
kubectl -n backtobasics get pods -l app.kubernetes.io/name=worker -w
```

---

## Vérifications utiles

```bash
kubectl -n backtobasics get pod,svc,pvc,hpa
kubectl -n backtobasics logs job/minio-init
kubectl -n backtobasics get events --sort-by=.metadata.creationTimestamp
kubectl -n backtobasics get hpa
```

Vérifier les cibles Prometheus :

```powershell
minikube service prometheus -n backtobasics --url -p minikube
# Prometheus > Status > Targets — attendu UP :
# - fastapi
# - celery-worker
# - kube-state-metrics
# - kubernetes-nodes
# - kubernetes-cadvisor
```

Vérifier le dashboard Grafana :

```powershell
minikube service grafana -n backtobasics --url -p minikube
# Dashboard "Backtobasics — Métriques" (9 panels) :
# - HTTP latence, Celery p99, ML inférence + confiance
# - K8s : pods par phase, HPA worker, top CPU/mémoire, charge cluster %
```

**cAdvisor (Minikube K8s ≥1.38)** : le label `container` est souvent vide ; les panels K8s CPU/mémoire filtrent sur `pod!=""`. Si le panel cluster % est vide, vérifier que la requête utilise `scalar(sum(...))` au dénominateur (cf. `monitoring/grafana/dashboards/backtobasics.json`).

Tester les métriques worker :

```bash
kubectl -n backtobasics port-forward svc/worker 8000:8000
# puis dans un autre terminal
curl http://localhost:8000/metrics
```

---

## Accès UI

**Recommandé (Windows, driver Docker)** — tunnels vers localhost :

```powershell
minikube service api -n backtobasics --url -p minikube        # ajouter /docs pour Swagger
minikube service flower -n backtobasics --url -p minikube
minikube service prometheus -n backtobasics --url -p minikube
minikube service grafana -n backtobasics --url -p minikube
# MinIO console : 2e URL du tunnel (port 9001), login = k8s/secrets/minio.yaml
minikube service minio -n backtobasics --url -p minikube
```

Grafana : auth anonyme activée (Viewer) — pas de login en démo.

**NodePorts (référence)** — souvent **non** joignables depuis le navigateur hôte sous Docker :

| Service | NodePort |
|---------|----------|
| api | 30500 |
| flower | 30555 |
| prometheus | 30900 |
| grafana | 30300 |

`minikube ip` + NodePort peut fonctionner avec d'autres drivers (ex. hyperkit, linux natif).