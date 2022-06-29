import logging
from typing import List

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s :: %(levelname)s :: %(message)s")
logger = logging.getLogger(__name__)

n_bus = 10              # number of busses
passenger_rate = 0.15   # per timestep
bus_speed = 0.03        # city length, per timestep
pickup_eps = 1e-4       # pickup radius


class Passenger:
    def __init__(self, id, source, destination, start_time):
        self.id = id
        self.source = source  # 2-element numpy array (x, y) where spawned
        self.on_bus = False
        self.loc = source  # if on_bus==True, this should be ignored
        self.destination = destination
        self.start_time = start_time
        self.end_time = np.nan
        self.vel = np.zeros(2)  # walking velocity


class Bus:
    def __init__(self, id, route, loc, passengers=[]):
        self.id = id
        self.route = route
        self.loc = loc
        self.passengers = passengers  # list of Passenger objects
        self.vel = np.zeros(2)

    def is_near_pickup(self, passenger):
        return np.linalg.norm(passenger.loc - self.loc) < pickup_eps

    def is_near_dropoff(self, passenger):
        return np.linalg.norm(passenger.destination - self.loc) < pickup_eps

    def pickup(self, passenger):
        if self.is_near_pickup(passenger) and not passenger.on_bus:
            self.passengers.append(passenger)  # add newest passenger to end of list
            passenger.on_bus = True
            logger.debug(f"Passenger {passenger.id}, Bus {self.id}, pickup at {self.loc}")
        else:
            raise ValueError("Passenger is too far to pick up or is already on bus!!")

    def dropoff(self, passenger, time):
        self.passengers.remove(passenger)
        passenger.loc = self.loc
        passenger.on_bus = False
        logger.debug(f"Passenger {passenger.id}, Bus {self.id}, dropoff at {self.loc}")


class State:
    def __init__(self, busses: List[Bus], passengers: List[Passenger]):
        self.busses = busses  
        self.passengers = passengers  # active passengers or awaiting pickup
        self.completed = []  # passengers who have reached their destinations and can be ignored

    def plot(self):
        ax = plt.gca()
        ax.set_aspect("equal")

        for bus in self.busses:
            angle = 180 / 3.14 * np.arctan2(bus.vel[1], bus.vel[0]) + 180
            props = {"ha": "center", "va": "center", "bbox": {"fc": "0.8", "pad": 0}}
            text = f"{bus.id}, {bus.route}, {len(bus.passengers)}"
            ax.text(*bus.loc, text, props, rotation=angle)

        for p in self.passengers:
            plt.arrow(*p.source, *(p.destination - p.source), width=0.005)


def spawn_new_passengers(state: State, time: int) -> None:
    if np.random.rand() > passenger_rate:
        return None
    new_id = np.max([p.id for p in [*state.passengers, *state.completed]]) + 1
    source = np.random.rand(2)
    destination = np.random.rand(2)
    passenger = Passenger(id=new_id, source=source, destination=destination, start_time=time)
    logging.debug(f"Passenger {new_id} spawned at time {time} at {source}, going to {destination}")
    state.passengers.append(passenger)


#### Define initial state
state = State(
    busses=[Bus(id=i, route=0, loc=np.random.rand(2), passengers=[]) for i in range(n_bus)],
    passengers=[
        Passenger(id=0, source=np.ones(2) * 0.2, destination=np.ones(2) * 0.2, start_time=0)
    ],
)

####################### Define and instantiate the oracle #####################
class GreedyRoutingOracle:
    def __init__(self, state):
        for bus in state.busses:
            bus.assignment = None

    def route(self, state):
        """ 
        """

        # if there's an unassigned passenger, and any available bus,
        #    assign the passenger to the bus
        assignments = [bus.assignment for bus in state.busses]

        for p in state.passengers:
            if p not in assignments and not p.on_bus:
                # assign it to an empty bus, if available
                for bus in state.busses:
                    if bus.assignment is None:
                        bus.assignment = p
                        logger.debug(f"Passenger {p.id} assigned to bus {bus.id}")
                        break

        # for every bus that has an assignment, go pick them up if they're not already aboard
        for bus in state.busses:
            if bus.assignment is not None:
                if bus.assignment not in bus.passengers:
                    # if we havent picked them up, got to them
                    dir = bus.assignment.loc - bus.loc
                else:
                    # if bus has an assignment as passenger, go to their destination
                    dir = bus.assignment.destination - bus.loc

                bus.vel = dir / np.linalg.norm(dir) * bus_speed

                # handle the last step to a target (don't overshoot)
                if np.linalg.norm(dir) < bus_speed:
                    bus.vel = dir

    def pickup_and_dropoff(self, state, time):
        for bus in state.busses:
            if bus.assignment is not None:
                if bus.is_near_pickup(bus.assignment) and not bus.assignment.on_bus:
                    bus.pickup(bus.assignment)
            for p in bus.passengers:
                if bus.is_near_dropoff(p):
                    bus.dropoff(p, time)
                    bus.vel = np.zeros(2)
                    bus.assignment = None

oracle = GreedyRoutingOracle(state)


############################ Run the actual simulation ########################
for i in range(3500):

    # plot state
    if i % 100 == 0:
        plt.clf()
        state.plot()
        plt.xlim([0, 1])
        plt.ylim([0, 1])
        plt.pause(0.01)
        #plt.savefig(f"{i:03d}.png")

    # update state
    spawn_new_passengers(state, i)

    # let the busses do their thing: 
    oracle.route(state)                  # first determine their velocities
    for bus in state.busses:             # update their positions
        bus.loc += bus.vel
    oracle.pickup_and_dropoff(state, i)  # do pickups and dropoffs

    # update metrics
    completed = []
    for p in state.passengers:
        if np.linalg.norm(p.loc - p.destination) < pickup_eps:
            p.end_time = i
            logging.debug(f"Passenger {p.id} arrived at destination in {p.end_time - p.start_time} timesteps")
            completed.append(p)

    for p in completed:
        state.completed.append(p)
        state.passengers.remove(p)




################# Plot metrics  ################################################
all_passengers = [*state.passengers, *state.completed]
start_times = [p.start_time for p in all_passengers]
transit_times = [p.end_time - p.start_time for p in all_passengers]

plt.figure()
plt.scatter(start_times, transit_times)
plt.xlabel("start time")
plt.ylabel("total trip duration (wait+ride)")
plt.show()

