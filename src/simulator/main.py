from typing import Callable
from simulator.code.code import Code, CodeResult
from simulator.code.rs import RS
from simulator.code.hh import HH
from simulator.code.lrc import LRC
from simulator.code.hhlrc import HHLRC
from simulator.code.design2 import DESIGN2
from simulator.code.clay import CLAY
from simulator.graphic.axis import Scale, ScaleKind
from simulator.graphic.histogram import Histogram, HistogramEntry

S: int = 17
R: int = 10
LOCAL_PARITIES: tuple[int, ...] = (1, 2, 3)
LOSSES: tuple[int, ...] = (1, 2, 3)
SYMBOL_TITLE: str = "Coût de lecture normalisé par rapport à Reed–Solomon"
SEQUENTIAL_TITLE: str = "Coût de lecture séquentielle normalisé par rapport à Reed–Solomon"

class Series:

    def __init__(self, code: Code, color: str):
        self.CODE: Code = code
        self.COLOR: str = color

def compared(local_parities: int) -> list[Series]:
    n = S + R
    built = []
    built.append(Series(RS(S, R), '#898781'))
    built.append(Series(HH(S, R), '#1baf7a'))
    built.append(Series(LRC(S, R, local_parities), '#4a3aa7'))
    built.append(Series(HHLRC(S, R, local_parities), '#2a78d6'))
    built.append(Series(DESIGN2(S, R), '#e34948'))
    built.append(Series(CLAY(S, R, n - 1), '#eb6834'))
    built.append(Series(CLAY(S, R, n - 2), '#eda100'))
    built.append(Series(CLAY(S, R, n - 3), '#e87ba4'))
    return built

def symbol_scales() -> list[Scale]:
    return [Scale(step=0.05)]

def sequential_scales() -> list[Scale]:
    built = []
    built.append(Scale(limit=2.0, step=0.2))
    built.append(Scale(kind=ScaleKind.LOG))
    return built

def simulate(plotted: list[Series], aggregate: Callable[[Code, int], CodeResult], losses: int) -> list[HistogramEntry]:
    entries = []
    for series in plotted:
        entries.append(HistogramEntry(series.CODE, aggregate(series.CODE, losses), series.COLOR))
    return entries

def render(name: str, entries: list[HistogramEntry], scales: list[Scale], title: str) -> None:
    histogram = Histogram(name, scales=scales, measure=title)
    for entry in entries:
        histogram.add(entry)
    histogram.save()

def main():
    for local_parities in LOCAL_PARITIES:
        plotted = compared(local_parities)
        for losses in LOSSES:
            name = f"S{S}_R{R}_L{local_parities}_E{losses}"
            render(f"{name}_symbol", simulate(plotted, Code.avg_normalized_cost, losses), symbol_scales(), SYMBOL_TITLE)
            render(f"{name}_sequential", simulate(plotted, Code.avg_normalized_sequential_read_cost, losses), sequential_scales(), SEQUENTIAL_TITLE)

if __name__ == "__main__":
    main()
