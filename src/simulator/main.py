import math
from simulator.schema.rs import RS
from simulator.schema.hh import HH
from simulator.schema.lrc import LRC
from simulator.schema.hhlrc import HHLRC
from simulator.utils import build_params_list
from simulator.graph.histogram import Histogram, HistogramEntry

CHUNKS: int = 36
RATIOS_TARGETS: tuple[float, ...] = (1.60, 1.65, 1.70, 1.75, 1.80)
TOLERANCE: int = math.ceil((CHUNKS / 3) + 1)
TOLERANCE_SIMULATED_MAX: int = 3
W: int = 1
STEP: float = 0.025

def main():
    for N, S, R, L, RATIO in build_params_list(CHUNKS, TOLERANCE, RATIOS_TARGETS):
        for E in range(1, min(TOLERANCE, TOLERANCE_SIMULATED_MAX) + 1):
            entries: list[HistogramEntry] = []
            hh=HH(S, R + L, W)
            hh_result = hh.avg_normalized_cost(E)
            entries.append(HistogramEntry(hh, hh_result, 'blue'))
            lrc=LRC(S, R, L)
            lrc_result = lrc.avg_normalized_cost(E)
            entries.append(HistogramEntry(lrc, lrc_result, 'green'))
            hhlrc=HHLRC(S, R, L, W)
            hhlrc_result = hhlrc.avg_normalized_cost(E)
            entries.append(HistogramEntry(hhlrc, hhlrc_result, 'orange'))
            name: str = f"N{N}_S{S}_R{R}_L{L}_E{E}_P{RATIO:.2f}"
            histogram = Histogram(name, entries, E, step=STEP)
            histogram.save()

if __name__ == "__main__":
    main()
