from simulator.schema.schema import Schema

class RS(Schema):

    def __init__(self, s: int, r: int):
        super().__init__("RS", s + r, s, 1)
        self.R: int = r

    def symbol_cost(self, lost_indexes: set[int]) -> int:
        if not self._has_lost(lost_indexes):
            return 0
        if not self._is_decodable(lost_indexes):
            return self.F
        return self.C

    def get_settings(self) -> dict[str, float]:
        return {"n": self.N, "s": self.S, "r": self.R, r"$\rho$": self.P}

    def _has_lost(self, lost_indexes: set[int]):
        return len(lost_indexes) != 0

    def _is_decodable(self, lost_indexes: set[int]):
        return len(lost_indexes) <= self.R
