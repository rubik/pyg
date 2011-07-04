Feature: Some basic installation scenarios

Scenario: Install hg-git
    Given I use "foo2.7" environment
    When I execute pyg install hg-git
    Then the return code is 0
    When I execute pyg check hg-git
    Then the return code is 0

Scenario: Install misc packages
    Given I use "foo2.7" environment
    When I execute pyg install <pkg>
    Then the return code is 0

        Examples:
            | pkg       |
            | bottle    |
            | mercurial |
            | lk        |
            | grin      |