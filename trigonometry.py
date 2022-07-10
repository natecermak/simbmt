import numpy as np


def is_acute_triangle(p1, p2, p3):
    a = np.linalg.norm(np.array(p2) - np.array(p1))
    b = np.linalg.norm(np.array(p3) - np.array(p1))
    c = np.linalg.norm(np.array(p3) - np.array(p2))
    sides = np.sort([a, b, c])
    print(sides)
    return sides[2] ** 2 < sides[1] ** 2 + sides[0] ** 2


def test_is_acute_triangle():
    assert not is_acute_triangle([0, 0], [1, 0], [1, 1])
    assert is_acute_triangle([0, 0], [1, 0], [0.5, 1])


def get_accessible_region(p, b1, b2, t1: float, vp: float, vb: float):
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
        nearest = (1-t) * s1 + t * s2
    else:
        d1 = np.linalg.norm(x - s1)
        d2 = np.linalg.norm(x - s2)
        nearest = s1 if d1 < d2 else s2

    return nearest


def test_closest_point_to_segment():
    np.testing.assert_almost_equal(
        closest_point_to_segment([0,0], [1,-1], [1,1]), 
        np.array([1,0])
    )
    
    np.testing.assert_almost_equal(
        closest_point_to_segment([0,0], [1,-0.7], [1,1]), 
        np.array([1,0])
    )
    
    np.testing.assert_almost_equal(
        closest_point_to_segment([0,0], [1,2], [1,1]), 
        np.array([1,1])
    )
    
    np.testing.assert_almost_equal(
        closest_point_to_segment([0,0], [1,-2], [1,-1]), 
        np.array([1,-1])
    )

    np.testing.assert_almost_equal(
        closest_point_to_segment([0,0], [1,0], [10,0]), 
        np.array([1,0])
    )

    np.testing.assert_almost_equal(
        closest_point_to_segment([0,0], [-10,0], [10,0]), 
        np.array([0,0])
    )


def distance_to_segment(x, s1, s2):
    return np.linalg.norm(x - closest_point_to_segment(x, s1, s2))


def test_get_accessible_region():
    p = (0, 0)
    b1 = (1, -1)
    b2 = (1, 1)

    print(get_accessible_region(p, b1, b2, t1=0, vp=1, vb=1))
    print(get_accessible_region(p, b1, b2, t1=1.41, vp=1, vb=1))
    print(get_accessible_region(p, b1, b2, t1=1, vp=1, vb=10))


def when_to_get_off_bus():
    pass


if __name__ == "__main__":
    # test_is_acute_triangle()
    # test_get_accessible_region()
    test_closest_point_to_segment()
