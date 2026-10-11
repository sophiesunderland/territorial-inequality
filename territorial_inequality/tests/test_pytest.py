"""Basic tests for the template package.

Overview:
- Purpose: Verify example behavior and error handling.
- Used by: `pytest` via `make test` and CI.
- Adds: Confidence that core functionality works after changes.
- Learn more: https://docs.pytest.org/en/stable/getting-started.html

How to adapt this file to your own function:
1. Import your function at the top of the file.
2. Update one "known values" test with 3-5 concrete input/output examples.
3. Add at least one edge case (for example: empty input, zero, or one).
4. Add at least one invalid-input test using ``pytest.raises``.
5. Keep one regression test per bug you fix in the future.

Additional tutorials:
- Pytest examples: https://docs.pytest.org/en/stable/example/index.html
- Good test structure: https://docs.pytest.org/en/stable/explanation/goodpractices.html
- Python testing intro (Real Python): https://realpython.com/python-testing/
"""

import pytest

'''Test the fix country name code line.'''
@pytest.mark.parametrize(
    ("country", "expected"),
    [
        ("Zambia", "Zambia"),
        ("Burkina Faso", "BurkinaFaso"),
        ("South Africa", "SouthAfrica"),
        ("  South Africa  ", "SouthAfrica"),
    ],
)
def test_country_filename_formatting(country, expected):
    country_file = country.replace(" ", "")
    assert country_file == expected
    

'''Check that density is calculated correctly'''
def test_density_calculation():
    length_km = 100
    area_km2 = 50

    density = length_km / area_km2

    assert density == pytest.approx(2.0)

