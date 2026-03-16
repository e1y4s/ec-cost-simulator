import os
import numpy
from matplotlib import pyplot
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from simulator.schema.schema import Schema, SchemaResult
from simulator.utils import format_number

class HistogramEntry:
    def __init__(self, schema: Schema, result: SchemaResult, color: str):
        self.SCHEMA = schema
        self.RESULT = result
        self.COLOR = color

class Histogram:
    def __init__(self, name, entries: list[HistogramEntry], losses: int, width: float = 14, height: float = 7, step: float = 0.05):
        self.NAME: str = name
        self.ENTRIES: list[HistogramEntry] = entries
        self.LOSSES: int = losses
        self.WIDTH: float = width
        self.HEIGHT: float = height
        self.STEP: float = step
        self.BAR_WIDTH: float = self.compute_bar_width()
        self.BINS: numpy.ndarray = self.compute_bins()
        self.BINS_POSITIONS: numpy.ndarray = self.compute_bins_positions()
        self.LINES_STYLES: list[tuple[float, tuple[float, float]]] = self.compute_lines_styles()
        self.figure: Figure
        self.axis: Axes
        self.figure, self.axis = pyplot.subplots(figsize=(self.WIDTH, self.HEIGHT))
        self.setup_content()
        self.setup_axis()
        self.setup_figure()

    def compute_bar_width(self) -> float:
        return (self.STEP / (len(self.ENTRIES))) * 0.90

    def compute_bins(self) -> numpy.ndarray:
        nb = int(round(1.0 / self.STEP))
        regular = numpy.linspace(0.0, 1.0, nb + 1)
        bins = numpy.append(regular, 1.0 + self.STEP)
        return bins

    def compute_bins_positions(self) -> numpy.ndarray:
        entries_count = len(self.ENTRIES)
        bin_centers = self.BINS[:-1] + self.STEP / 2
        offsets = (numpy.arange(entries_count) - (entries_count - 1) / 2.0) * (self.BAR_WIDTH)
        positions = bin_centers[numpy.newaxis, :] + offsets[:, numpy.newaxis]
        return positions

    def compute_lines_styles(self) -> list[tuple[float, tuple[float, float]]]:
        same_cost_count: dict[float, list[HistogramEntry]] = {}
        for entry in self.ENTRIES:
            avg_cost = round(entry.RESULT.avg_cost, 2)
            same_cost_count[avg_cost] = same_cost_count.get(avg_cost, []) + [entry]
        styles: list[tuple[float, tuple[float, float]]] = []
        for entry in self.ENTRIES:
            avg_cost = round(entry.RESULT.avg_cost, 2)
            dot_size: float = 5
            dot_space: float = 2.5
            count = len(same_cost_count[avg_cost])
            dot_space_relative = dot_space + (count - 1) * (dot_size + dot_space)
            dot_offset_relative = (dot_size + dot_space) * same_cost_count[avg_cost].index(entry)
            styles.append((dot_offset_relative, (dot_size, dot_space_relative)))
        return styles

    def compute_frequencies(self, dist: dict[float, int]) -> numpy.ndarray:
        if not dist:
            return numpy.zeros(len(self.BINS) - 1, dtype=float)
        x = numpy.array(list(dist.keys()), dtype=float)
        w = numpy.array(list(dist.values()), dtype=float)
        is_one = numpy.isclose(x, 1.0, atol=1e-12)
        x = x.copy()
        x[is_one] = 1.0 + (self.STEP / 2.0)
        counts, _ = numpy.histogram(x, bins=self.BINS, weights=w)
        s = counts.sum()
        frequencies = counts / s if s > 0 else counts.astype(float)
        return frequencies * 100.0

    def draw_cost_bar(self, entry: HistogramEntry) -> None:
        self.axis.bar(
            label=entry.SCHEMA.get_name(),
            x=self.BINS_POSITIONS[self.ENTRIES.index(entry)],
            height=self.compute_frequencies(entry.RESULT.cost_distribution),
            width=self.BAR_WIDTH,
            color=entry.COLOR,
            edgecolor="black",
            alpha=1,
        )

    def draw_average_line(self, entry: HistogramEntry) -> None:
        avg_cost = round(entry.RESULT.avg_cost * 100.0, 2)
        self.axis.axvline(
            label=f"{entry.SCHEMA.get_name()} coût moyen : {format_number(avg_cost)} %",
            x=entry.RESULT.avg_cost,
            color=entry.COLOR,
            linestyle=self.LINES_STYLES[self.ENTRIES.index(entry)],
            linewidth=2,
            alpha=1,
        )

    def _build_xtick_labels(self) -> list[str]:
        labels = [f"{format_number(x * 100.0)}" for x in self.BINS]
        labels[-1] = ""
        return labels

    def setup_axis(self) -> None:
        self.axis.set_xticks(self.BINS, self._build_xtick_labels(), rotation=45)
        self.axis.set_xlabel("Intervalle de coût normalisé (%)")
        self.axis.set_ylabel("Fréquence (%)")
        y_ticks = numpy.arange(0.0, 100.0 + 10.0, 10.0)
        self.axis.set_yticks(y_ticks, [f"{format_number(x)}" for x in y_ticks])
        legend = self.axis.legend(loc="upper left", frameon=True, shadow=True)
        for line in legend.get_lines():
            line.set_linewidth(2)
            line.set_linestyle("--")
        self.axis.grid(axis="x", linestyle="--", zorder=100, linewidth=0.5)
        self.axis.grid(axis="y", linestyle="--", zorder=100, linewidth=0.5)

    def setup_figure(self) -> None:
        title: str = ""
        for entry in self.ENTRIES:
            settings_str = ", ".join([f"{k}={format_number(v)}" for k, v in entry.SCHEMA.get_settings().items()])
            title += f"{entry.SCHEMA.get_name()}({settings_str})\n"
        self.axis.set_title(title)
        self.figure.tight_layout()

    def setup_content(self) -> None:
        for entry in self.ENTRIES:
            self.draw_cost_bar(entry)
            self.draw_average_line(entry)

    def save(self) -> None:
        graph_directory = os.path.join(os.getcwd(), "graphs")
        os.makedirs(graph_directory, exist_ok=True)
        self.figure.savefig(os.path.join(graph_directory, f"{self.NAME}.png"), dpi=150)
