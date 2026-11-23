from simulator.code.code import Code

class Legend:

    def __init__(self, codes: list[Code]):
        self.CODES: list[Code] = codes

    def settings(self, code: Code) -> dict[str, float]:
        return code.get_settings()

    def common_settings(self) -> dict[str, float]:
        first = self.settings(self.CODES[0])
        return {k: v for k, v in first.items() if all(self.settings(s).get(k) == v for s in self.CODES)}

    def describe(self, settings: dict[str, float]) -> str:
        return ", ".join(f"{k} = {format_number(v, 2)}" for k, v in settings.items())

    def format(self, value: float) -> str:
        return f"{value:.2f}" if value < 10 else f"{value:.0f}"

    def label(self, code: Code, avg: float, low: float, high: float) -> str:
        common = self.common_settings()
        name = code.get_name()
        plain = name.replace("$", "").replace("\\", "")
        particular = {k: v for k, v in self.settings(code).items() if k not in common and f"{k.strip('$')}=" not in plain.replace(" ", "")}
        head = f"{name} ({self.describe(particular)})" if particular else name
        return f"{head} : {self.format(avg)} (de {self.format(low)} à {self.format(high)})"

def format_number(value, precision: int = 1) -> str:
    text = f"{round(value, precision)}"
    return text if not '.' in text else text.rstrip('0').rstrip('.')
