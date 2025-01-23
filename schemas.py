from pydantic import BaseModel
from typing import Tuple, List, Union


class BBox(BaseModel):
    box_class: str
    conf: float
    left_top: Tuple[int, int]
    right_bottom: Tuple[int, int]


class ImagePredict(BaseModel):
    filename: str
    bboxes: List[BBox]
    link_to_processed_image: Union[str, None] = None
