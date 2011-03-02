from .inst import Installer


def install_from_name(name):
    return Installer(name).install()

def install_func(args):
    if args.develop:
        raise NotImplementedError('not implemented yet')
    return install_from_name(args.packname)