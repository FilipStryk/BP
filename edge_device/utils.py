import cv2

from typing import Tuple

def draw_crosshair(img, x: int, y: int, color: Tuple[int, int, int] = (0, 0, 255), width: int = 1) -> None:
    cv2.line(img, (x - 10, y), (x + 10, y), color, width)
    cv2.line(img, (x, y - 10), (x, y + 10), color, width)
    cv2.circle(img, (x, y), 8, color, width)