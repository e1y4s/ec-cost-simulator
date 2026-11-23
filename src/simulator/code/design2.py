from simulator.code.code import Code, SymbolState

class DESIGN2(Code):

    def __init__(self, s: int, r: int):
        if r < 3:
            raise ValueError(f"invalid r={r}: Design 2 requires r >= 3")
        super().__init__("Design 2", "DESIGN2", s + r, s, 2 * r - 3)
        self.R: int = r
        self.PARTITION: list[set[int]] = self._build_partition()

    def get_settings(self) -> dict[str, float]:
        return {"n": self.N, "s": self.S, "r": self.R, "m": self.D, r"$\rho$": self.P}

    def symbol_cost(self, lost_indexes: set[int], inventory: list[list[SymbolState]] | None = None) -> int | None:
        if inventory is None:
            inventory = self._init_inventory(lost_indexes)
        if not lost_indexes:
            return 0
        if not self._is_decodable(lost_indexes):
            return None
        if len(lost_indexes) == 1:
            lost = next(iter(lost_indexes))
            if lost < self.S:
                return self._repair_systematic_cost(lost, inventory)
        return self._full_read_inventory(lost_indexes, inventory)

    def _build_partition(self) -> list[set[int]]:
        count = self.R - 1
        base, remainder = divmod(self.S, count)
        partition: list[set[int]] = []
        current = 0
        for rank in range(count):
            size = base + 1 if rank < remainder else base
            partition.append(set(range(current, current + size)))
            current += size
        return partition

    def _piggyback_substripe(self, parity_rank: int, group_rank: int) -> int:
        group = group_rank + 1
        if group == parity_rank - 1:
            substripe = self.R - 1
        elif group <= parity_rank - 2:
            substripe = self.R + group - 1
        else:
            substripe = self.R + group - 2
        return substripe - 1

    def _read(self, node: int, substripe: int, inventory: list[list[SymbolState]]) -> int:
        if inventory[node][substripe] != SymbolState.NOT_READ:
            return 0
        inventory[node][substripe] = SymbolState.READ
        return 1

    def _repair_systematic_cost(self, lost: int, inventory: list[list[SymbolState]]) -> int:
        group_rank = next(rank for rank, members in enumerate(self.PARTITION) if lost in members)
        cost = 0
        for node in [i for i in range(self.S) if i != lost] + [self.S]:
            for z in range(self.R - 1, self.D):
                cost += self._read(node, z, inventory)
        for parity_rank in range(2, self.R + 1):
            cost += self._read(self.S + parity_rank - 1, self._piggyback_substripe(parity_rank, group_rank), inventory)
        for node in self.PARTITION[group_rank] - {lost}:
            for z in range(self.R - 1):
                cost += self._read(node, z, inventory)
        self._complete({lost}, inventory)
        return cost

    def _is_decodable(self, lost_indexes: set[int]) -> bool:
        return len(lost_indexes) <= self.R
