

def is_installed(packname, v=None):
    def _inner(packname, v):
        try:
            packname = __import__(packname)
        except ImportError:
            return False
        else:
            if v is not None:
                return v == packname.__version__ or tuple(v.split('.')) == packname.__version__
            return True
    if not _inner(packname, v):
        packname = packname.lower()
        return _inner(packname, v)
    return True