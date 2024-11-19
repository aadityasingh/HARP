from typing import Any

def map_difficulty(year: str, contest: str, number: int) -> int:
    """Rough difficulty mapping based off AoPS wiki
    https://artofproblemsolving.com/wiki/index.php/AoPS_Wiki:Competition_ratings

    For problems that appear in multiple contests, we use
    the mapping for the harder (and older) contest

    TODO: refine
    - One big thing is not sure how difficulty changes with year

    AMC8 1-10: 1
    AMC8 11-20: 1.5 (or 1)
    AMC8 21-25: 2
    
    AMC10 1-5: 1
    AMC10 6-10: 1.5 (or 2)
    AMC10 11-20: 2
    AMC10 21-25: 3
    
    AMC12 1-5: 1.5 (or 2)
    AMC12 6-10: 2
    AMC12 11-20: 3
    AMC12 21-25: 4
    
    AIME 1-5: 3
    AIME 6-9: 4
    AIME 10-12: 5
    AIME 13-15: 6

    USAJMO 1/4 - 6
    USAJMO 2/5 - 6.5 (or 7?)
    USAJMO 3/6 - 7

    USAMO 1/4 - 7
    USAMO 2/5 - 8
    USAMO 3/6 - 9
    """
    year_num = int(year.split("_")[0])

    if contest.startswith("AMC_8") or contest.startswith("AJHSME"):
        if number <= 20:
            return 1
        else:
            return 2
    elif contest.startswith("AMC_10"):
        if number <= 5:
            return 1
        elif number <= 20:
            return 2
        else:
            return 3
    elif contest.startswith("AMC_12"):
        if number <= 10:
            return 2
        elif number <= 20:
            return 3
        else:
            return 4
    elif contest.startswith("AIME"):
        if number <= 5:
            return 3
        elif number <= 9:
            return 4
        elif number <= 12:
            return 5
        else:
            return 6
    elif contest.startswith("AHSME"):
        # scaled it proportionally to AMC_12
        if year_num < 1960:
            # 50 problems
            if number <= 20:
                return 2
            elif number <= 40:
                return 3
            else:
                return 4
        elif year_num < 1967:
            # 40 problems
            if number <= 16:
                return 2
            elif number <= 32:
                return 3
            else:
                return 4
        elif year_num < 1973:
            # 35 problems
            if number <= 14:
                return 2
            elif number <= 28:
                return 3
            else:
                return 4
        else:
            # 30 problems
            if number <= 12:
                return 2
            elif number <= 24:
                return 3
            else:
                return 4
    elif contest.startswith("USAJMO"):
        if number == 1 or number == 4:
            return 6
        else:
            return 7
    elif contest.startswith("USAMO"):
        if number == 1 or number == 4:
            return 7
        elif number == 2 or number == 5:
            return 8
        else:
            return 9


def get_difficulty_from_problem(aops_prob: dict[str, Any]) -> int:
    year: str = aops_prob["year"]
    contest: str = aops_prob["contest"]
    number: int = aops_prob["number"]
    return map_difficulty(year, contest, number)
