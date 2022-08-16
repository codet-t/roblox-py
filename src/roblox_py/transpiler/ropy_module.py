# Helps bridge the gap between Python and Luau
# We can't use any features in Python that isn't in Luau in this file specifically

def all(iterable):
    for element in iterable:
        if not element:
            return False
    return True