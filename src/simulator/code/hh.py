from simulator.code.code import Code, SymbolState

class HH(Code):

    SUBSTRIPE_A: int = 0
    SUBSTRIPE_B: int = 1

    def __init__(self, s: int, r: int):
        if r < 2:
            raise ValueError(f"invalid r={r}: one parity stays unpiggybacked, so r >= 2")
        super().__init__("Hitchhiker-XOR", "HH", s + r, s, 2)
        self.R: int = r
        self.PARITIES: frozenset[int] = frozenset(range(s, s + r))
        self.GROUPS: dict[int, set[int]] = self._build_groups()

    def get_settings(self) -> dict[str, float]:
        return {"n": self.N, "s": self.S, "r": self.R, r"$\rho$": self.P}

    def symbol_cost(self, lost_indexes: set[int], inventory: list[list[SymbolState]] | None = None) -> int | None:
        if inventory is None:
            inventory = self._init_inventory(lost_indexes)
        if not lost_indexes:
            return 0
        if not self._is_decodable(lost_indexes):
            return None
        if not self._has_piggyback():
            return self._full_read_inventory(lost_indexes, inventory)
        if not self._has_piggyback_route(lost_indexes):
            return self._full_read_inventory(lost_indexes, inventory)
        cost = self._decode_substripe_b_cost(lost_indexes, inventory)
        cost += self._decode_substripe_a_cost(lost_indexes, inventory)
        if cost > self.C:
            return self._full_read_inventory(lost_indexes, inventory)
        self._complete(lost_indexes, inventory)
        return cost

    def _build_groups(self) -> dict[int, set[int]]:
        slots = self.R - 1
        base, remainder = divmod(self.S, slots)
        sizes: list[int] = [0] * (self.S + 1)
        sizes += [base] * (slots - remainder)
        sizes += [base + 1] * remainder
        return self._groups_from_sizes(sizes)

    def _decode_substripe_b_cost(self, lost_indexes: set[int], inventory: list[list[SymbolState]]) -> int:
        cost = 0
        decoded = 0
        for i in range(self.N):
            if i in lost_indexes:
                continue
            if i < self.S or not self.GROUPS[i] & lost_indexes:
                cost += len(self.GROUPS[i]) + 1
                decoded += 1
                inventory[i][self.SUBSTRIPE_B] = SymbolState.READ
                for j in self.GROUPS[i]:
                    if inventory[j][self.SUBSTRIPE_A] == SymbolState.NOT_READ:
                        inventory[j][self.SUBSTRIPE_A] = SymbolState.READ
            if decoded == self.S:
                break
        return cost

    def _decode_substripe_a_cost(self, lost_indexes: set[int], inventory: list[list[SymbolState]]) -> int:
        cost = 0
        for i in self.PARITIES:
            if not self.GROUPS[i] & lost_indexes:
                continue
            cost += len(self.GROUPS[i])
            inventory[i][self.SUBSTRIPE_B] = SymbolState.READ
            for j in self.GROUPS[i]:
                if j not in lost_indexes and inventory[j][self.SUBSTRIPE_A] == SymbolState.NOT_READ:
                    inventory[j][self.SUBSTRIPE_A] = SymbolState.READ
        return cost

    def _is_decodable(self, lost_indexes: set[int]) -> bool:
        return len(lost_indexes) <= self.R

    def _has_piggyback(self) -> bool:
        return self.R - 1 >= 2

    def _has_piggyback_route(self, lost_indexes: set[int]) -> bool:
        available = self.S - sum(1 for i in lost_indexes if i < self.S)
        for i in self.PARITIES:
            if i in lost_indexes:
                return False
            losses_in_group = len(self.GROUPS[i] & lost_indexes)
            if losses_in_group > 1:
                return False
            if losses_in_group == 0:
                available += 1
        return available >= self.S
