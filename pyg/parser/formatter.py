import argparse


def _formatter(parser):
        class PygHelpFormatter(argparse.HelpFormatter):
            def format_help(self):
                return 'test\n'
        return PygHelpFormatter