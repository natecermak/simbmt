import logging
import numpy as np

logger = logging.getLogger(__name__)


def is_acute_triangle(p1, p2, p3):
    a = np.linalg.norm(np.array(p2) - np.array(p1))
    b = np.linalg.norm(np.array(p3) - np.array(p1))
    c = np.linalg.norm(np.array(p3) - np.array(p2))
    sides = np.sort([a, b, c])

    return sides[2] ** 2 < sides[1] ** 2 + sides[0] ** 2


def get_accessible_region(p, b1, b2, t1: float, vp: float, vb: float):
    """ If a bus will traverse line segment b1->b2 starting at time t1, what
    (if any) subsegment can a passenger starting at point p reach?
    TODO: Finish docstring! This function is important.
    """
    # coerce, ensure they're numpy arrays
    p = np.array(p)
    b1 = np.array(b1)
    b2 = np.array(b2)

    # unit vector from b1 to b2
    beta = (b2 - b1) / np.linalg.norm(b2 - b1)
    # vector from passenger start point to beginning of bus segment
    alpha = b1 - p
    # length of bus segment
    d_max = np.linalg.norm(b2 - b1)

    # quadratic coefficients (ax**2 + bx + c)
    a = (1 / vp ** 2) - (1 / vb ** 2)
    b = 2 * (alpha @ beta / vp ** 2 - t1 / vb)
    c = np.linalg.norm(alpha) ** 2 / vp ** 2 - t1 ** 2

    if a == 0:  # linear or constant time difference
        if b == 0:  # constant time difference
            return [b1, b2] if c < 0 else None
        # linear time difference
        root = -c / b
        d1 = root if b < 0 else 0
        d2 = d_max if b < 0 else root
    else:
        # quadratic time difference
        discriminant = b ** 2 - 4 * a * c
        if discriminant < 0:
            # no roots, therefore there is no accessible region of the segment
            return None

        # at least one root
        roots = (-b + np.array([-1, 1]) * np.sqrt(discriminant)) / (2 * a)
        # find overlap between root interval and [0, b2-b1]
        d1 = np.max([0, roots[0]])
        d2 = np.min([d_max, roots[1]])

    if d2 >= d1:
        return [b1 + d1 * beta, b1 + d2 * beta]
    else:
        return None


def closest_point_to_segment(x, s1, s2):
    x = np.array(x)
    s1 = np.array(s1)
    s2 = np.array(s2)

    # nice algebraic solution:
    # https://math.stackexchange.com/questions/2193720/find-a-point-on-a-line-segment-which-is-the-closest-to-other-point-not-on-the-li
    u = x - s1
    v = s2 - s1
    t = (v @ u) / (v @ v)

    if t >= 0 and t <= 1:
        nearest = (1 - t) * s1 + t * s2
    else:
        d1 = np.linalg.norm(x - s1)
        d2 = np.linalg.norm(x - s2)
        nearest = s1 if d1 < d2 else s2

    return nearest


def find_best_dropoff_on_segment(x, s1, s2, vp, vb):
    """ Given a segment, should you get off at the beginning, somewhere in the middle
    or the end of the route, in order to minimize your total time?
    @param x: coordinates of the destination (2-element numpy vector)
    @param s1: start coordinates of the segment (2-element numpy vector)
    @param s2: end coordinates of the segment (2-element numpy vector)
    @param vp, vb: passenger and bus speed, respectively
    @returns: a dictionary, containing:
        coords: optimal dropoff coordinates
        distance: how far you should go along the segment S
        time: how long you should stay on the bus before getting off
        arrival_time: your actual time arriving at your destination
    """
    x = np.array(x)
    s1 = np.array(s1)
    s2 = np.array(s2)

    alpha = x - s1
    beta = (s2 - s1) / np.linalg.norm(s2 - s1)
    ab = alpha @ beta
    d_max = np.linalg.norm(s2 - s1)

    # here, we solve the quadratic for *times* (not distances) when bus' projected
    # velocity onto vector-to-destination falls below passenger walking speed
    a = vp ** 2 - vb ** 2
    b = 2 * ab * (vb - vp ** 2 / vb)
    c = (vp / vb) ** 2 * (alpha @ alpha) - ab ** 2

    discriminant = b ** 2 - 4 * a * c
    roots = (-b + np.array([-1, 1]) * np.sqrt(discriminant)) / (2 * a)
    distances = np.array([0, *(roots * vb), d_max])
    distances = distances[(distances >= 0) & (distances <= d_max)]

    # arrival_times is a dictionary from (how far you travel on the segment) to (how long it takes to arrive)
    arrival_times = {}
    for d in distances:
        arrival_times[d] = d / vb + np.linalg.norm(x - (s1 + d * beta)) / vp

    distance_along_segment = min(arrival_times, key=arrival_times.get)
    dropoff_coordinates = s1 + beta * distance_along_segment

    return_dict = {
        "coords": dropoff_coordinates,
        "distance": distance_along_segment,
        "time": distance_along_segment / vb,
        "arrival_time": arrival_times[distance_along_segment],
    }
    return return_dict


def find_best_dropoff_point(x, timetable, vp, vb):
    """ Given a timetable, where should you get off to get to x as quickly as possible?
    @param x: 2d numpy array containing coordinates of destination
    @param timetable: (n x 5) list of lists or numpy array
    @param vp: speed of passenger walking
    @param vb: speed of bus
    @returns:
        time of arrival
        time to get off
        segment (row of timetable) to get off at
        coordinates to get off at
    """

    best_arrival_time = None
    best_dropoff = None
    for i, (t0, x1, y1, x2, y2) in enumerate(timetable):
        s1 = np.array([x1, y1])
        s2 = np.array([x2, y2])
        dropoff = find_best_dropoff_on_segment(x, s1, s2, vp, vb)
        dropoff["arrival_time"] += t0
        dropoff["time"] += t0
        if best_arrival_time is None or dropoff["arrival_time"] < best_arrival_time:
            logger.debug(
                f"New optimal dropoff: Segment {i} from {s1} to {s2} "
                f"starting at {t0=:.1f}, arriving at {dropoff['arrival_time']:.1f}"
            )
            logger.debug(f"{dropoff=}")
            best_arrival_time = dropoff["arrival_time"]
            best_dropoff = dropoff
            # add a bunch of extra fields in case we need them later for planning
            best_dropoff["segment_start"] = np.array([x1, y1])
            best_dropoff["segment_end"] = np.array([x2, y2])
            best_dropoff["timetable_index"] = i

    return best_dropoff


def distance_to_segment(x, s1, s2):
    return np.linalg.norm(x - closest_point_to_segment(x, s1, s2))


def point_on_segment(x, s1, s2):
    a = np.linalg.norm(x - s1)
    b = np.linalg.norm(x - s2)
    c = np.linalg.norm(s2 - s1)
    return np.isclose(a + b, c)


def test_is_acute_triangle():
    assert not is_acute_triangle([0, 0], [1, 0], [1, 1])
    assert is_acute_triangle([0, 0], [1, 0], [0.5, 1])


def test_closest_point_to_segment():
    np.testing.assert_almost_equal(
        closest_point_to_segment([0, 0], [1, -1], [1, 1]), np.array([1, 0])
    )

    np.testing.assert_almost_equal(
        closest_point_to_segment([0, 0], [1, -0.7], [1, 1]), np.array([1, 0])
    )

    np.testing.assert_almost_equal(
        closest_point_to_segment([0, 0], [1, 2], [1, 1]), np.array([1, 1])
    )

    np.testing.assert_almost_equal(
        closest_point_to_segment([0, 0], [1, -2], [1, -1]), np.array([1, -1])
    )

    np.testing.assert_almost_equal(
        closest_point_to_segment([0, 0], [1, 0], [10, 0]), np.array([1, 0])
    )

    np.testing.assert_almost_equal(
        closest_point_to_segment([0, 0], [-10, 0], [10, 0]), np.array([0, 0])
    )


def test_get_accessible_region():
    p = (0, 0)
    b1 = (1, -1)
    b2 = (1, 1)

    print(get_accessible_region(p, b1, b2, t1=0, vp=1, vb=1))
    print(get_accessible_region(p, b1, b2, t1=1.41, vp=1, vb=1))
    print(get_accessible_region(p, b1, b2, t1=1, vp=1, vb=10))


def test_find_best_dropoff_on_segment():
    dropoff = find_best_dropoff_on_segment([0.8, 0.2], [0.1, 0.1], [0.9, 0.1], 0.003, 0.03)
    np.testing.assert_almost_equal(
        dropoff['coords'],
        np.array([0.7899496, 0.1]),
    )


if __name__ == "__main__":
    # test_is_acute_triangle()
    # test_get_accessible_region()
    # test_closest_point_to_segment()
    test_find_best_dropoff_on_segment()
