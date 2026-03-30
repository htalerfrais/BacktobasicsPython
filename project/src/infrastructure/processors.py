from src.domain.interfaces import ImageProcessor, ProcessedImage
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
    def __init__(self, device : str = "cpu"):
        self.device = torch.device(device)
        weights = DeepLabV3_ResNet50_Weights.DEFAULT
        self.model = deeplabv3_resnet50(weights=weights) 
        # problématique pour l'instant car ca fait que le model sera chargé à chaque appel de l'API !! 
        self.model.eval()
        self.model.to(self.device)
        # récupérer la normalisation associée aux 
        # données d'entrainement ayant données ces poids
        self.preprocess = weights.transforms()
    
    def _preprocess(self, image_bytes : bytes) -> Tuple[torch.Tensor, Image] :
        # bytes to tensors
        # normalisation and resize ... with transforms of pytorch
        # il peut y avoir des problèmes ici si mon image d'entrée est en PNG, car PNG est en RGBA avec transparence
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB") # ouvrir l'image en tant qu'objet PIL Image
        tensor = self.preprocess(image) # on applique le préprocessor récupéré des poids entraînés.
        tensor = tensor.unsqueeze(0) # ajouter channel de batch [batchs , C, H, W] => [1 , C, H, W] pour entrée model
        return tensor.to(self.device), image
    
    def _inference(self, tensor : torch.Tensor) -> torch.Tensor:
        # tensors to tensors
        with torch.no_grad():
            output = self.model(tensor)["out"]  # dimensions (21 classes) [1, 21, H, W]
        return output
    
    def _postprocess(self, tensor, original_image):
        # tensors to bytes
        orig_size = (original_image.height, original_image.width)
        # redimensionner logits en sortie de model pour fit avec taille originale de l'image
        resized_logits = F.interpolate(tensor, size=orig_size, mode='bilinear', align_corners=False)
        # argmax sur la dimensiond des classes, retirer channel de batch.
        predictions = torch.argmax(resized_logits, dim=1).squeeze(0)
        mask = (predictions != 0).cpu().numpy()   # on garde que piexels sur lesquels argmax n'est pas 0 : qui ne sont pas classés en background
        image_np = np.array(original_image)
        
        # construction de l'image RGBA (du alpha) pour avoir de la transparence au niveau du background
        alpha = mask.astype(np.uint8) * 255
        # dstack pour ajouter le canal alpha 
        rgba = np.dstack((image_np, alpha))
        result = Image.fromarray(rgba.astype(np.uint8), mode="RGBA")
        
        # on veut retourner des bytes, pas un objet PIL Image python
        buffer = io.BytesIO() # création d'un fichier dans la RAM 
        result.save(buffer, format="PNG")  # comme with open("image.png", "wb") mais dans le fichier buffer hors du disque
        return buffer.getvalue()
      
    def process(self, image_bytes : bytes) -> ProcessedImage:
        preprocessed, original_image = self._preprocess(image_bytes)
        inferenced = self._inference(preprocessed)
        postprocessed = self._postprocess(inferenced, original_image)
        output = ProcessedImage(data=postprocessed, file_extension='png')
        return output