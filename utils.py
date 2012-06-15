def empty(iterator):
    try:
        if not hasattr(iterator, "__next__"):
            iterator = iter(iterator)
        next(iterator)
        return False
    except StopIteration:
        return True

def diffNth(iterable, n=1, offset=0):
    i = 0
    iterator = iter(iterable)
    for x in xrange(offset):
        next(iterator)
    prev = next(iterator)
    for item in iterator:
        i += 1
        if i == n:
            i = 0
            yield item - prev
            prev = item

def intNth(iterable, n=1, offset=0):
    i = 0
    iterator = iter(iterable)
    for x in xrange(offset):
        next(iterator)
    s = next(iterator)
    for item in iterator:
        i += 1
        if i == n:
            i = 0
            yield s
            s = 0
        s += item
    if i == n-1:
        yield s
