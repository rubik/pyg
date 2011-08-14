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

Scenario Outline: Install misc packages
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
        | buzhug    |

Scenario: Pack & bundle them individually
    Given I use "standard-2.7" environment
    When I remove "foobar.zip"
    When I execute pyg pack foobar.zip <pkg>
    Then the return code is 0

    Examples:
        | pkg       |
        | bottle    |
        | mercurial |
        | lk        |
        | grin      |
        | gevent    |
        | buzhug    |

Scenario: Dump installed packages list
    Given I use "standard-2.7" environment
    Given I use "tmp_install" temporary folder
    When I execute pyg site -f requirements
    Then many lines match [a-zA-Z_]+==\d+[\d.]*.*
    Then the return code is 0

Scenario Outline: Upgrade all packages
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
        | buzhug    |


Scenario: Bundle all packages
    Given I use "standard-2.7" environment
    Given I use "tmp_install" temporary folder
    When I execute pyg bundle -r requirements mybundle
    Then the return code is 0


Scenario Outline: Remove all packages
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
        | buzhug    |


Scenario: UnBundle all packages
    Given I use "standard-2.7" environment
    Given I use "tmp_install" temporary folder
    When I execute pyg install -r requirements mybundle
    Then the return code is 0


Scenario Outline: Install misc packages (with operators)
    Given I use "standard-2.7" environment
    Given I use "tmp_install" temporary folder
    When I execute pyg install -U "<pkg>"
    Then the return code is 0

    Examples:
        | pkg            |
        | bottle==0.9.5  |
        | dulwich!=0.7.1 |
        | grin<=1.2.1    |
        | buzhug>1.6     |
        | gevent<0.13.6  |
        | lk>=1          |


Scenario Outline: Install packages from VCS
    Given I use "standard-2.7" environment
    Given I use "tmp_install" temporary folder
    When I execute pyg install <url>
    Then the return code is 0

    Examples:
        | url                                                         |
        | git+git@github.com:rubik/pkgtools.git#egg=pkgtools          |
        | git+https://github.com/fdev31/zicbee.git#egg=zicbee         |
        | hg+https://rubik@bitbucket.org/neithere/argh#egg=argh       |
        | hg+https://rubik@bitbucket.org/birkenfeld/sphinx#egg=sphinx |
        | bzr+lp:wadllib#egg=wadllib                                  |

Scenario Outline: Install misc packages (with multiple versions)
    Given I use "standard-2.7" environment
    Given I use "tmp_install" temporary folder
    When I execute pyg install -U "<pkg>"
    Then the return code is 0

    Examples:
        | pkg                        |
        | pkgtools>=0.4,!=0.5,<0.6.3 |
        | zicbee>0.7,!=0.8,<1        |


#Scenario: Install a dev package [not supported yet, see #78]
#    Given I use "standard-2.7" environment
#    When I execute pyg install bottle==dev
#    Then the return code is 255
