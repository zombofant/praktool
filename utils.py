def empty(iterator):
    try:
        if not hasattr(iterator, "__next__"):
            iterator = iter(iterator)
        next(iterator)
        return False
    except StopIteration:
        return True

def diffNth(iterable, n):
    i = 0
    iterator = iter(iterable)
    prev = next(iterator)
    for item in iterator:
        i += 1
        if i == n:
            i = 0
            yield item - prev
            prev = item

def intNth(iterable, n):
    i = 0
    iterator = iter(iterable)
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
