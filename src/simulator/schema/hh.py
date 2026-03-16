from simulator.schema.schema import Schema

class HH(Schema):

    def __init__(self, s: int, r: int, w: int = 1):
        super().__init__("HH", s + r, s, 2)
        self.R: int = r
        self.W: int = w # number of unpiggybacked parities
        self.GROUPS: dict[int, set[int]] = self._build_groups()

    def symbol_cost(self, lost_indexes: set[int]) -> int:
        if not self._has_lost(lost_indexes):
            return 0
        if not self._is_decodable(lost_indexes):
            return self.F
        if not self._is_depiggybackable(lost_indexes):
            return self.C
        b_cost = self._decode_b_cost(lost_indexes)
        a_cost = self._decode_a_cost(lost_indexes)
        cost = min(b_cost + a_cost, self.C)
        return cost

    def get_settings(self) -> dict[str, float]:
        return {"n": self.N, "s": self.S, "r": self.R, r"$\rho$": self.P}

    def _build_groups(self) -> dict[int, set[int]]:
        slots: int = self.R - self.W
        excluded_slots: int = self.S + self.W
        if slots < 1:
            return {i: set() for i in range(self.N)}
        base_size, remainder = divmod(self.S, slots)
        block_sizes: list[int] = [0] * excluded_slots # data and first parity are not piggybacked
        block_sizes += [base_size] * (slots - remainder) # smallest parity piggyback groups
        block_sizes += [base_size + 1] * remainder # largest parity piggyback groups
        groups: dict[int, set[int]] = {}
        current: int = 0
        for i in range(self.N):
            size: int = block_sizes[i]
            groups[i] = set(range(current, current + size)) if size else set()
            current += size
        return groups

    def _decode_b_cost(self, lost_indexes: set[int]) -> int:
        cost: int = 0
        decoded_count: int = 0
        for i in range(0, self.N):
            if i in lost_indexes:
                continue
            if i < self.S or lost_indexes & self.GROUPS[i] == set():
                cost += len(self.GROUPS[i]) + 1
                decoded_count += 1
            if decoded_count == self.S:
                break
        return cost

    def _decode_a_cost(self, lost_indexes: set[int]) -> int:
        cost: int = 0
        for i in range(self.S, self.N):
            if self.GROUPS[i] & lost_indexes == set():
                continue
            cost += len(self.GROUPS[i])
        return cost

    def _has_lost(self, lost_indexes: set[int]) -> bool:
        return len(lost_indexes) != 0

    def _is_decodable(self, lost_indexes: set[int]) -> bool:
        # decodable if number of losses is at most R
        return len(lost_indexes) <= self.R

    def _is_depiggybackable(self, lost_indexes: set[int]) -> bool:
        available_symbols_count: int = len(set(range(self.S)) - lost_indexes)
        for i in range(self.S, self.N):
            if i in lost_indexes:
                return False
            losses_in_group = len(self.GROUPS[i] & lost_indexes)
            if losses_in_group > 1:
                return False
            elif losses_in_group == 0:
                available_symbols_count += 1
        return available_symbols_count >= self.S
