import io
import torch
import numpy as np
from PIL import Image
from typing import Tuple
import torch.nn.functional as F
from abc import ABC, abstractmethod
from torchvision.models.segmentation import deeplabv3_resnet50, DeepLabV3_ResNet50_Weights

class ImageProcessor(ABC):
    @abstractmethod
    def process(self, image_bytes: bytes) -> bytes:
        pass

class PyTorchBackgroundRemover(ImageProcessor):
    def __init__(self, device: str = "cpu"):
        self.device = torch.device(device)
        print(f"--- Loading model on {self.device} ---")
        
        weights = DeepLabV3_ResNet50_Weights.DEFAULT
        # Correction de l'appel : on passe les weights au constructeur
        self.model = deeplabv3_resnet50(weights=weights)
        self.model.eval()
        self.model.to(self.device)
        
        self.preprocess = weights.transforms()
        print("--- Model Loaded ---")
    
    def _preprocess(self, image_bytes: bytes) -> Tuple[torch.Tensor, Image.Image]:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = self.preprocess(image)
        tensor = tensor.unsqueeze(0) # Correction de l'assignation
        return tensor.to(self.device), image
    
    def _inference(self, tensor: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            output = self.model(tensor)["out"]
        return output
    
    def _postprocess(self, tensor: torch.Tensor, original_image: Image.Image) -> bytes:
        orig_size = (original_image.height, original_image.width)
        
        # Upsampling des logits vers la taille originale
        resized_logits = F.interpolate(tensor, size=orig_size, mode='bilinear', align_corners=False)
        
        # Argmax pour trouver les classes (1, 21, H, W) -> (H, W)
        predictions = torch.argmax(resized_logits, dim=1).squeeze(0)
        
        # Création du masque (classe 0 = background dans COCO)
        mask = (predictions != 0).byte().cpu().numpy()
        
        # Conversion image originale en Numpy
        image_np = np.array(original_image)
        
        # Création du canal Alpha (0 ou 255)
        alpha = (mask * 255).astype(np.uint8)
        
        # Stack RGBA
        rgba = np.dstack((image_np, alpha))
        result = Image.fromarray(rgba, mode="RGBA")
        
        # Export en bytes
        buffer = io.BytesIO()
        result.save(buffer, format="PNG")
        return buffer.getvalue()

    def process(self, image_bytes: bytes) -> bytes:
        preprocessed, original_image = self._preprocess(image_bytes)
        inferenced = self._inference(preprocessed)
        postprocessed = self._postprocess(inferenced, original_image)
        return postprocessed


if __name__ == "__main__":
    input_path = "data/dillion-tkc007.webp" 
    output_path = "data/resultat_sans_fond.png"
    print("beggining")
    try:
        # Lecture de l'image
        print(f"Lecture du fichier : {input_path}")
        with open(input_path, "rb") as f:
            image_data = f.read()

        # Initialisation du processeur
        remover = PyTorchBackgroundRemover(device="cpu") # Ou "cuda" si tu as un GPU

        # Traitement
        print("Démarrage du traitement...")
        result_bytes = remover.process(image_data)

        # Sauvegarde
        with open(output_path, "wb") as f:
            f.write(result_bytes)
        
        print("--- SUCCESS ---")
        print(f"Image sauvegardée sous : {output_path}")

    except FileNotFoundError:
        print(f"Erreur : Le fichier {input_path} est introuvable.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")