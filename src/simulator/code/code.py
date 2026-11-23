from itertools import combinations
from typing import Callable
from enum import Enum, auto

class SymbolState(Enum):

    NOT_READ = auto()
    READ = auto()
    LOST = auto()
    COMPUTED = auto()

class CodeResult:

    def __init__(self) -> None:
        self.AVG: float | None = None
        self.MIN: float | None = None
        self.MAX: float | None = None
        self.SUM: float = 0
        self.COUNT: int = 0
        self.FAILED: int = 0
        self.DISTRIBUTION: dict[float, int] = {}

    def __str__(self) -> str:
        return str(self.__dict__)

class Code:

    def __init__(self, name: str, short_name: str, n: int, s: int, d: int):
        if s < 1:
            raise ValueError(f"invalid s={s}: a code needs at least one data fragment")
        if d < 1:
            raise ValueError(f"invalid d={d}: a code needs at least one substripe")
        if n <= s:
            raise ValueError(f"invalid n={n}: a code needs at least one parity fragment, so n > s={s}")
        self.NAME: str = name
        self.SHORT_NAME: str = short_name
        self.N: int = n
        self.S: int = s
        self.D: int = d
        self.P: float = n / s
        self.C: int = s * d

    def get_name(self) -> str:
        return self.NAME

    def get_short_name(self) -> str:
        return self.SHORT_NAME

    def get_settings(self) -> dict[str, float]:
        raise NotImplementedError

    def symbol_cost(self, lost_indexes: set[int], inventory: list[list[SymbolState]] | None = None) -> int | None:
        raise NotImplementedError

    def normalized_cost(self, lost_indexes: set[int]) -> float | None:
        cost = self.symbol_cost(lost_indexes, self._init_inventory(lost_indexes))
        if cost is None:
            return None
        return cost / self.D / self.S

    def sequential_read_cost(self, lost_indexes: set[int]) -> int | None:
        inventory = self._init_inventory(lost_indexes)
        cost = self.symbol_cost(lost_indexes, inventory)
        if cost is None:
            return None
        return self._sequential_cost(inventory)

    def normalized_sequential_read_cost(self, lost_indexes: set[int]) -> float | None:
        cost = self.sequential_read_cost(lost_indexes)
        if cost is None:
            return None
        return cost / self.S

    def avg_cost(self, lost_count: int) -> CodeResult:
        return self._avg_cost(lost_count, self.symbol_cost)

    def avg_normalized_cost(self, lost_count: int) -> CodeResult:
        return self._avg_cost(lost_count, self.normalized_cost)

    def avg_sequential_read_cost(self, lost_count: int) -> CodeResult:
        return self._avg_cost(lost_count, self.sequential_read_cost)

    def avg_normalized_sequential_read_cost(self, lost_count: int) -> CodeResult:
        return self._avg_cost(lost_count, self.normalized_sequential_read_cost)

    def _avg_cost(self, lost_count: int, cost_func: Callable[[set[int]], float | None]) -> CodeResult:
        result: CodeResult = CodeResult()
        for lost_indexes in map(set, combinations(range(self.N), lost_count)):
            cost = cost_func(lost_indexes)
            if cost is None:
                result.FAILED += 1
                continue
            result.SUM += cost
            result.COUNT += 1
            result.DISTRIBUTION[cost] = result.DISTRIBUTION.get(cost, 0) + 1
            result.MAX = cost if result.MAX is None else max(result.MAX, cost)
            result.MIN = cost if result.MIN is None else min(result.MIN, cost)
        if result.COUNT > 0:
            result.AVG = result.SUM / result.COUNT
        return result

    def _groups_from_sizes(self, sizes: list[int]) -> dict[int, set[int]]:
        groups: dict[int, set[int]] = {}
        current = 0
        for i in range(self.N):
            size = sizes[i] if i < len(sizes) else 0
            groups[i] = set(range(current, current + size))
            current += size
        return groups

    def _init_inventory(self, lost_indexes: set[int]) -> list[list[SymbolState]]:
        inventory = [[SymbolState.NOT_READ] * self.D for _ in range(self.N)]
        for i in lost_indexes:
            for z in range(self.D):
                inventory[i][z] = SymbolState.LOST
        return inventory

    def _full_read_inventory(self, lost_indexes: set[int], inventory: list[list[SymbolState]]) -> int:
        for i in range(self.N):
            for z in range(self.D):
                inventory[i][z] = SymbolState.LOST if i in lost_indexes else SymbolState.NOT_READ
        decoded = 0
        for i in range(self.N):
            if i not in lost_indexes:
                for z in range(self.D):
                    inventory[i][z] = SymbolState.READ
                decoded += 1
            if decoded == self.S:
                break
        self._complete(lost_indexes, inventory)
        return self.C

    def _complete(self, lost_indexes: set[int], inventory: list[list[SymbolState]]) -> None:
        for i in lost_indexes:
            for z in range(self.D):
                if inventory[i][z] != SymbolState.READ:
                    inventory[i][z] = SymbolState.COMPUTED

    def _sequential_cost(self, inventory: list[list[SymbolState]]) -> int:
        cost = 0
        for i in range(self.N):
            read_zones = [z for z in range(self.D) if inventory[i][z] == SymbolState.READ]
            if not read_zones:
                continue
            cost += 1
            for k in range(1, len(read_zones)):
                if read_zones[k] != read_zones[k - 1] + 1:
                    cost += 1
        return cost
