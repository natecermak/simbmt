import logging
from typing import List

import numpy as np


logger = logging.getLogger(__name__)


class Passenger:
    def __init__(self, id: int, source: np.ndarray, destination: np.ndarray, start_time: int):
        self.id = id
        self.source = source  # 2-element numpy array (x, y) where spawned
        self.on_bus = False
        self.loc = source.copy()
        self.destination = destination
        self.start_time = start_time
        self.end_time = np.nan
        self.vel = np.zeros(2)  # walking velocity
