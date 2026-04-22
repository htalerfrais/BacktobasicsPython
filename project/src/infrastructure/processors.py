import time

from src.domain.interfaces import ImageProcessor, ProcessedImage
from src.infrastructure.metrics import ML_INFERENCE_DURATION, ML_MASK_CONFIDENCE
from src.utils.decorators import time_logger

from typing import List, Tuple
from torchvision.models.segmentation import deeplabv3_resnet50, DeepLabV3_ResNet50_Weights 
import torch 
from PIL import Image
import numpy as np
import io
import torch.nn.functional as F


class DummyProcessor(ImageProcessor):
    @time_logger
    def process(self, image_bytes : bytes) -> ProcessedImage : 
        print("using dummy processor pretending to process")
        processed_image = ProcessedImage(
            data = image_bytes,
            file_extension = 'png'
        )
        return processed_image
    
        
class WhiteProcessor(ImageProcessor):
    @time_logger
    def process(self, image_bytes : bytes) -> ProcessedImage:
        print("using whiteprocessor")
        processed_image = ProcessedImage(
            data = image_bytes,
            file_extension = 'png'
        )
        return processed_image


class CompositeProcessor(ImageProcessor):
    """
    Cette classe ne peut pas être utilisée comme un orchestrateur de 
    preprocessor, inferenceEngine, puis postProcessor car chaque processor 
    qui compose la pipeline qu'elle met en place doit lui meme etre un 
    ImageProcessor. Or, un inferenceEngine n'a pas des bytes en entrées sorties.
    """
    
    def __init__(self, processors : List[ImageProcessor]):
        self._processors = processors
        
    @time_logger
    def process(self, image_bytes : bytes) -> ProcessedImage:
        output = ProcessedImage(data=image_bytes, file_extension='none')
        for processor in self._processors:
            output = processor.process(output.data)
        return output
    

class PyTorchBackgroundRemover(ImageProcessor):
    _instance = None  # variable de classe : instance unique (singleton)
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            #l'instance n'existe pas on peut la créer
            # super(PyTorchBackgroundRemover, cls) différent de PyTorchBackgroundRemover.
            # super(PyTorchBackgroundRemover) est un genre de classe mère qui sait comment fabriquer l'objet en mémoire. 
            cls._instance = super(PyTorchBackgroundRemover, cls).__new__(cls)
            cls._instance._model_loaded = False # savoir si on doit charger le model dans le init, ici oui car l'instance est toute nouvelle.
            
        return cls._instance # soit l'instance préexistante soit la nouvelle
    
    def __init__(self, device : str = "cpu"):
        # checker si le modèle a déjà été chargé sur l'instance unique grace au flag
        if not self._model_loaded:
            self.device = torch.device(device)
            weights = DeepLabV3_ResNet50_Weights.DEFAULT
            self.model = deeplabv3_resnet50(weights=weights) 
            self.model.eval()
            self.model.to(self.device)
            self.preprocess = weights.transforms()
            self._model_loaded = True
    
    def _preprocess(self, image_bytes : bytes) -> Tuple[torch.Tensor, Image] :
        # bytes to tensors
        # normalisation and resize ... with transforms of pytorch
        # il peut y avoir des problèmes ici si mon image d'entrée est en PNG, car PNG est en RGBA avec transparence
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB") # ouvrir l'image en tant qu'objet PIL Image
        tensor = self.preprocess(image) # on applique le préprocessor récupéré des poids entraînés.
        tensor = tensor.unsqueeze(0) # ajouter channel de batch [batchs , C, H, W] => [1 , C, H, W] pour entrée model
        return tensor.to(self.device), image
    
    def _inference(self, tensor : torch.Tensor) -> torch.Tensor:
        start = time.perf_counter()
        try:
            with torch.no_grad():
                return self.model(tensor)["out"]  # dimensions (21 classes) [1, 21, H, W]
        finally:
            # toujours enregistrer la durée (succès ou exception) pour Prometheus
            ML_INFERENCE_DURATION.observe(time.perf_counter() - start)

    def _postprocess(self, tensor, original_image) -> Tuple[bytes, float | None]:
        # tensors (logits) -> bytes PNG RGBA + score de confiance optionnel pour les métriques
        orig_size = (original_image.height, original_image.width)
        with torch.no_grad():
            # redimensionner logits en sortie de model pour fit avec taille originale de l'image
            resized_logits = F.interpolate(
                tensor, size=orig_size, mode="bilinear", align_corners=False
            )
            # proba de la classe prédite par pixel (max du softmax sur les 21 classes)
            probs = torch.softmax(resized_logits, dim=1)
            max_per_pixel = probs.max(dim=1).values.squeeze(0)
            # argmax sur la dimension des classes, retirer channel de batch
            predictions = torch.argmax(resized_logits, dim=1).squeeze(0)
        # pixels "sujet" : pas la classe 0 (background COCO)
        foreground = predictions != 0
        if foreground.any():
            # moyenne de la proba du gagnant sur le masque — une valeur / image pour ml_mask_confidence
            mean_conf = max_per_pixel[foreground].float().mean().item()
        else:
            # toute l'image classée en fond : pas d'observation histogramme (évite biais)
            mean_conf = None
        mask = foreground.cpu().numpy()  # même masque binaire qu'avant pour l'alpha
        image_np = np.array(original_image)

        # construction de l'image RGBA (canal alpha) pour la transparence du background
        alpha = mask.astype(np.uint8) * 255
        rgba = np.dstack((image_np, alpha))
        result = Image.fromarray(rgba.astype(np.uint8), mode="RGBA")

        buffer = io.BytesIO()
        result.save(buffer, format="PNG")
        return buffer.getvalue(), mean_conf

    @time_logger
    def process(self, image_bytes : bytes) -> ProcessedImage:
        preprocessed, original_image = self._preprocess(image_bytes)
        inferenced = self._inference(preprocessed)
        postprocessed, mask_conf = self._postprocess(inferenced, original_image)
        if mask_conf is not None:
            ML_MASK_CONFIDENCE.observe(mask_conf)  # worker uniquement (Celery)
        output = ProcessedImage(data=postprocessed, file_extension='png')
        return output