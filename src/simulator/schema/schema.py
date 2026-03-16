from itertools import combinations
from typing import Callable

class SchemaResult:

    def __init__(self) -> None:
        self.avg_cost: float = 0
        self.cost_min: float = float('inf')
        self.cost_max: float = float('-inf')
        self.cost_sum: float = 0
        self.case_count: int = 0
        self.case_failed_count: int = 0
        self.cost_distribution: dict[float, int] = {}

    def __str__(self) -> str:
        return str(self.__dict__)

class Schema:

    def __init__(self, name:str, n: int, s: int = 0, d: int = 0):
        self.NAME: str = name
        self.N: int = n
        self.S: int = s
        self.P: float = n / s
        self.D: int = d # density (symbols per chunk)
        self.C: int = s * d # max cost (RS cost)
        self.F: int = -1 # cost for undecodable cases (failed cases)

    def get_name(self) -> str:
        return self.NAME

    def symbol_cost(self, lost_indexes: set[int]) -> int:
        raise NotImplementedError

    def get_settings(self) -> dict[str, float]:
        raise NotImplementedError

    def avg_cost(self, lost_count: int) -> SchemaResult:
        return self._avg_cost(lost_count, self.symbol_cost)

    def normalized_cost(self, lost_indexes: set[int]) -> float:
        cost = self.symbol_cost(lost_indexes)
        if cost == self.F:
            return self.F
        return cost / self.D / self.S

    def avg_normalized_cost(self, lost_count: int) -> SchemaResult:
        return self._avg_cost(lost_count, self.normalized_cost)

    def _avg_cost(self, lost_count: int, cost_func: Callable[[set[int]], float]) -> SchemaResult:
        result: SchemaResult = SchemaResult()
        for lost_indexes in map(set, combinations(range(self.N), lost_count)):
            cost = cost_func(lost_indexes)
            if cost == self.F:
                result.case_failed_count += 1
                continue
            result.cost_sum += cost
            result.case_count += 1
            result.cost_distribution[cost] = result.cost_distribution.get(cost, 0) + 1
            result.cost_max = max(result.cost_max, cost)
            result.cost_min = min(result.cost_min, cost)
        if result.case_count == 0:
            result.cost_min = 0
            result.cost_max = 0
        result.avg_cost = result.cost_sum / result.case_count if result.case_count > 0 else 0
        return result
