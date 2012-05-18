def empty(iterator):
    try:
        next(iterator)
        return False
    except StopIteration:
        return True
