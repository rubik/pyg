Feature: Be able to remove packages

Scenario: Install then Uninstall <pkg>
    Given I use "standard" environment
    Given I execute pyg check <pkg>
    Then a single line matches False
    Then the return code is 0
    Then no trace of <pkg>* is found
    When I execute pyg install <pkg>
    Then the return code is 0
    When I execute pyg check <pkg>
    Then a single line matches True
    Then the return code is 0
    When I execute pyg remove -y <pkg>
    Then the return code is 0
    When I execute pyg check <pkg>
    Then one line matches False
    Then the return code is 0
    Then no trace of <pkg>* is found

        Examples:
            | pkg       |
            | gevent    |
            | bottle    |
            | grin      |
            | lk        |
            | mercurial |
