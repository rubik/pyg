import operator
import itertools


class Version(object):
    def __init__(self, v):
        self.v = v
        while self.v[-1] == 0:
            self.v = self.v[:-2]

    def __str__(self):
        return self.v

    def __repr__(self):
        return 'Version({0})'.format(self.v)

    def __eq__(self, other):   
        if len(self.v) != len(other.v):
            return False
        return self.v == other.v

    def __ge__(self, other):
        return self.v >= other.v

    def __gt__(self, other):
        return self.v > other.v

    def __le__(self, other):
        return self.v <= other.v

    def __lt__(self, other):
        return self.v < other.v


class Requirement(object):

    OPMAP = {'==': operator.eq,
             '>=': operator.ge,
             '>': operator.gt,
             '<=': operator.le,
             '<': operator.lt
             }

    def __init__(self, req):
        self.req = req
        self.split()

    def __repr__(self):
        return 'Requirement({0})'.format(self.req)

    def split(self):
        for c in ('==', '>=', '>', '<=', '<'):
            if c in self.req:
                self.name, self.op, self.version = map(str.strip, self.req.partition(c))
                self.version = Version(self.version)
                break
        else:
            self.name = self.req.split()[0]
            self.version = None
            self.op = None

    @ staticmethod
    def find_version(s):
        v = []
        for c in s:
            if c.isdigit() or c == '.':
                v.append(c)
            else:
                break
        return Version(''.join(v).strip('.')) ## FIXME do we really need .strip() ?

    def match(self, v):
        try:
            return self.OPMAP[self.op](v, self.version)
        except KeyError: ## Operator not specified, so we pick up any version
            return True

    def best_match(self, reqs):
        matched = {}
        for r in reqs:
            parts = r.split('-')
            version = Requirement.find_version('-'.join(parts[1:]))
            if self.version is None or self.match(version):
                matched[version] = r
        if len(matched) == 0:
            return None
        elif len(matched) == 1:
            return matched[matched.keys()[0]]
        ## The highest version possible
        return matched[max(matched)] ## OR matched[sorted(matched.keys(), reverse=True)[0]]?