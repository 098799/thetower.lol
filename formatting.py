from hardcoding import colors, stratas, sus_person


def color_top(wave):
    for strata, color in zip(stratas[::-1], colors[::-1]):
        if wave >= strata:
            return f"color: {color}"


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
