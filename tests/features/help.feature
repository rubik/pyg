Feature: Be able to get some help

Scenario Outline: Global help
    Given I use "standard-2.7" environment

    Given I execute pyg <opt>
    Then one line matches usage:
    Then one line matches Available commands:
    Then the return code is 0

    Examples:

        | opt       |
        | -h        |
        | help      |
        | --help    |

Scenario Outline: Specific help
    Given I use "standard-2.7" environment
    Given I execute pyg <cmd> <opt>
    Then one line matches usage:
    Then one line matches optional arguments:
    Then the return code is 0

    Examples:
        | cmd      | opt       |
        | install  | -h        |
        | install  | --help    |
        | search   | --help    |
        | list     | --help    |
        | update   | --help    |
        | link     | --help    |
        | shell    | --help    |
        | help     | --help    |
        | check    | --help    |
        | site     | --help    |
        | pack     | --help    |
        | remove   | --help    |
        | download | --help    |
        | bundle   | --help    |

Scenario Outline: Version
    Given I use "standard-2.7" environment
    Given I execute pyg <cmd>
    Then one line matches 0.8a
    Then the return code is 0

    Examples
        | cmd       |
        | -v        |
        | --version |
