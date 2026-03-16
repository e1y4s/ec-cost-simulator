from simulator.schema.schema import Schema

class HHLRC(Schema):

    def __init__(self, s: int, r: int, l: int, w: int = 1):
        super().__init__("HHLRC", s + r + l, s, 2)
        self.R = r
        self.W = w
        self.L = l  # nombre de localités
        self.__pbx = self.__get_pbx()

    def symbol_cost(self, lost_indexes: set[int]) -> int:
        tx = set(lost_indexes)
        dejaLu=set()
        cConstructionParity = 0
        cConstructionlocality=0
        if self.__is_undecodable(tx):
            return self.F
        if self.__has_locality_lost(tx) :
            lost_localities = tx.intersection(set(range(self.S + self.R, self.S + self.R + self.L)))
            lost_parities = tx.intersection(set(range(self.S, self.S + self.R)))
            for i in range(self.S+self.R, self.S+self.R+self.L):
                if len(lost_localities & {i}) != 0:
                    if len(lost_parities & self.__pbx[i]) >= 1:
                        # Si une parité perdue dans une localité, on ne peut pas reconstruire
                        return self.C
                    elif i in lost_localities:
                        cConstructionlocality += len(self.__pbx[i]) * 2
                        dejaLu.update(self.__pbx[i])
            tx.difference_update(lost_localities) #enlever toutes les localités perdues de tx qui ont déjà été reconstruites
            if len(tx)==0: #cas où il n'y a pas de symboles perdus(si on avait uniquement des localités perdues)
                return self.C if cConstructionlocality > self.C else cConstructionlocality
        if self.__has_no_pb():
            return self.C
        if self.__has_parity_lost(tx):
            lost_parities = tx.intersection(set(range(self.S, self.S + self.R)))
            # Chercher si dans une localité il y a une parité perdue
            for i in range(self.S + self.R, self.S + self.R + self.L):
                if len(lost_parities & self.__pbx[i]) == 1:
                    # Ajouter le coût de reconstruction pour cette localité
                    cConstructionParity +=  len(self.__pbx[i]) * 2
                    dejaLu.update(self.__pbx[i])
                elif len(lost_parities & self.__pbx[i]) > 1:
                    # Si plusieurs parités perdues dans une localité, on ne peut pas reconstruire
                    return self.C
            tx.difference_update(lost_parities) #enlever toutes les parités perdues de tx qui ont déjà été reconstruites
            if len(tx)==0: #cas où il n'y a pas de symboles perdus(si on a uniquement des parités perdues)
                return self.C if cConstructionlocality + cConstructionParity > self.C else cConstructionlocality + cConstructionParity
        c = self.__pb_decode_cost(tx, dejaLu) + cConstructionParity + cConstructionlocality
        return self.C if c == self.F or c > self.C else c

    def get_settings(self) -> dict[str, float]:
        return {"n": self.N, "s": self.S, "r": self.R, "l": self.L, r"$\rho$": self.P}

    def __get_pbx(self):
        # Distribution pour les parités normales
        r_p = self.R - self.W
        base, rem = divmod(self.S, r_p)
        # Distribution pour les localités
        baseL, remL = divmod(self.R, self.L)
        # Construction du tableau des tailles
        pbx_size = [0] * (self.S + 1) + [base] * (r_p - rem) + [base + 1] * rem
        if len(pbx_size) < self.N:
            pbx_size += [0] * (self.N - len(pbx_size))
        pbx_size += [baseL] * (self.L - remL) + [baseL + 1] * remL
        pbx: dict[int, set[int]] = {}
        # Distribution des symboles
        for i in range(self.N): #modif ici
            if i < self.S:
                # Symboles de données
                pbx[i] = set()
            elif i < self.S + self.R:
                # Parités normales avec piggybacking
                begin = sum(pbx_size[0:i])
                end = begin + pbx_size[i]
                pbx[i] = set(range(begin, end))
            else:
                # Localités
                group_size = self.R // self.L           # taille moyenne des groupes
                extra = self.R % self.L                 # pour répartir le surplus
                index = self.S                         # début des parités normales
                for i in range(self.L):
                    size = group_size + (1 if i < extra else 0)
                    pbx[self.S + self.R + i] = set(range(index, index + size))
                    index += size
        return pbx

    def __rs_decode_b_cost(self, tx: set[int], dejaLu: set[int]):
        cost = self.S - len(tx)
        count = 0
        parities = sorted(range(self.S, self.S + self.R), key=lambda i: len(self.__pbx[i]))
        for ri in parities:
            piggybacked = self.__pbx[ri]
            if len(piggybacked & tx) != 0:
                continue
            cost += len(piggybacked) + (0 if ri in dejaLu else 1)
            count += 1
            if count == len(tx):
                return cost
        return self.F

    def __pb_decode_a_with_b_cost(self, tx: set[int], dejaLu: set[int]):
        cost = 0
        count = 0
        parities = sorted(range(self.S, self.S + self.R), key=lambda i: len(self.__pbx[i]))
        for ri in parities:
            piggybacked = self.__pbx[ri]
            if len(piggybacked & tx) != 1:
               continue
            cost += len(piggybacked) - (1 if ri in dejaLu else 0)
            count += 1
            if count == len(tx):
                return cost
        return self.F

    def __is_undecodable(self, tx: set[int]):
        return len(tx) > self.R

    def __has_no_pb(self):
        return self.R <= 1 or self.R - self.W < 2

    def __has_parity_lost(self, tx: set[int]):
        return len(set(range(self.S, self.S + self.R)) & tx) != 0

    def __has_locality_lost(self, tx: set[int]):
        return len(set(range(self.S + self.R , self.S + self.R + self.L)) & tx) != 0


    def __pb_decode_cost(self, tx: set[int], dejaLu: set[int]):
        rs_b_cost = self.__rs_decode_b_cost(tx, dejaLu)
        if rs_b_cost == self.F:
            return self.F
        pb_a_with_b = self.__pb_decode_a_with_b_cost(tx, dejaLu) #problem here on a self.F
        if pb_a_with_b == self.F:
            return self.F
        return rs_b_cost + pb_a_with_b
