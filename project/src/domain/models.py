from dataclasses import dataclass
from pathlib import Path 
from typing import Optional


@dataclass(frozen=True)
class ProcessedImage:
    # Sortie d'un ImageProcessor : octets encodés et extension (sans point)
    data: bytes
    file_extension: str


@dataclass(frozen=True)
class ImageMetadata:
    filename: str
    file_extension: str
    size_bytes: int
    path : str
    file_id : Optional[int] = None

    def __post_init__(self) -> None :
        suffix = Path(self.filename).suffix.lower() # onstruit un objet de la classe Path, qui contient donc un suffix
        if suffix not in [".jpg", ".jpeg", ".png", ".pdf", ".webp"] :
            raise ValueError(f"format non supporté : {suffix}")
    
    
if __name__ == "__main__":
    image = ImageMetadata(filename="strange.jpg", file_extension="jpg", size_bytes=34)
    print(image)
    

