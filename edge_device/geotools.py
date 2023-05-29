from __future__ import annotations
import math
from typing import List, Tuple

import numpy as np
import cv2


class Point:
    def __init__(self, x: int, y: int, lat: float = 0, lon: float = 0) -> None:
        self.x = x
        self.y = y
        self.lat = lat
        self.lon = lon

    def pixelCoorinates(self) -> Tuple[int, int]:
        return (self.x, self.y)

    def gpsCoorinates(self) -> Tuple[float, float]:
        return (self.lat, self.lon)

    def distanceTo(self, point: Point) -> float:
        dlat = math.radians(self.lat) - math.radians(point.lat)
        dlon = math.radians(self.lon) - math.radians(point.lon)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(self.lat) * math.cos(point.lat) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return c * 6371e3
    
    def toList(self) -> List:
        return [self.x, self.y, self.lat, self.lon]


class CoordinatesConverter:
    def __init__(self, ref_points: List[Point]) -> None:
        self.ref_points = ref_points
        self.trans_matrix = cv2.getPerspectiveTransform(
            np.float32([(p.x, p.y) for p in self.ref_points]),  # type: ignore
            np.float32([(p.lat, p.lon) for p in self.ref_points]),  # type: ignore
        )

    def pixelToGps(self, x: int, y: int) -> Tuple[float, float]:
        pixel_coords = np.array([x, y, 1], dtype=np.float32)
        coords = np.dot(self.trans_matrix, pixel_coords)
        gps_coords = coords[:2] / coords[2]

        return (gps_coords[0], gps_coords[1])
