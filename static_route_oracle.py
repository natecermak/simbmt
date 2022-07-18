import logging
from typing import Dict

import numpy as np

import trigonometry as trig

logger = logging.getLogger(__name__)


class StaticRouteOracle:

    def __init__(self, params: Dict):
        self.params = params  # keep track of simulation parameters
        self.routes = []

    def add_grid_routes(self, nx: int, ny: int) -> None:
        for i in range(nx):
            if nx == 1:
                self.routes.append(np.array([[0, 0.5], [1, 0.5]]))
            else:
                self.routes.append(np.array([[0, i / (nx - 1)], [1, i / (nx - 1)]]))
        for i in range(ny):
            if ny == 1:
                self.routes.append(np.array([[0.5, 0], [0.5, 1]]))
            else:
                self.routes.append(np.array([[i / (ny - 1), 0], [i / (ny - 1), 1]]))

    def add_spoke_routes(self, ns: int) -> None:
        # TODO: define this
        pass

    def add_hub_and_spoke_routes(self, nh: int, ns: int) -> None:
        # TODO: define this
        pass

    def add_single_square_route(self, inset: float) -> None:
        self.routes.append(
            np.array(
                [
                    [inset, inset], 
                    [1 - inset, inset], 
                    [1 - inset, 1 - inset], 
                    [inset, 1 - inset]
                ]
            )
        )

    def initialize_busses(self, state, num_routes: int) -> None:
        # evenly distribute busses between routes
        for i, bus in enumerate(state.busses):
            frac = i * num_routes / len(state.busses)
            bus.route = int(frac)
            route = self.routes[bus.route]

            # add `tci` (target coordinate index - the index of the route coordinates that is the current bus destination)
            phase = frac - bus.route
            nv = self.routes[bus.route].shape[0]  # number of vertices
            bus.tci = int(phase * nv)
            if bus.tci == nv:
                bus.tci = 0
                bus.loc = (route[-1] + route[0]) / 2
            else:
                bus.loc = (route[bus.tci] + route[bus.tci - 1]) / 2

    def route(self, state) -> None:
        for bus in state.busses:
            route = self.routes[bus.route]
            if np.all(bus.loc == route[bus.tci]):
                bus.tci = (bus.tci + 1) % len(route)

            dir = route[bus.tci] - bus.loc
            bus.vel = dir / np.linalg.norm(dir) * self.params["bus_speed"]

            # handle the last step to a target (don't overshoot)
            if np.linalg.norm(dir) < self.params["bus_speed"]:
                bus.vel = dir

        for passenger in state.passengers:
            if passenger.on_bus:
                continue  # irrelevant they're already on bus.

            # Do we come up with the plan as soon as they pop into existence and then save it?
            # Or do we continually re-derive it?
            # For now, do the former

            if not hasattr(passenger, "plan"):
                self.derive_plan(passenger, state)
            # TODO:
            # passenger.vel = derive_vel_from_plan(passenger)
            # FOR TESTING ONLY:
            passenger.vel = np.array([0.001, 0.001])

    def pickup_and_dropoff(self, state, time) -> None:
        for p in state.passengers:
            # if (p's plan is to board BUS `bus`) and
            #    (p is near last line segment travelled for bus):
            #       bus.pickup(p)
            #       update p's plan to reflect that they're gotten picked up

            # if p.on_bus and the bus
            pass

    def derive_plan(self, passenger, state):
        # 1. check the walking time. that's a cheap upper bound.
        walking_time = (
            np.linalg.norm(passenger.destination - passenger.loc) / self.params["passenger_speed"]
        )

        # check which buses it is even possible to get on
        for bus in state.busses:
            logger.debug(f"Bus {bus.id} on route {bus.route}")
            
            timetable = self.get_bus_timetable(bus, 1)
            accessible_timetable = []
            found_accessible_segment = False
            for row in timetable:
                if not found_accessible_segment:
                    accessible_segment = trig.get_accessible_region(
                        p=passenger.loc,
                        b1=row[1:3],
                        b2=row[3:5],
                        t1=row[0],
                        vp=self.params["passenger_speed"],
                        vb=self.params["bus_speed"],
                    )
                    if accessible_segment is None:
                        logger.debug(f"  Unreachable: {row}")
                    else:
                        found_accessible_segment = True
                        # TODO: get_accessible_region should probably return this entire row
                        #       (that is, this calculation shouldn't be here)
                        t0 = row[0] + np.linalg.norm(accessible_segment[0] - row[1:3]) / self.params["bus_speed"]
                        new_row = [t0, *accessible_segment[0], *row[3:5]]
                        accessible_timetable.append(new_row)

                        logger.debug(f"  Can reach:   {row}")
                        logger.debug(f"  Reachable:   {new_row}")
                        logger.debug(f"  => All subsequent segments are reachable")
                else:
                    accessible_timetable.append(row)

            dropoff_time = trig.find_best_dropoff_point(
                x=passenger.destination,
                timetable=accessible_timetable,
                vp=self.params["passenger_speed"],
                vb=self.params["bus_speed"],
            )
            logger.debug(f"best dropoff time for this bus: {dropoff_time:.1f}")

        # plan should consist of a sequence of time windows
        #   from time t0 to t1, walk from loc1 to loc2
        #   t1 - t2: wait for bus (don't move)
        #   t2 - t3: ride bus X
        #   t3 - t4: get off and walk from loc3 to loc4
        # TODO: WHAT IS THE DATA STRUCTURE?
        # Actions: walk, wait, get on, get off

        # passenger.plan = [
        #     ['walk', start_time, end_time, start_loc, end_loc]
        #     ['wait', start_time, end_time, start_loc, end_loc]
        #     ['ride', start_time, end_time, start_loc, end_loc]
        #     ['walk', start_time, end_time, start_loc, end_loc]
        # ]
        # passenger.plan_counter = 0
        passenger.plan = True # TODO: this is a placeholder so `plan` exists

    def get_bus_timetable(self, bus, t_max):
        """ get a n x 5 table (t, x0, y0, x1, y1) from NOW (t=0) till t=t=max """
        table = np.empty((10, 5))
        route = self.routes[bus.route]

        table[0, 0] = 0
        table[0, 1:3] = bus.loc
        table[0, 3:5] = route[bus.tci]

        for i in range(1, 10):
            # time at which the bus starts this line segment
            table[i, 0] = (
                table[i - 1, 0]
                + np.linalg.norm(table[i - 1, 3:5] - table[i - 1, 1:3]) / self.params["bus_speed"]
            )

            # start and end coordinates of this segment
            table[i, 1:3] = route[(bus.tci + i - 1) % len(route)]
            table[i, 3:5] = route[(bus.tci + i) % len(route)]

        # logger.debug(f"Bus {bus.id} on route {bus.route} has upcoming timetable:")
        # logger.debug(table)

        return table
