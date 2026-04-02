from pydantic import BaseModel
from typing import List

class Tree(BaseModel):
    vertice: str
    nombreComun: str
    nombreCientifico: str
    altura: str
    copa: str
    dap: str
    latitud: str
    longitud: str
    images: List[str] = []
