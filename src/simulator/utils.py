import math

def build_params(n: int, e_min: int, ratio: float) -> tuple[int, int, int, int, float]:
    s = math.floor(n / ratio)
    g = n - s
    r = min(g, e_min)
    l = g - r
    n = s + r + l
    ratio = n / s
    return n, s, r, l, ratio

def build_params_list(n: int, e_min: int, ratios: tuple[float, ...]) -> list[tuple[int, int, int, int, float]]:
    params_list: list[tuple[int, int, int, int, float]] = []
    for ratio in ratios:
        params = build_params(n, e_min, ratio)
        if params not in params_list:
            params_list.append(params)
    return params_list

def format_number(value) -> str:
    s = f"{round(value, 1)}"
    return s if not '.' in s else s.rstrip('0').rstrip('.')
