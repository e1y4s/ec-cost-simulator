from simulator.code.code import Code, SymbolState

class HHLRC(Code):

    SUBSTRIPE_A: int = 0
    SUBSTRIPE_B: int = 1

    def __init__(self, s: int, r: int, l: int):
        if r < 2:
            raise ValueError(f"invalid r={r}: one parity stays unpiggybacked, so r >= 2")
        if l < 1:
            raise ValueError(f"invalid l={l}: an HH-LRC needs at least one local parity")
        if l > r:
            raise ValueError(f"invalid l={l}: local parities split the {r} global ones, so l <= r")
        super().__init__("HH-LRC", "HHLRC", s + r + l, s, 2)
        self.R: int = r
        self.L: int = l
        self.PARITIES: frozenset[int] = frozenset(range(s, s + r))
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
        remaining = set(lost_indexes)
        already_read: set[int] = set()
        locality_cost = self._repair_localities(remaining, already_read, inventory)
        if locality_cost is None:
            return self._full_read_inventory(lost_indexes, inventory)
        if not remaining:
            self._complete(lost_indexes, inventory)
            return min(locality_cost, self.C)
        if not self._has_piggyback():
            return self._full_read_inventory(lost_indexes, inventory)
        parity_cost = self._repair_parities(remaining, already_read, inventory)
        if parity_cost is None:
            return self._full_read_inventory(lost_indexes, inventory)
        if not remaining:
            self._complete(lost_indexes, inventory)
            return min(locality_cost + parity_cost, self.C)
        cost = self._decode_piggyback_cost(remaining, already_read, inventory)
        if cost is None:
            return self._full_read_inventory(lost_indexes, inventory)
        cost += locality_cost + parity_cost
        if cost > self.C:
            return self._full_read_inventory(lost_indexes, inventory)
        self._complete(lost_indexes, inventory)
        return cost

    def _repair_localities(self, remaining: set[int], already_read: set[int], inventory: list[list[SymbolState]]) -> int | None:
        lost_localities = remaining & self.LOCALITIES
        if not lost_localities:
            return 0
        lost_parities = remaining & self.PARITIES
        cost = 0
        for i in sorted(lost_localities):
            if lost_parities & self.GROUPS[i]:
                return None
            cost += len(self.GROUPS[i]) * 2
            already_read.update(self.GROUPS[i])
            self._read_whole(self.GROUPS[i], inventory)
            for z in range(self.D):
                inventory[i][z] = SymbolState.COMPUTED
        remaining.difference_update(lost_localities)
        return cost

    def _repair_parities(self, remaining: set[int], already_read: set[int], inventory: list[list[SymbolState]]) -> int | None:
        lost_parities = remaining & self.PARITIES
        if not lost_parities:
            return 0
        cost = 0
        for i in sorted(self.LOCALITIES):
            losses_in_group = len(lost_parities & self.GROUPS[i])
            if losses_in_group > 1:
                return None
            if losses_in_group == 1:
                cost += len(self.GROUPS[i]) * 2
                already_read.update(self.GROUPS[i])
                for z in range(self.D):
                    inventory[i][z] = SymbolState.READ
                self._read_whole(self.GROUPS[i], inventory)
        remaining.difference_update(lost_parities)
        return cost

    def _read_whole(self, fragments: set[int], inventory: list[list[SymbolState]]) -> None:
        for j in fragments:
            for z in range(self.D):
                if inventory[j][z] == SymbolState.NOT_READ:
                    inventory[j][z] = SymbolState.READ

    def _build_groups(self) -> dict[int, set[int]]:
        slots = self.R - 1
        base, remainder = divmod(self.S, slots)
        sizes: list[int] = [0] * (self.S + 1)
        sizes += [base] * (slots - remainder)
        sizes += [base + 1] * remainder
        groups = self._groups_from_sizes(sizes)
        base, remainder = divmod(self.R, self.L)
        current = self.S
        for i in range(self.L):
            size = base + (1 if i < remainder else 0)
            groups[self.S + self.R + i] = set(range(current, current + size))
            current += size
        return groups

    def _by_group_size(self) -> list[int]:
        return sorted(range(self.S, self.S + self.R), key=lambda parity: len(self.GROUPS[parity]))

    def _decode_piggyback_cost(self, remaining: set[int], already_read: set[int], inventory: list[list[SymbolState]]) -> int | None:
        b_cost = self._decode_substripe_b_cost(remaining, already_read, inventory)
        if b_cost is None:
            return None
        a_cost = self._decode_substripe_a_cost(remaining, already_read, inventory)
        if a_cost is None:
            return None
        return b_cost + a_cost

    def _decode_substripe_b_cost(self, remaining: set[int], already_read: set[int], inventory: list[list[SymbolState]]) -> int | None:
        cost = self.S - len(remaining)
        decoded = 0
        for i in range(self.S):
            if i not in remaining and inventory[i][self.SUBSTRIPE_B] == SymbolState.NOT_READ:
                inventory[i][self.SUBSTRIPE_B] = SymbolState.READ
        for i in self._by_group_size():
            group = self.GROUPS[i]
            if group & remaining:
                continue
            if inventory[i][self.SUBSTRIPE_B] == SymbolState.NOT_READ:
                inventory[i][self.SUBSTRIPE_B] = SymbolState.READ
            for j in group:
                if inventory[j][self.SUBSTRIPE_A] == SymbolState.NOT_READ:
                    inventory[j][self.SUBSTRIPE_A] = SymbolState.READ
            cost += len(group) + (0 if i in already_read else 1)
            decoded += 1
            if decoded == len(remaining):
                return cost
        return None

    def _decode_substripe_a_cost(self, remaining: set[int], already_read: set[int], inventory: list[list[SymbolState]]) -> int | None:
        cost = 0
        decoded = 0
        for i in self._by_group_size():
            group = self.GROUPS[i]
            if len(group & remaining) != 1:
                continue
            if inventory[i][self.SUBSTRIPE_B] == SymbolState.NOT_READ:
                inventory[i][self.SUBSTRIPE_B] = SymbolState.READ
            for j in group:
                if j not in remaining and inventory[j][self.SUBSTRIPE_A] == SymbolState.NOT_READ:
                    inventory[j][self.SUBSTRIPE_A] = SymbolState.READ
            cost += len(group) - (1 if i in already_read else 0)
            decoded += 1
            if decoded == len(remaining):
                return cost
        return None

    def _is_decodable(self, lost_indexes: set[int]) -> bool:
        return len(lost_indexes) <= self.R

    def _has_piggyback(self) -> bool:
        return self.R - 1 >= 2
