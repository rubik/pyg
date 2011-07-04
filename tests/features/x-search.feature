Feature: Use search functionality

Scenario: search for popular package bottle
    Given I use "foo2.7" environment
    When I execute pyg search bottle
    Then many lines matches bottle
    When I execute pyg search -e bottle
    Then one line matches bottle
    When I execute pyg search -ae bottle
    Then many line matches bottle\s+

Scenario: search for unique package "zicbee-mplayer"
    Given I use "foo2.7" environment
    When I execute pyg search zicbee-mplayer
    Then all lines matches zicbee-mplayer
    When I execute pyg search -e zicbee-mplayer
    Then one line matches zicbee-mplayer
    When I execute pyg search -ae zicbee-mplayer
    Then all lines matches zicbee-mplayer\s+
