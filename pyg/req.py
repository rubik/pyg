import operator
import itertools


class Version(object):
    def __init__(self, v):
        self.v = v
        self.parts = v.split('.')

    def __repr__(self):
        return 'Version({0})'.format(self.v)

    def __eq__(self, other):
        if len(self.parts) != len(other.parts):
            return False
        return all(p == p2 for p, p2 in itertools.izip(self.parts, other.parts))

    def __ge__(self, other):
        for p, p2 in itertools.izip_longest(self.parts, other.parts):
            if p is None and p2 is not None:
                return False
            elif p2 is None:
                return True
            elif p >= p2:
                return True
            elif p < p2:
                return False
        return False

    def __gt__(self, other):
        for p, p2 in itertools.izip_longest(self.parts, other.parts):
            if p is None and p2 is not None:
                return False
            elif p2 is None:
                return True
            elif p > p2:
                return True
            elif p < p2:
                return False
        return False

    def __le__(self, other):
        for p, p2 in itertools.izip_longest(self.parts, other.parts):
            if p is None and p2 is not None:
                return True
            elif p2 is None:
                return False
            elif p <= p2:
                return True
            elif p > p2:
                return False
        return False

    def __lt__(self, other):
        for p, p2 in itertools.izip_longest(self.parts, other.parts):
            if p is None and p2 is not None:
                return True
            elif p2 is None:
                return False
            elif p < p2:
                return True
            elif p > p2:
                return False
        return False


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

    def split(self):
        for c in ('==', '>=', '>', '<=', '<'):
            if c in self.req:
                self.name, self.op, self.version = map(str.strip, self.req.partition(c))
                self.version = Version(self.version)
                break
        else:
            self.name = self.req.split()[0]
            self.version = None

    @ staticmethod
    def find_version(s):
        v = []
        for c in s:
            if c.isdigit() or c == '.':
                v.append(c)
            else:
                break
        return Version(''.join(v).strip('.')) ## FIXME do we really need .strip() ?
        

    def best_match(self, reqs):
        matched = {}
        for r in reqs:
            parts = r.split('-')
            version = Requirement.find_version('-'.join(parts[1:]))
            if self.version is None or self.OPMAP[self.op](version, self.version):
                matched[version] = r
        if len(matched) == 0:
            return None
        elif len(matched) == 1:
            return matched[matched.keys()[0]]
        ## The highest version possible
        return matched[max(matched)] ## OR matched[sorted(matched.keys(), reverse=True)[0]]?