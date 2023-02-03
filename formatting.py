from functools import partial

from hardcoding import colors, stratas, sus_person


def color_top(wave):
    for strata, color in zip(stratas[::-1], colors[::-1]):
        if wave >= strata:
            return f"color: {color}"


def color_nickname__detail(row, roles_by_id, which, how_many):
    wave = roles_by_id[row.id]

    for strata, color in zip(stratas[::-1], colors[::-1]):
        if wave >= strata:
            color_results = [None for _ in range(how_many)]
            color_results[which] = f"color: {color}"
            return color_results


color_nickname = partial(color_nickname__detail, which=2, how_many=6)
color_nickname__top = partial(color_nickname__detail, which=1, how_many=4)


def am_i_sus(name):
    if name == sus_person:
        return "color: red"


def color(value):
    if value.startswith("+"):
        return "color: green"
    elif value.startswith("-"):
        return "color: red"
    return "color: orange"


def strike(text):
    result = ""
    for c in text:
        result = result + c + "\u0336"
    return result
