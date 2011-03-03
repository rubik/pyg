from .inst import Installer


def install_from_name(name):
    return Installer(name).install()

def install_func(args):
    if args.develop:
        raise NotImplementedError('not implemented yet')
    if args.file:
        return Installer.from_file(args.file)
    if args.bundle:
        return Installer.from_bundle(args.bundle)
    return install_from_name(args.packname)