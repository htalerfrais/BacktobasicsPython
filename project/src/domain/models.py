from dataclasses import dataclass
from pathlib import Path 

@dataclass(frozen=True)
class ImageMetadata:
    filename: str
    content_type: str
    size_bytes: int
    
    def __post_init__(self) -> None :
        suffix = Path(self.filename).suffix.lower() # onstruit un objet de la classe Path, qui contient donc un suffix
        if suffix not in [".jpg", ".jpeg", ".png", ".pdf"] :
            raise ValueError(f"format non supporté : {suffix}")
    
    
if __name__ == "__main__":
    image = ImageMetadata(filename="strange.jpg", content_type="image", size_bytes=34)
    print(image)