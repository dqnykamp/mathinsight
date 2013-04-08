from core import (exhaust, multiplex, debug, notempty, condition, chain,
        onaction, sfilter, yieldify, do_one, identity)
from traverse import top_down

def canon(*rules):
    """ Strategy for canonicalization

    Apply each branching rule in a top-down fashion through the tree.
    Multiplex through all branching rule traversals
    Keep doing this until there is no change.
    """
    return exhaust(multiplex(*map(top_down, rules)))
