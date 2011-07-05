Feature: check

Scenario: Install grin and bottle
    Given I use "standard" environment
    Given I execute pyg install bottle
    Then the return code is 0
    Given I execute pyg install grin
    Then the return code is 0

Scenario: Check Uninstalled packages
    Given I use "standard" environment
    When I execute pyg check <pkg>
    Then one line matches False
    Then the return code is 0

        Examples:
            | pkg       |
            | bottle    |
            | flask     |
            | ZODB3     |
            | gevent    |

Scenario: Check Installed packages
    Given I use "standard" environment
    When I execute pyg check <pkg>
    Then one line matches True
    Then the return code is 0

    Examples:
        | pkg       |
        | bottle    |
        | grin      |
