from simulator.code.code import Code, SymbolState

class RS(Code):

    def __init__(self, s: int, r: int):
        super().__init__("Reed–Solomon", "RS", s + r, s, 1)
        self.R: int = r

    def get_settings(self) -> dict[str, float]:
        return {"n": self.N, "s": self.S, "r": self.R, r"$\rho$": self.P}

    def symbol_cost(self, lost_indexes: set[int], inventory: list[list[SymbolState]] | None = None) -> int | None:
        if inventory is None:
            inventory = self._init_inventory(lost_indexes)
        if not lost_indexes:
            return 0
        if not self._is_decodable(lost_indexes):
            return None
        return self._full_read_inventory(lost_indexes, inventory)

    def _is_decodable(self, lost_indexes: set[int]) -> bool:
        return len(lost_indexes) <= self.R
