

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