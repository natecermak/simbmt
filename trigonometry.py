import numpy as np


def is_acute_triangle(p1, p2, p3):
    a = np.linalg.norm(np.array(p2) - np.array(p1))
    b = np.linalg.norm(np.array(p3) - np.array(p1))
    c = np.linalg.norm(np.array(p3) - np.array(p2))
    sides = np.sort([a, b, c])
    print(sides)
    return sides[2]**2 < sides[1]**2 + sides[0]**2


def test_is_acute_triangle():
    assert not is_acute_triangle([0,0], [1, 0], [1, 1]) 
    assert is_acute_triangle([0,0], [1, 0], [0.5, 1]) 



if __name__ == "__main__":
    test_is_acute_triangle()


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
    a = (1 / vp**2) - (1 / vb**2)
    b = 2 * (alpha @ beta / vp**2 - t1 / vb)
    c = np.linalg.norm(alpha)**2 / vp**2 - t1**2

    discriminant = b**2 - 4 * a * c
    if discriminant < 0:
        # no roots, therefore there is no accessible region of the segment
        return None
    elif discriminant >= 0:
        roots = (-b + np.array([-1, 1]) * np.sqrt(discriminant)) / (2 * a)
        # find overlap between root interval and [0, b2-b1]
        d1 = np.max([0, roots[0]])
        d2 = np.min([d_max, roots[1]])
        if d2 >= d1:
            return [b1 + d1 * beta, b1 + d2 * beta]
        else:
            return None




