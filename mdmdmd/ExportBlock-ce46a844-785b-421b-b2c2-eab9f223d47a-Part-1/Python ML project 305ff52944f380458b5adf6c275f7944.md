# Python ML project

The aim of this project is not entreprenarial, it is to improve technical skills asked by CTO and tech interviewers in order to grasp the full stack of an AI application and to bridge the gap between my AI / ML / DL / CV / DATA knowledge and my lack of software engineering competencies. This project will be led in parallel of deep self techning about advanced python internals, Object Oriented Programming, Git concepts, and architecture / patterns design. 
In this project the goal is to write the code implementing the notions learned about those subjects, without the help of AI.
The goal of this project is totally different from a project like “Obra” where I use AI as much as possible with agentic AI practices.

Here is the schedule . (2h per day)

# Roadmap

# **Semaine 1 — Fondations Python + structure projet**

- **Concepts** : list, tuple, dict, set, comprehension, generators, classes, dataclasses, dunder methods, Python idioms
- **Projet** : initialiser repo, structure FastAPI + services + ML + tests, endpoint upload image, stockage local
- **Code à lire** : `fastapi/routing.py`, `pydantic/main.py`
- **Micro-feature post 2h** : endpoint upload image fonctionnel

---

# **Semaine 2 — OOP avancé & design patterns**

- **Concepts** : factory, strategy, singleton, observer, architecture hexagonale, dependency injection, Git merge/rebase/stash/hooks
- **Projet** : service `ImageProcessingService`, decorator logging / timing, endpoint remove background simple
- **Code à lire** : `fastapi/dependencies/utils.py`
- **Micro-feature post 2h** : logging / decorator appliqué à pipeline ML

---

# **Semaine 3 — ML pipeline / Computer Vision**

- **Concepts** : PyTorch tensors, dataloaders, preprocessing, batch inference, GPU / CPU, postprocessing
- **Projet** : pipeline ML → load image → preprocess → U²-Net → postprocess → save
- **Code à lire** : `torch/nn/modules/module.py`, `rembg/bg.py`
- **Micro-feature post 2h** : pipeline ML testable pour images

---

# **Semaine 4 — Async / Celery / Tâches longues**

- **Concepts** : asyncio, event loop, Celery + Redis / RabbitMQ, retries, gestion erreurs
- **Projet** : transformer endpoint en tâche asynchrone, suivi statut tâche (pending / done)
- **Code à lire** : `celery/app/task.py`
- **Micro-feature post 2h** : API async avec Celery + suivi des tâches

---

# **Semaine 5 — Video / Batch processing**

- **Concepts** : OpenCV, ffmpeg, batch processing, stockage optimisé
- **Projet** : upload vidéo → extraction frames → pipeline ML → reconstruction vidéo → stockage S3 / minIO
- **Code à lire** : `opencv/videoio.py`
- **Micro-feature post 2h** : endpoint traitement vidéo + stockage

---

# **Semaine 6 — MLOps / Versionning / Tests**

- **Concepts** : MLflow / W&B pour versionning modèle, Pytest unit / pipeline tests, linting Black / Ruff
- **Projet** : intégrer MLflow, écrire tests unitaires pipeline ML, config linting
- **Code à lire** : `mlflow/tracking/fluent.py`, `pytest/runner.py`
- **Micro-feature post 2h** : pipeline versionnée + tests automatisés

---

# **Semaine 7 — Containerisation / CI**

- **Concepts** : Docker, docker-compose, CI/CD (GitHub Actions), container GPU, reproducibility
- **Projet** : Dockerfile API + Celery + Redis, docker-compose dev, CI/CD pipeline build + tests
- **Code à lire** : `docker/cli/command.py`
- **Micro-feature post 2h** : projet containerisé + tests / build automatique

---

# **Semaine 8 — Frontend / UX / Monétisation**

- **Concepts** : React upload / affichage / suivi tâche, UX freemium, Stripe intégration quotas / crédits
- **Projet** : frontend React, endpoints API async, affichage résultats + progression, Stripe quotas
- **Code à lire** : `react/packages/react-dom/src/client/ReactDOM.js`
- **Micro-feature post 2h** : MVP complet image / vidéo → résultat + frontend + quotas

[Concepts Learned](Concepts%20Learned%20321ff52944f380d9bf2fe6c9244c718d.csv)

 

[Project Features](Project%20Features%20321ff52944f3802987d2c5c2ff0b3947.csv)

[Daily Logs](Daily%20Logs%20321ff52944f380c3b44ef32786e0b9d2.csv)