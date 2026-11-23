from simulator.code.code import Code, SymbolState

class LRC(Code):

    def __init__(self, s: int, r: int, l: int):
        if l < 1:
            raise ValueError(f"invalid l={l}: an LRC needs at least one local parity")
        if l > s + r:
            raise ValueError(f"invalid l={l}: local parities split the {s + r} other fragments, so l <= s + r")
        super().__init__("LRC", "LRC", s + r + l, s, 1)
        self.R: int = r
        self.L: int = l
        self.LOCALITIES: frozenset[int] = frozenset(range(s + r, s + r + l))
        self.GROUPS: dict[int, set[int]] = self._build_groups()

    def get_settings(self) -> dict[str, float]:
        return {"n": self.N, "s": self.S, "r": self.R, "l": self.L, r"$\rho$": self.P}

    def symbol_cost(self, lost_indexes: set[int], inventory: list[list[SymbolState]] | None = None) -> int | None:
        if inventory is None:
            inventory = self._init_inventory(lost_indexes)
        if not lost_indexes:
            return 0
        if not self._is_decodable(lost_indexes):
            return None
        if not self._has_local_route(lost_indexes):
            return self._full_read_inventory(lost_indexes, inventory)
        cost = self._decode_local_cost(lost_indexes, inventory)
        if cost > self.C:
            return self._full_read_inventory(lost_indexes, inventory)
        self._complete(lost_indexes, inventory)
        return cost

    def _build_groups(self) -> dict[int, set[int]]:
        base, remainder = divmod(self.S + self.R, self.L)
        sizes: list[int] = [0] * (self.S + self.R)
        sizes += [base] * (self.L - remainder)
        sizes += [base + 1] * remainder
        return self._groups_from_sizes(sizes)

    def _decode_local_cost(self, lost_indexes: set[int], inventory: list[list[SymbolState]]) -> int:
        cost = 0
        for i in self.LOCALITIES:
            if i not in lost_indexes and not self.GROUPS[i] & lost_indexes:
                continue
            if inventory[i][0] == SymbolState.NOT_READ:
                inventory[i][0] = SymbolState.READ
            for j in self.GROUPS[i]:
                if j not in lost_indexes and inventory[j][0] == SymbolState.NOT_READ:
                    inventory[j][0] = SymbolState.READ
            cost += len(self.GROUPS[i])
        return cost

    def _is_decodable(self, lost_indexes: set[int]) -> bool:
        if len(lost_indexes) <= self.R:
            return True
        return self._has_local_route(lost_indexes)

    def _has_local_route(self, lost_indexes: set[int]) -> bool:
        for i in self.LOCALITIES:
            lost_in_group = len(self.GROUPS[i] & lost_indexes) + (1 if i in lost_indexes else 0)
            if lost_in_group > 1:
                return False
        return True
