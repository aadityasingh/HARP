"""
This file constructs a year: contest: list of problem numbers map
to scrape the AoPS wiki

Note: Some problems may not be present, and some may be duplicates
We will handle those cases in a different file -- this file just constructs an exhaustive list.
"""

# Initialize all years
years = [str(y) for y in range(1950, 2022)] + ["2021_Fall"] + [str(y) for y in range(2022, 2025)]
all_year_contest_problem_map = {year: dict() for year in years}

# All AMC8
# In the school year of 2021-2022, the AMC 8 was moved to past the new year
# so there was no 2021 exam
for year in range(1999, 2021):
    all_year_contest_problem_map[str(year)]['AMC_8'] = range(1, 26)
for year in range(2022, 2025):
    all_year_contest_problem_map[str(year)]['AMC_8'] = range(1, 26)


# AMC10 + 12
for contest in [10, 12]:
    for sub in ['A', 'B']:
        for year in range(2002, 2024):
            all_year_contest_problem_map[str(year)]['AMC_{}{}'.format(contest, sub)] = range(1, 26)
        # In the school year of 2021-2022, the AMC 10/12 was moved to before the new year
        # so there was a 2021 spring and fall exam
        all_year_contest_problem_map["2021_Fall"]['AMC_{}{}'.format(contest, sub)] = range(1, 26)

    for year in [2000, 2001]:
        all_year_contest_problem_map[str(year)]['AMC_{}'.format(contest)] = range(1, 26)


# All AJHSME
for year in range(1985, 1999):
    all_year_contest_problem_map[str(year)]['AJHSME'] = range(1, 26)


# All AHSME
# some of these are incomplete -- will need to figure out how to detect
for year in range(1950, 1960):
    all_year_contest_problem_map[str(year)]['AHSME'] = range(1, 51)

for year in range(1960, 1968):
    all_year_contest_problem_map[str(year)]['AHSME'] = range(1, 41)

for year in range(1968, 1974):
    all_year_contest_problem_map[str(year)]['AHSME'] = range(1, 36)

for year in range(1974, 2000):
    all_year_contest_problem_map[str(year)]['AHSME'] = range(1, 31)


# All AIME
for year in range(1983, 2000):
    all_year_contest_problem_map[str(year)]['AIME'] = range(1, 16)

for contest in ['I', 'II']:
    for year in range(2000, 2025):
        all_year_contest_problem_map[str(year)]['AIME_{}'.format(contest)] = range(1, 16)


# All USAMO
for year in range(1972, 1996):
    all_year_contest_problem_map[str(year)]['USAMO'] = range(1, 6)

for year in range(1996, 2025):
    all_year_contest_problem_map[str(year)]['USAMO'] = range(1, 7)


# All USAJMO
for year in range(2010, 2025):
    all_year_contest_problem_map[str(year)]['USAJMO'] = range(1, 7)


total_problems = 0
for y in all_year_contest_problem_map:
    for c in all_year_contest_problem_map[y]:
        total_problems += len(all_year_contest_problem_map[y][c])
# total_problems = 6574


def has_choices(contest_name):
    return contest_name.startswith('AMC') or contest_name.endswith('SME')


def has_answer(contest_name):
    return not contest_name.endswith('MO')
