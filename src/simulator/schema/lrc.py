from simulator.schema.schema import Schema

class LRC(Schema):

    def __init__(self, s: int, r: int, l: int):
        super().__init__("LRC",s + r + l, s, 1)
        self.R: int = r
        self.L: int = l # number of local parities
        self.LOCAL_GROUPS: dict[int, set[int]] = self._build_local_groups()

    def symbol_cost(self, lost_indexes: set[int]) -> int:
        if not self._has_lost(lost_indexes):
            return 0
        if not self._is_decodable(lost_indexes):
            return self.F
        if not self._is_locally_decodable(lost_indexes):
            return self.C
        return min(self._decode_local_cost(lost_indexes), self.C)

    def get_settings(self) -> dict[str, float]:
        return {"n": self.N, "s": self.S, "r": self.R, "l": self.L, r"$\rho$": self.P}

    def _decode_local_cost(self, lost_indexes: set[int]) -> int:
        cost: int = 0
        for i in range(self.S + self.R, self.S + self.R + self.L):
            if i not in lost_indexes and len(self.LOCAL_GROUPS[i] & lost_indexes) == 0:
                continue
            cost += len(self.LOCAL_GROUPS[i])
        return cost

    def _build_local_groups(self) -> dict[int, set[int]]:
        if self.L < 1:
            return {i: set() for i in range(self.N)}
        base_size, remainder = divmod(self.S + self.R, self.L)
        block_sizes: list[int] = [0] * (self.S + self.R) # data and global parities are not local
        block_sizes += [base_size] * (self.L - remainder) # smallest local groups
        block_sizes += [base_size + 1] * remainder # largest local groups
        groups: dict[int, set[int]] = {}
        current: int = 0
        for i in range(self.N):
            size: int = block_sizes[i]
            groups[i] = set(range(current, current + size)) if size else set()
            current += size
        return groups

    def _has_lost(self, lost_indexes: set[int]):
        return len(lost_indexes) != 0

    def _is_decodable(self, lost_indexes: set[int]):
        # decodable if number of losses is at most R, or if losses are in different groups
        if len(lost_indexes) > self.R:
            for i in range(self.S + self.R, self.S + self.R + self.L):
                lost_in_group = 0
                lost_in_group += len(self.LOCAL_GROUPS[i] & lost_indexes)
                lost_in_group += 1 if i in lost_indexes else 0
                if lost_in_group > 1:
                    return False
        return True

    def _is_locally_decodable(self, lost_indexes: set[int]):
        # locally decodable if no group has more than 1 loss
        for i in range(self.S + self.R, self.S + self.R + self.L):
            lost_in_group = 0
            lost_in_group += len(self.LOCAL_GROUPS[i] & lost_indexes)
            lost_in_group += 1 if i in lost_indexes else 0
            if lost_in_group > 1:
                return False
        return True
