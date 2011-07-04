Feature: Environments cleanup

Scenario: Remove hg-git (if present)
    Given I use "foo2.7" environment
    When I execute pyg remove -y hg-git
    Then the return code is 0
    When I execute pyg check hg-git
    Then one stdout line matches False

Scenario Outline: Remove other packages
    Given I use "foo2.7" environment
    When I execute pyg remove -y <pkg>
    Then the return code is 0
    When I execute pyg check <pkg>
    Then one stdout line matches False

        Examples:
            | pkg       |
            | bottle    |
            | mercurial |
            | lk        |
            | grin      |