import operator


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
                self.version = float(self.version)
                break
        else:
            raise ValueError('The request does not make any sense') ## FIXME: We have to search the newest

    @ staticmethod
    def find_version(s):
        v = []
        for c in s:
            if c.isdigit() or c == '.':
                v.append(c)
            else:
                break
        return float(''.join(v).strip('.')) ## FIXME do we really need .strip() ?
        

    def best_match(self, reqs):
        matched = {}
        for r in reqs:
            parts = r.split('-')
            version = Requirement.find_version('-'.join(parts[1:]))
            if self.OPMAP[self.op](version, self.version):
                matched[version] = r
        if len(matched) == 0:
            return None
        elif len(matched) == 1:
            return matched[matched.keys()[0]]
        return matched[sorted(matched.keys(), reverse=True)[0]] ## The highest version possible