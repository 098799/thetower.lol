from functools import partial
from operator import ge, le

from hardcoding import colors, position_colors, position_stratas, stratas, sus_person


def simple_format(color):
    return f"color: {color}"


def detailed_format(color, which, how_many):
    color_results = [None for _ in range(how_many)]
    color_results[which] = f"color: {color}"
    return color_results


def color_strata(wave, stratas, colors, operator, formatting_function):
    for strata, color in zip(stratas[::-1], colors[::-1]):
        if operator(wave, strata):
            return formatting_function(color)


color_top = partial(color_strata, stratas=stratas, colors=colors, operator=ge, formatting_function=simple_format)
color_position = partial(color_strata, stratas=position_stratas, colors=position_colors, operator=le, formatting_function=simple_format)


def color_nickname__detail(row, roles_by_id, stratas, colors, operator, formatting_function):
    return color_strata(roles_by_id[row.id], stratas, colors, operator, formatting_function)


detailed_format__base = partial(detailed_format, which=2, how_many=6)
detailed_format__top = partial(detailed_format, which=1, how_many=5)
detailed_format__top_position = partial(detailed_format, which=3, how_many=5)

color_nickname = partial(color_nickname__detail, stratas=stratas, colors=colors, operator=ge, formatting_function=detailed_format__base)
color_nickname__top = partial(color_nickname__detail, stratas=stratas, colors=colors, operator=ge, formatting_function=detailed_format__top)
color_position__top = partial(color_strata, stratas=position_stratas, colors=position_colors, operator=le, formatting_function=simple_format)


def am_i_sus(name):
    if name == sus_person:
        return "color: #FF6666"


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
