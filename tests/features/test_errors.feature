Feature: Test if errors are reported correctly
    Scenario: install not existing package
        Given I use "standard-2.7" environment
        When I execute pyg install thispackageiscertainlynotinpypi
        Then no stderr line matches \s*Traceback
        Then the return code is 1


