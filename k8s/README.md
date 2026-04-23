# Kubernetes (Minikube)

## Pourquoi cette arborescence ?

- **Un dossier par composant** (`redis/`, `minio/`, `api/`, …) : on retrouve vite ce qui appartient à quoi, comme en prod.
- **Fichiers séparés** (deployment, service, PVC, job) : revue de PR et `kubectl apply -f k8s/minio/` possibles.
- **Préfixes `01-`, `02-`…** dans `minio/` (et `redis/`) : l’ordre d’application est clair (ex. PVC avant Deployment). Sans ça, `kubectl` trie par nom et risquerait d’appliquer le Deployment avant le PVC.
- `api/`, `worker/`, `prometheus/`, `grafana/` : prêts pour les étapes suivantes (fichiers YAML à venir, dossiers maintenus via `.gitkeep`).

Avant, des fichiers plats `04-redis.yaml` avaient le même contenu : pratique pour itérer vite, moins pour grandir le socle.

---

## Ordre d’application (recommandé)

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/
kubectl apply -f k8s/redis/
kubectl apply -f k8s/minio/01-pvc.yaml
kubectl apply -f k8s/minio/02-deployment.yaml
kubectl apply -f k8s/minio/03-service.yaml
kubectl wait -n backtobasics deployment/minio --for=condition=Available --timeout=120s
kubectl apply -f k8s/minio/04-job-init.yaml
```

Ou en une ligne pour redis + minio (hors job), si déjà up to date :

```bash
kubectl apply -f k8s/redis/
kubectl apply -f k8s/minio/01-pvc.yaml -f k8s/minio/02-deployment.yaml -f k8s/minio/03-service.yaml
```

Vérifications :

```bash
kubectl -n backtobasics get pod,svc,pvc
kubectl -n backtobasics logs job/minio-init
```

---

## Changer le secret MinIO (sans commit)

```bash
kubectl -n backtobasics delete secret backtobasics-minio
kubectl -n backtobasics create secret generic backtobasics-minio \
  --from-literal=MINIO_ROOT_USER=tonuser \
  --from-literal=MINIO_ROOT_PASSWORD=tonpass
```

Les services s’appellent `redis` et `minio` (aligné avec le ConfigMap `backtobasics-config`).

---

---

## Étape 5 : API + Worker

**Prérequis :** étapes 3 + 4 appliquées. Image `backtobasics:latest` construite dans Minikube (étape 2).

```bash
kubectl apply -f k8s/api/
kubectl apply -f k8s/worker/
kubectl -n backtobasics rollout status deployment/api
kubectl -n backtobasics rollout status deployment/worker
```

Accéder à l'API depuis la machine hôte :

```bash
minikube service api -n backtobasics
```

Minikube ouvre l'URL dans le navigateur ou affiche l'URL (`http://<minikube-ip>:30500`).

Vérifier les métriques du worker (depuis l'intérieur du cluster) :

```bash
kubectl -n backtobasics port-forward svc/worker 8000:8000
# puis dans un autre terminal :
curl http://localhost:8000/metrics
```

---

## Étape suivante

Deployments `prometheus/` et `grafana/` (monitoring dans le cluster).
