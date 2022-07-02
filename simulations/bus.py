import logging
from typing import List

import numpy as np

from passenger import Passenger


logger = logging.getLogger(__name__)


class Bus:
    def __init__(self, id: int, route: int, loc: np.ndarray, passengers: List[Passenger]) -> None:
        self.id = id  # bus id number
        self.route = route  # route number
        self.loc = loc  # current bus location (2-element numpy array)
        self.passengers = passengers  # list of Passenger objects
        self.vel = np.zeros(2)  # current velocity

    def pickup(self, passenger: Passenger) -> None:
        if not passenger.on_bus:
            # TODO: verify passenger is physically present?
            self.passengers.append(passenger)  # add newest passenger to end of list
            passenger.on_bus = True
            logger.debug(f"Passenger {passenger.id}, Bus {self.id}, pickup at {self.loc}")
        else:
            raise ValueError("Passenger is too far to pick up or is already on bus!!")

    def dropoff(self, passenger: Passenger, time: int) -> None:
        self.passengers.remove(passenger)
        passenger.loc = (
            self.loc
        )  # TODO: is this right? should this be handled by the simulation manager?
        passenger.on_bus = False
        logger.debug(f"Passenger {passenger.id}, Bus {self.id}, dropoff at {self.loc}")
