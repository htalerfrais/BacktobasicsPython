import time
from pathlib import Path
import io
import tempfile
import os

import mlflow
import numpy as np
from PIL import Image

from src.infrastructure.processors import PyTorchBackgroundRemover

# --- Configuration ---

EXPERIMENT_NAME = "segmentation-evaluation"
MODEL_NAME = "deeplabv3_resnet50"
DEVICE = "cpu"
MAX_IMAGES = 20  # mettre None pour tourner sur tout le dataset

# Chemin vers les données ECSSD (voir guide dans evaluation/README.md)
IMAGES_DIR = Path("project/evaluation/test_images/ECSSD/images")
MASKS_DIR = Path("project/evaluation/test_images/ECSSD/ground_truth_mask")


# --- Helpers ---

def compute_iou(predicted_mask: np.ndarray, gt_mask: np.ndarray) -> float:
    """
    Calcule l'IoU (Intersection over Union) entre deux masques binaires.
    IoU = |pred ∩ gt| / |pred ∪ gt|
    1 si les masques sont identiques, 0 si masques ne se chevauchent pas.
    """
    pred_bool = predicted_mask > 127
    gt_bool = gt_mask > 127

    intersection = np.logical_and(pred_bool, gt_bool).sum()
    union = np.logical_or(pred_bool, gt_bool).sum()

    if union == 0:
        return 1.0
    return float(intersection / union)


def extract_predicted_mask(rgba_bytes: bytes) -> np.ndarray:
    """Extrait le masque prédit depuis les bytes RGBA retournés par le processor."""
    image = Image.open(io.BytesIO(rgba_bytes)).convert("RGBA")
    return np.array(image)[:, :, 3]  # masque foreground alpha channel


def load_gt_mask(mask_path: Path) -> np.ndarray:
    """Charge le masque ground truth ECSSD en niveaux de gris (binaire)."""
    return np.array(Image.open(mask_path).convert("L"))


# --- Evaluation principale ---

def run_evaluation():
    image_paths = sorted(IMAGES_DIR.glob("*.jpg"))
    if not image_paths:
        raise FileNotFoundError(f"Aucune image trouvée dans {IMAGES_DIR}. Consulte evaluation/README.md.")
    if MAX_IMAGES is not None:
        image_paths = image_paths[:MAX_IMAGES]

    processor = PyTorchBackgroundRemover(device=DEVICE)

    # Stocke tous les runs dans evaluation/mlruns/ plutôt qu'à la racine du repo
    mlflow.set_tracking_uri((Path(__file__).parent / "mlruns").as_uri())
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(run_name=MODEL_NAME):
        mlflow.log_params({
            "model_name": MODEL_NAME,
            "device": DEVICE,
            "n_images": len(image_paths),
            "dataset": "ECSSD",
        })

        ious = []
        inference_times = []

        total = len(image_paths)
        for i, image_path in enumerate(image_paths, start=1):
            print(f"\r[{i}/{total}] {image_path.name}...", end="", flush=True)
            mask_path = MASKS_DIR / image_path.with_suffix(".png").name
            if not mask_path.exists():
                print(f"\r[SKIP] Masque manquant pour {image_path.name}")
                continue

            image_bytes = image_path.read_bytes()
            # process and get
            start = time.perf_counter()
            result = processor.process(image_bytes)
            elapsed = time.perf_counter() - start

            # compute IoU with prediction
            predicted_mask = extract_predicted_mask(result.data)
            gt_mask = load_gt_mask(mask_path)
            iou = compute_iou(predicted_mask, gt_mask)

            ious.append(iou)
            inference_times.append(elapsed)

            # Artifact : image de sortie
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(result.data)
                tmp_path = tmp.name
            mlflow.log_artifact(tmp_path, artifact_path="output_images")
            os.remove(tmp_path)

        # Métriques agrégées sur tout le dataset
        mlflow.log_metrics({
            "mean_iou": float(np.mean(ious)),
            "std_iou": float(np.std(ious)),
            "min_iou": float(np.min(ious)),
            "max_iou": float(np.max(ious)),
            "avg_inference_time_s": float(np.mean(inference_times)),
        })

        print(f"\n=== Résultats {MODEL_NAME} sur ECSSD ({len(ious)} images) ===")
        print(f"  mean IoU  : {np.mean(ious):.4f}")
        print(f"  std  IoU  : {np.std(ious):.4f}")
        print(f"  avg  time : {np.mean(inference_times):.2f}s / image")


if __name__ == "__main__":
    run_evaluation()
