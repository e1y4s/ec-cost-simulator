import os
import numpy
from matplotlib import pyplot
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from simulator.code.code import Code, CodeResult
from simulator.graphic.axis import Axis, Scale, ScaleKind
from simulator.graphic.legend import Legend, format_number

AXIS_INK = "#52514e"
SCALE_NAMES = {ScaleKind.LINEAR: "échelle linéaire", ScaleKind.LOG: "échelle logarithmique"}

class HistogramEntry:

    def __init__(self, code: Code, result: CodeResult, color: str):
        self.CODE = code
        self.RESULT = result
        self.COLOR = color

class Histogram:

    def __init__(self, name: str, scales: list[Scale] | None = None, measure: str = "Coût", width: float = 9.5, height: float = 4.9):
        self.NAME: str = name
        self.SCALES: list[Scale] = scales or [Scale()]
        self.MEASURE: str = measure
        self.WIDTH: float = width
        self.HEIGHT: float = height
        self.ENTRIES: list[HistogramEntry] = []
        self.AXIS: Axis | None = None
        self.LEGEND: Legend | None = None
        self.FREQUENCIES: list[numpy.ndarray] = []
        self.BAR_WIDTH: float = 0.0
        self.LAYOUT: list[tuple[numpy.ndarray, numpy.ndarray]] = []
        self.LINES_STYLES: list[tuple[float, tuple[float, float]]] = []
        self.figure: Figure
        self.axis: Axes

    def add(self, entry: HistogramEntry) -> None:
        self.ENTRIES.append(entry)

    def draw(self) -> None:
        self.AXIS = Axis(self.SCALES, [c for e in self.ENTRIES for c in e.RESULT.DISTRIBUTION])
        self.LEGEND = Legend([e.CODE for e in self.ENTRIES])
        self.FREQUENCIES = [self.compute_frequencies(e.RESULT.DISTRIBUTION) for e in self.ENTRIES]
        self.BAR_WIDTH = self.compute_bar_width()
        self.LAYOUT = self.compute_layout()
        self.LINES_STYLES = self.compute_lines_styles()
        self.figure, self.axis = pyplot.subplots(figsize=(self.WIDTH, self.HEIGHT))
        self.setup_content()
        self.setup_axis()
        self.setup_figure()

    def compute_bar_width(self) -> float:
        widths = [w for i, w in enumerate(self.AXIS.widths()) if i != self.AXIS.EXACT]
        return (min(widths) if widths else 1.0) * 0.94

    def compute_layout(self) -> list[tuple[numpy.ndarray, numpy.ndarray]]:
        centres = self.AXIS.centres()
        count = len(self.ENTRIES)
        here = [numpy.flatnonzero([f[b] > 0 for f in self.FREQUENCIES]) for b in range(len(centres))]
        slot = self.BAR_WIDTH / count
        layout = []
        for index in range(count):
            xs = numpy.array(centres, dtype=float)
            widths = numpy.zeros(len(centres), dtype=float)
            for b, seats in enumerate(here):
                if index not in seats:
                    continue
                rank = int(numpy.flatnonzero(seats == index)[0])
                xs[b] = centres[b] + (rank - (len(seats) - 1) / 2.0) * slot
                widths[b] = slot * 0.9
            layout.append((xs, widths))
        return layout

    def compute_lines_styles(self) -> list[tuple[float, tuple[float, float]]]:
        same_cost_count: dict[float, list[HistogramEntry]] = {}
        for entry in self.ENTRIES:
            avg_cost = round(entry.RESULT.AVG, 2)
            same_cost_count[avg_cost] = same_cost_count.get(avg_cost, []) + [entry]
        styles: list[tuple[float, tuple[float, float]]] = []
        for entry in self.ENTRIES:
            avg_cost = round(entry.RESULT.AVG, 2)
            dot_size: float = 5
            dot_space: float = 2.5
            count = len(same_cost_count[avg_cost])
            dot_space_relative = dot_space + (count - 1) * (dot_size + dot_space)
            dot_offset_relative = (dot_size + dot_space) * same_cost_count[avg_cost].index(entry)
            styles.append((dot_offset_relative, (dot_size, dot_space_relative)))
        return styles

    def compute_frequencies(self, dist: dict[float, int]) -> numpy.ndarray:
        if not dist:
            return numpy.zeros(len(self.AXIS.BINS) - 1, dtype=float)
        x = numpy.array(list(dist.keys()), dtype=float)
        w = numpy.array(list(dist.values()), dtype=float)
        counts, _ = numpy.histogram(x, bins=self.AXIS.BINS, weights=w)
        total = counts.sum()
        frequencies = counts / total if total > 0 else counts.astype(float)
        return frequencies * 100.0

    def draw_cost_bar(self, entry: HistogramEntry) -> None:
        index = self.ENTRIES.index(entry)
        self.axis.bar(label=self.LEGEND.label(entry.CODE, entry.RESULT.AVG, entry.RESULT.MIN, entry.RESULT.MAX), x=self.LAYOUT[index][0], height=self.FREQUENCIES[index], width=self.LAYOUT[index][1], color=entry.COLOR, edgecolor="none", alpha=1, zorder=3)

    def draw_average_line(self, entry: HistogramEntry) -> None:
        self.axis.axvline(label="_nolegend_", x=self.AXIS.warp(entry.RESULT.AVG), color=entry.COLOR, linestyle=self.LINES_STYLES[self.ENTRIES.index(entry)], linewidth=1.3, alpha=0.55, zorder=1)

    def setup_axis(self) -> None:
        ticks = [t for t in self.AXIS.bounds() if self.AXIS.EXACT is None or not numpy.isclose(t, self.AXIS.BINS[self.AXIS.EXACT])]
        extra_positions, extra_labels = self.AXIS.reference_ticks()
        every = [self.AXIS.warp(float(t)) for t in ticks] + extra_positions
        names = [f"{t:g}" for t in ticks] + extra_labels
        order = numpy.argsort(every)
        self.axis.set_xticks([every[i] for i in order], [names[i] for i in order], fontsize=8.5)
        self.axis.set_xlim(float(self.AXIS.DRAW[0]), float(self.AXIS.DRAW[-1]))
        self.axis.set_xlabel(self.MEASURE, fontsize=9.5, labelpad=8)
        self.axis.set_ylabel("Fréquence (%)", fontsize=9.5)
        self.axis.set_ylim(0.0, 122.0)
        y_ticks = numpy.arange(0.0, 100.0 + 10.0, 10.0)
        self.axis.set_yticks(y_ticks, [f"{format_number(x)}" for x in y_ticks], fontsize=8.5)
        handles, labels = self.axis.get_legend_handles_labels()
        legend = self.figure.legend(handles, labels, title=f"{self.LEGEND.describe(self.LEGEND.common_settings())} pour tous les codes", loc="lower center", bbox_to_anchor=(0.5, 0.025), ncol=2, frameon=False, fontsize=7.5, handlelength=1.2, columnspacing=1.6)
        legend.get_title().set_fontsize(8.5)
        self.axis.tick_params(axis="x", which="major", length=4, width=0.9, color=AXIS_INK, pad=5)
        self.annotate_scales()
        self.axis.grid(axis="x", linestyle="--", zorder=0, linewidth=0.5)
        self.axis.grid(axis="y", linestyle="--", zorder=0, linewidth=0.5)
        self.axis.set_axisbelow(True)

    def annotate_scales(self) -> None:
        runs = self.AXIS.runs()
        if len(runs) < 2:
            return
        for first, stop, kind in runs:
            left, right = float(self.AXIS.DRAW[first]), float(self.AXIS.DRAW[stop])
            if first:
                self.axis.axvline(left, color=AXIS_INK, linewidth=1.0, linestyle=(0, (2, 3)), zorder=2)
            self.axis.annotate(SCALE_NAMES[kind], ((left + right) / 2.0, 1.0), xycoords=("data", "axes fraction"), xytext=(0, -12), textcoords="offset points", ha="center", fontsize=7.5, color=AXIS_INK)

    def setup_figure(self) -> None:
        self.figure.subplots_adjust(left=0.075, right=0.985, top=0.955, bottom=0.35)

    def setup_content(self) -> None:
        for entry in self.ENTRIES:
            self.draw_cost_bar(entry)
            self.draw_average_line(entry)

    def save(self) -> None:
        self.draw()
        graph_directory = os.path.join(os.getcwd(), "graphs")
        os.makedirs(graph_directory, exist_ok=True)
        self.figure.savefig(os.path.join(graph_directory, f"{self.NAME}.png"), dpi=220)
        pyplot.close(self.figure)
