'''
Pyg's own HelpFormatter for argparse.
The standard help would be like this:

    usage: pyg [-h] [-d] [--verbose] [-v]

          {search,shell,help,list,update,remove,freeze,link,bundle,install,
          download,unlink,check}
               ...

    positional arguments:
      {search,shell,help,list,update,remove,freeze,link,bundle,install,download,unlink,check}
        install
        remove
        freeze
        link
        unlink
        list
        search
        check
        download
        update
        shell
        bundle
        help

It repeats 3 times the commands without giving some useful information.
With this modification Pyg's help is more comprehensive and useful:

usage: pyg [-h] [-v] [-d] [--verbose] [command] args
or: pyg command -h
or: pyg command --help

Available commands:
	install [-eUAngu] [-r <path>] [-i <url>] [-d <path>] [--no-scripts] [--no-data] packname
		Install a package

	bundle [-r <path>] [-e <requirement>] bundlename packages
		Create bundles (like Pip's ones)

	download [-u] [-d <path>] [-p <ext>] packname
		Download a package

	remove [-yi] [-r <path>] packname
		Remove a package

	freeze [-c] [-f <path>]
		Freeze current environment (i.e. installed packages)

	check [-i] packname
		Check if a package is installed

	search [-ea] query
		Search PyPI

	unlink [-a] path
		Remove a previously added directory (with link) from PYTHONPATH

	list packname
		List all versions for a package

	update [-y]
		Check for updates for installed packages

	link path
		Add a directory to PYTHONPATH

	shell
		Fire up Pyg Shell

	help
		Show this help and exit
'''


import re
import argparse


TEMPLATE = '''{0}

Available commands:
{1}
'''


def _formatter(parser):

    class PygHelpFormatter(argparse.HelpFormatter):

        _argh_parser = None

        def _get_commands(self):
            commands = {}
            actions = [a for a in self._argh_parser._actions if isinstance(a, argparse._SubParsersAction)]
            for action in actions:
                ## List all subcommands (i.e. install, remove, etc.) and their
                ## options. None is the placeholder for an action's help (if there is)
                for subcommand, parser in action.choices.iteritems():
                    commands[subcommand] = [None, parser._actions]
                ## Look for actions' help
                for pseudo_action in action._choices_actions:
                    if pseudo_action.dest in commands:
                        commands[pseudo_action.dest][0] = pseudo_action.help
            return commands

        def _format_usage(self):
            return 'usage: pyg [-h] [-v] [-d] [--verbose] [--no-colors] [command] args\n' \
                   'or: pyg command -h\n' \
                   'or: pyg command --help'

        def _format_args(self):
            args = []
            _spaces_re = re.compile(r'[ ]+')
            for command, help_actions in self._get_commands().iteritems():
                help, actions = help_actions

                ## Split the action depending on their type:
                ##
                ## - no_value: -e, -g, -A, -U, etc.
                ## - with_value: -i <url>, -r <path>, etc.
                ## - one_opt: --no-scripts, --no-data, etc.
                ## - positional: packname, bundlename, etc.
                no_value, with_value, one_opt, positional = [], [], [], []
                for action in actions:
                    if isinstance(action, argparse._HelpAction):
                        continue
                    options = action.option_strings
                    if not options:
                        positional.append(action.dest)
                    elif action.metavar:
                        with_value.append((options[0], action.metavar))
                    else:
                        if len(options) == 1:
                            one_opt.append(options[0])
                            continue
                        no_value.append(options[0])

                line = '{0} [-{1}] {2} {3} {4}\n\t\t{5}'.format(
                    command,
                    ''.join(option.strip('-') for option in no_value),
                    ' '.join('[{0} {1}]'.format(option, metavar) for option, metavar in with_value),
                    ' '.join('[{0}]'.format(opt) for opt in one_opt),
                    ' '.join(positional),
                    help.strip() or ''
                )

                ## Remove [-] in case there weren't options with no value
                line = line.replace('[-]', '')
                ## Replace multiple spaces
                line = _spaces_re.sub(' ', line)
                args.append(line.lstrip())

            return '\t' + '\n\t'.join(sorted(args, key=lambda line: -len(line.split('\n\t\t')[0]))) + '\n'

        def format_help(self):
            return TEMPLATE.format(
                self._format_usage(),
                self._format_args()
            )

    PygHelpFormatter._argh_parser = parser
    return PygHelpFormatter
