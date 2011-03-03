import re
import os.path
import urllib2
import collections


__all__ = ['Finder', 'request']


def request(url):
    r = urllib2.Request(url)
    return urllib2.urlopen(r).read()


class _FileMapper(collections.defaultdict):

    def __missing__(self, key):
        return self['others']


class Finder(object):

    base_url = 'http://pypi.python.org/simple/'
    file_regex = re.compile(r'<a\s?href="(?P<href>[^"]+)">(?P<name>[^\<]+)</a><br/>')
    link_regex = re.compile(r'<a\s?href="(?P<href>[^"]+)"\srel="(?P<rel>[^"]+)">(?P<name>[^\<]+)</a><br/>')

    def __init__(self, packname):
        self.url = '{0}{1}'.format(self.base_url, packname)

    def find(self):
        files = _FileMapper(list, {'.gz': {}, '.bz2': {}, '.zip': {},
                                  '.egg': {}, 'others': {}
                                 }
                           )

        print 'Checking: {0}'.format(self.url)
        data = request(self.url)
        f = self.file_regex.findall(data)
        links = self.link_regex.findall(data)
        for l, file in f:
            ext = os.path.splitext(file)[1]
            files[ext][file] = l
        return files, links