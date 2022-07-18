import logging
from typing import List

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from passenger import Passenger
from bus import Bus
from static_route_oracle import StaticRouteOracle
from naber_oracle import NaberOracle

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s :: %(levelname)s :: %(message)s")
logger = logging.getLogger(__name__)

np.set_printoptions(precision=2)


class State:
    def __init__(self, busses: List[Bus], passengers: List[Passenger]):
        self.busses = busses
        self.passengers = passengers  # active passengers or awaiting pickup
        self.completed = []  # passengers who have reached their destinations and can be ignored

    def plot(self):
        plt.clf()
        ax = plt.gca()
        ax.set_aspect("equal")

        for bus in self.busses:
            angle = 180 / 3.14 * np.arctan2(bus.vel[1], bus.vel[0]) + 180
            props = {"ha": "center", "va": "center", "bbox": {"fc": "0.8", "pad": 0}}
            text = f"{bus.id}, {bus.route}, {len(bus.passengers)}"
            ax.text(*bus.loc, text, props, rotation=angle)

        for p in self.passengers:
            plt.arrow(*p.source, *(p.destination - p.source), width=0.005)
            plt.arrow(*p.source, *(p.loc - p.source), width=0.005)
            plt.arrow(*p.loc, *(p.destination - p.loc), width=0.005)

        plt.xlim([0, 1])
        plt.ylim([0, 1])

    def spawn_new_passengers(self, time: int, passenger_rate: float) -> None:
        if np.random.rand() > passenger_rate:
            return None
        new_id = np.max([p.id for p in [*self.passengers, *self.completed]]) + 1
        source = np.random.rand(2)
        destination = np.random.rand(2)
        passenger = Passenger(id=new_id, source=source, destination=destination, start_time=time)
        logging.debug(
            f"Passenger {new_id} spawned at time {time} at {source}, going to {destination}"
        )
        self.passengers.append(passenger)


# oracle and simulation both need access to this dictionary
simulation_parameters = dict(
    n_bus=3,  # number of busses
    passenger_rate=0.0,  # per timestep
    bus_speed=0.03,  # city length, per timestep
    passenger_speed=0.003,  # city length, per timestep
    pickup_eps=1e-4,  # pickup radius
)

#### Define initial state
test_passenger = Passenger(
    id=0, source=np.array([0.2, 0.2]), destination=np.array([0.8, 0.2]), start_time=0
)
state = State(
    busses=[
        Bus(id=i, route=0, loc=np.random.rand(2), passengers=[])
        for i in range(simulation_parameters["n_bus"])
    ],
    passengers=[test_passenger],
)

####################### Define and instantiate the oracle #####################
# oracle = NaberOracle(simulation_parameters, state)

oracle = StaticRouteOracle(simulation_parameters)
#oracle.add_grid_routes(nx=3, ny=0)
oracle.add_single_square_route(inset=0.1)
oracle.initialize_busses(state, num_routes=len(oracle.routes))

# state.plot()
# plt.show()

############################ Run the actual simulation ########################
for i in range(350):

    # plot state
    if i % 1 == 0:
        state.plot()
        plt.pause(0.01)
        # plt.savefig(f"{i:03d}.png")

    # update state
    state.spawn_new_passengers(i, simulation_parameters["passenger_rate"])

    # let the busses do their thing:
    oracle.route(state)  # first determine their velocities
    for bus in state.busses:  # update their positions
        # TODO: enforce check that bus.vel is a valid velocity (doesnt exceed speed limits)
        bus.loc += bus.vel
        for p in bus.passengers:
            p.loc = bus.loc
    for p in state.passengers:  # update their positions
        if not p.on_bus:
            # TODO: enforce check that passenger velocity is valid
            p.loc += p.vel

    # TODO: oracle should request pickups/dropoffs, simulation should execute
    oracle.pickup_and_dropoff(state, i)  # do pickups and dropoffs

    # removed passengers who arrived (`completed` passengers) and update metrics
    completed = []
    for p in state.passengers:
        if np.linalg.norm(p.loc - p.destination) < simulation_parameters["pickup_eps"] and not p.on_bus:
            p.end_time = i
            logging.debug(f"Passenger {p.id} arrived in {p.end_time - p.start_time} timesteps")
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
