Feature: Some basic installation scenarios

Scenario: Install hg-git
    Given I use "standard-2.7" environment
    When I execute pyg check hg-git
    Then one line matches False
    Then the return code is 0
    When I execute pyg install hg-git
    Then the return code is 0
    When I execute pyg check hg-git
    Then one line matches True
    Then the return code is 0

Scenario: Install misc packages
    Given I use "standard-2.7" environment
    When I execute pyg install <pkg>
    Then the return code is 0

    Examples:
        | pkg       |
        | bottle    |
        | mercurial |
        | lk        |
        | grin      |
        | gevent    |

Scenario: Pack & bundle them individually
    Given I use "standard-2.7" environment
    When I remove "foobar.zip"
    When I execute pyg pack foobar.zip <pkg>
    Then the return code is 0
    When I execute pyg pack -d foobar.zip <pkg>
    Then the return code is 0

    Examples:
        | pkg       |
        | bottle    |
        | mercurial |
        | lk        |
        | grin      |
        | gevent    |

Scenario: Dump installed packages list
    Given I use "standard-2.7" environment
    Given I use "tmp_install" temporary folder
    When I execute pyg site -f requirements
    Then many lines match [a-zA-Z_]+==\d+[\d.]*.*
    Then the return code is 0

Scenario: Upgrade all packages
    Given I use "standard-2.7" environment
    When I execute pyg install -U <pkg>
    Then the return code is 0

    Examples:
        | pkg       |
        | bottle    |
        | mercurial |
        | lk        |
        | grin      |
        | gevent    |


Scenario: Bundle all packages
    Given I use "standard-2.7" environment
    Given I use "tmp_install" temporary folder
    When I execute pyg bundle -r requirements mybundle mercurial
    Then the return code is 0

Scenario: Remove all packages
    Given I use "standard-2.7" environment
    When I execute pyg remove -y <pkg>
    Then the return code is 0

    Examples:
        | pkg       |
        | bottle    |
        | mercurial |
        | lk        |
        | grin      |
        | gevent    |


Scenario: UnBundle all packages
    Given I use "standard-2.7" environment
    Given I use "tmp_install" temporary folder
    When I execute pyg install -r requirements mybundle
    Then the return code is 0


#Scenario: Install a dev package [not supported yet, see #78]
#    Given I use "standard-2.7" environment
#    When I execute pyg install bottle==dev
#    Then the return code is 255
