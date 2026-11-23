import numpy
from enum import Enum, auto

LADDER = [m * 10.0 ** k for k in range(-5, 7) for m in (1, 2, 5)]

class ScaleKind(Enum):

    LINEAR = auto()
    LOG = auto()

class Scale:

    def __init__(self, limit: float | None = None, kind: ScaleKind = ScaleKind.LINEAR, step: float = 0.05, decade: float | None = None):
        self.LIMIT: float | None = limit
        self.KIND: ScaleKind = kind
        self.STEP: float = step
        self.DECADE: float | None = decade

class Axis:

    def __init__(self, scales: list[Scale], values: list[float]):
        self.SCALES: list[Scale] = scales or [Scale()]
        self.BINS: numpy.ndarray = self.compute_bins(values)
        self.DRAW: numpy.ndarray = self.compute_draw()

    def compute_bins(self, values: list[float]) -> numpy.ndarray:
        self.EXACT: int | None = None
        high = max(max(values), 1.0) if values else 1.0
        low = min(values) if values else 1.0
        edges = [self._ladder_floor(low) if self.SCALES[0].KIND == ScaleKind.LOG else 0.0]
        kinds: list[ScaleKind] = []
        owners: list[Scale] = []
        for index, scale in enumerate(self.SCALES):
            start = edges[-1]
            if start >= high and index > 0:
                break
            last = index == len(self.SCALES) - 1
            end = high if scale.LIMIT is None else scale.LIMIT
            stop = max(end, high) if last else min(end, high)
            if scale.KIND == ScaleKind.LOG:
                new = self._ladder_edges(start, stop)
            else:
                count = int(numpy.ceil((stop - start) / scale.STEP - 1e-9))
                new = [start + k * scale.STEP for k in range(1, count + 1)]
            edges += new
            kinds += [scale.KIND] * len(new)
            owners += [scale] * len(new)
        near = [i for i, e in enumerate(edges) if numpy.isclose(e, 1.0)]
        if near:
            self.EXACT = near[0]
            gap = 1e-4 if kinds[min(self.EXACT, len(kinds) - 1)] == ScaleKind.LOG else 1e-3 * self.SCALES[0].STEP
            edges = edges[:self.EXACT + 1] + [1.0 + gap] + edges[self.EXACT + 1:]
            kinds.insert(self.EXACT, ScaleKind.LINEAR)
            owners.insert(self.EXACT, owners[min(self.EXACT, len(owners) - 1)])
        self.KINDS: list[ScaleKind] = kinds
        self.OWNERS: list[Scale] = owners
        return numpy.array(edges)

    def _ladder_floor(self, value: float) -> float:
        below = [v for v in LADDER if v <= value]
        return below[-1] if below else LADDER[0]

    def _ladder_edges(self, low: float, high: float) -> list[float]:
        inner = [v for v in LADDER if low < v < high]
        above = [v for v in LADDER if v >= high][:1]
        return inner + above

    def runs(self) -> list[tuple[int, int, ScaleKind]]:
        runs: list[tuple[int, int, ScaleKind]] = []
        for index, kind in enumerate(self.KINDS):
            if index == self.EXACT and runs:
                runs[-1] = (runs[-1][0], index + 1, runs[-1][2])
                continue
            if runs and runs[-1][2] == kind:
                runs[-1] = (runs[-1][0], index + 1, kind)
            else:
                runs.append((index, index + 1, kind))
        return runs

    def compute_draw(self) -> numpy.ndarray:
        widths: list[float | None] = [None] * len(self.KINDS)
        for first, stop, kind in self.runs():
            if kind == ScaleKind.LINEAR:
                for index in range(first, stop):
                    widths[index] = None if index == self.EXACT else float(self.BINS[index + 1] - self.BINS[index])
                continue
            span_before = float(self.BINS[first] - self.BINS[0]) if first else 0.0
            decades = max(1.0, float(numpy.log10(self.BINS[stop] / self.BINS[first])))
            decade = self.OWNERS[first].DECADE or (span_before / decades if span_before else 1.0)
            for index in range(first, stop):
                if index == self.EXACT:
                    widths[index] = None
                else:
                    widths[index] = decade * float(numpy.log10(self.BINS[index + 1] / self.BINS[index]))
        regular = [w for w in widths if w]
        span = sum(regular)
        self.SHIFT: float = max(min(regular), span * 0.05) if (self.EXACT is not None and regular) else 0.0
        return numpy.concatenate([[0.0], numpy.cumsum([self.SHIFT if w is None else w for w in widths])])

    def warp(self, value: float) -> float:
        index = int(numpy.clip(numpy.searchsorted(self.BINS, value, side="right") - 1, 0, len(self.BINS) - 2))
        left, right = float(self.BINS[index]), float(self.BINS[index + 1])
        if right <= left:
            return float(self.DRAW[index])
        if self.KINDS[index] == ScaleKind.LOG and left > 0:
            share = numpy.log10(value / left) / numpy.log10(right / left)
        else:
            share = (value - left) / (right - left)
        return float(self.DRAW[index]) + share * float(self.DRAW[index + 1] - self.DRAW[index])

    def widths(self) -> numpy.ndarray:
        return numpy.diff(self.DRAW)

    def centres(self) -> numpy.ndarray:
        return (self.DRAW[:-1] + self.DRAW[1:]) / 2.0

    def bounds(self) -> list[float]:
        if self.EXACT is None:
            return [float(b) for b in self.BINS]
        reference = float(self.BINS[self.EXACT])
        width = float(self.BINS[self.EXACT + 1]) - reference
        return [float(b) for b in self.BINS if abs(b - reference) > width * 1.5]

    def reference_ticks(self) -> tuple[list[float], list[str]]:
        if self.EXACT is None:
            return [], []
        return [float(self.DRAW[self.EXACT]), float(self.DRAW[self.EXACT + 1])], ["1", "1"]
