import numpy

from simulator.code.code import Code, SymbolState

class CLAY(Code):

    def __init__(self, s: int, r: int, d: int | None = None):
        n = s + r
        if d is None:
            d = n - 1
        if not (s < d <= n - 1):
            raise ValueError(f"invalid d={d}: need s < d <= n - 1 with s={s}, n={n}")
        self.Q: int = d - s + 1
        self.VIRTUAL: int = (-n) % self.Q
        self.SECTIONS: int = (n + self.VIRTUAL) // self.Q
        super().__init__("Clay", "CLAY", n, s, self.Q ** self.SECTIONS)
        self.R: int = r
        self.HELPERS: int = d
        self.DIGITS: list = [(numpy.arange(self.D) // self.Q ** (self.SECTIONS - 1 - y)) % self.Q for y in range(self.SECTIONS)]

    def get_settings(self) -> dict[str, float]:
        return {"n": self.N, "s": self.S, "r": self.R, "d": self.HELPERS, "q": self.Q, r"$\alpha$": self.D, r"$\rho$": self.P}

    def symbol_cost(self, lost_indexes: set[int], inventory: list[list[SymbolState]] | None = None) -> int | None:
        if inventory is None:
            inventory = self._init_inventory(lost_indexes)
        if not lost_indexes:
            return 0
        if not self._is_decodable(lost_indexes):
            return None
        helpers, layers = self._build_plan(lost_indexes)
        if helpers is None:
            return self._full_read_inventory(lost_indexes, inventory)
        for i in helpers:
            for z in numpy.nonzero(layers)[0]:
                inventory[i][int(z)] = SymbolState.READ
        self._complete(lost_indexes, inventory)
        return len(helpers) * int(layers.sum())

    def normalized_cost(self, lost_indexes: set[int]) -> float | None:
        cost = self._cost(lost_indexes)
        if cost is None:
            return None
        return cost / self.D / self.S

    def sequential_read_cost(self, lost_indexes: set[int]) -> int | None:
        if not lost_indexes:
            return 0
        if not self._is_decodable(lost_indexes):
            return None
        helpers, layers = self._build_plan(lost_indexes)
        if helpers is None:
            return self.S
        runs = int(numpy.count_nonzero(numpy.diff(layers.astype(numpy.int64)) == 1)) + int(layers[0])
        return len(helpers) * runs

    def _cost(self, lost_indexes: set[int]) -> int | None:
        if not lost_indexes:
            return 0
        if not self._is_decodable(lost_indexes):
            return None
        helpers, layers = self._build_plan(lost_indexes)
        if helpers is None:
            return self.C
        return len(helpers) * int(layers.sum())

    def _build_plan(self, lost_indexes: set[int]) -> tuple:
        lost = {self._internal(i) for i in lost_indexes}
        count = len(lost)
        internal_n = self.N + self.VIRTUAL
        failed_sections = {j // self.Q for j in lost}
        survivors = [j for j in range(internal_n) if j not in lost]
        if self.HELPERS == self.N - 1:
            if len(failed_sections) != 1 or count > self.Q - 1:
                return None, None
            helpers = set(survivors)
        else:
            if count > self.N - self.HELPERS:
                return None, None
            total = self.HELPERS + self.VIRTUAL
            helpers = {j for j in survivors if j // self.Q in failed_sections}
            if len(helpers) > total:
                return None, None
            for j in sorted(survivors, key=lambda survivor: (not self._is_virtual(survivor), survivor)):
                if len(helpers) >= total:
                    break
                helpers.add(j)
        layers = numpy.zeros(self.D, dtype=numpy.int64)
        for j in lost:
            layers += self.DIGITS[j // self.Q] == j % self.Q
        layers = layers > 0
        real_helpers = sorted(self._external(j) for j in helpers if not self._is_virtual(j))
        if len(real_helpers) * int(layers.sum()) > self.C:
            return None, None
        return real_helpers, layers

    def _internal(self, i: int) -> int:
        return i if i < self.S else i + self.VIRTUAL

    def _external(self, j: int) -> int:
        return j if j < self.S else j - self.VIRTUAL

    def _is_virtual(self, j: int) -> bool:
        return self.S <= j < self.S + self.VIRTUAL

    def _is_decodable(self, lost_indexes: set[int]) -> bool:
        return len(lost_indexes) <= self.R
