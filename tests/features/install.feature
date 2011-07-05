Feature: Some basic installation scenarios

Scenario: Install hg-git
    Given I use "standard" environment
    When I execute pyg check hg-git
    Then one line matches False
    Then the return code is 0
    When I execute pyg install hg-git
    Then the return code is 0
    When I execute pyg check hg-git
    Then one line matches True
    Then the return code is 0

Scenario: Install misc packages
    Given I use "standard" environment
    When I execute pyg install <pkg>
    Then the return code is 0

    Examples:
        | pkg       |
        | bottle    |
        | mercurial |
        | lk        |
        | grin      |
        | gevent    |

#Scenario: Install a dev package [not supported yet, see #78]
#    Given I use "standard" environment
#    When I execute pyg install bottle==dev
#    Then the return code is 255
