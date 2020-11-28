import functools

def genreq(cellprops=[], entities=[], worldparams=[]):
    # Return the decorator function with the parameters above available via closures.
    def funcdec(func):
        @functools.wraps(func)
        def dec(*args, **kwargs):
            retval = func(*args, **kwargs)

            return retval
        
        setattr(dec, 'cellprops', cellprops)
        setattr(dec, 'entities', entities)
        setattr(dec, 'worldparams', worldparams)

        return dec
    
    return funcdec