from scipy import interpolate

import numpy

def mm(val, minimum, maximum):
    return min(max(val, minimum), maximum)


def add_color(col, delta):
    return (
        mm(col[0] + delta, 0.0, 1.0), 
        mm(col[1] + delta, 0.0, 1.0), 
        mm(col[2] + delta, 0.0, 1.0),
    )

def add_p(num, percent):
    '''
    Add `percent` percent to num. If `percent` is negative then subtract.
    '''

    return num + (num * percent)

def inter(vals):
    x_axis = list( range(0, len(vals)) )

    f = interpolate.interp1d(x_axis, vals, kind='quadratic')
    x_axis_new = numpy.arange(0, len(vals) - 1, 0.5)

    return x_axis_new, f(x_axis_new)

def inter_pts(pts):
    x = [pt[0] for pt in pts]
    y = [pt[1] for pt in pts]

    _, inter_x = inter(x)
    _, inter_y = inter(y)

    return list( zip(inter_x, inter_y) )