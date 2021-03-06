Feature: check

Scenario: Install grin and bottle
    Given I use "standard-2.7" environment
    Given I execute pyg install -U bottle
    Then the return code is 0
    Given I execute pyg install -U grin
    Then the return code is 0

Scenario: Check Uninstalled packages
    Given I use "standard-2.7" environment
    When I execute pyg check <pkg>
    Then one line matches False
    Then the return code is 0

        Examples:
            | pkg       |
            | invalid   |
            | flask     |
            | ZODB3     |
            | dulwich   |

Scenario: Check Installed packages
    Given I use "standard-2.7" environment
    When I execute pyg check <pkg>
    Then one line matches True
    Then the return code is 0

    Examples:
        | pkg       |
        | bottle    |
        | grin      |
