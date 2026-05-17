# Kubernetes (Minikube)

Ce dossier contient les manifests Kubernetes du projet `backtobasics`.

## Arborescence

- Un dossier par composant (`redis/`, `minio/`, `api/`, `worker/`, `flower/`, `prometheus/`, `grafana/`).
- Fichiers séparés (`deployment`, `service`, `pvc`, `job`, `hpa`) pour faciliter la revue et les `kubectl apply -f <dossier>/`.
- Préfixes `01-`, `02-`, `03-`... pour expliciter l'ordre d'application.

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
- démarre Minikube seulement s'il n'est pas déjà `Running`
- active `metrics-server`
- build `backtobasics:latest` dans le daemon Docker de Minikube
- applique les manifests dans l'ordre ci-dessous
- attend les rollouts principaux

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

Vérifier les cibles Prometheus:

```bash
minikube service prometheus -n backtobasics
# puis dans Prometheus > Status > Targets:
# - fastapi UP
# - celery-worker UP
# - kube-state-metrics UP
# - kubernetes-nodes UP
# - kubernetes-cadvisor UP
```

Vérifier les panels Grafana:

```bash
minikube service grafana -n backtobasics
# dashboard "Backtobasics — Métriques":
# section K8s non vide (pods, deployments, endpoints, HPA, CPU/mémoire)
```

Tester les métriques worker :

```bash
kubectl -n backtobasics port-forward svc/worker 8000:8000
# puis dans un autre terminal
curl http://localhost:8000/metrics
```

---

## Accès UI (NodePort)

- API : `http://<minikube-ip>:30500` (ou `minikube service api -n backtobasics`)
- Flower : `http://<minikube-ip>:30555`
- Prometheus : `http://<minikube-ip>:30900`
- Grafana : `http://<minikube-ip>:30300`

Astuce : Minikube peut ouvrir l'URL automatiquement :

```bash
minikube service api -n backtobasics
minikube service flower -n backtobasics
minikube service prometheus -n backtobasics
minikube service grafana -n backtobasics
```