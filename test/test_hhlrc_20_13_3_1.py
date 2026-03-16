import pytest
from simulator.schema.hhlrc import HHLRC


@pytest.fixture
def hhlrc():
    """
    Crée une instance standard pour les tests.
    s (données), r (parités globales), l (localités), w (fenêtre piggyback)
    """
    return HHLRC(s=20, r=13, l=3, w=1)

"""
{------------------Données:-------------
 {0: set(), 1: set(), 2: set(), 3: set(), 4: set(), 5: set(), 6: set(), 7: set(), 8: set(), 9: set(),
 10: set(), 11: set(), 12: set(), 13: set(), 14: set(), 15: set(), 16: set(), 17: set(), 18: set(), 19: set(),
 -----------------Vide:-------------
 20: set(),
 -------------------Parité:-------------
 21: {0}, 22: {1}, 23: {2}, 24: {3}, 25: {4, 5}, 26: {6, 7}, 27: {8, 9},
 28: {10, 11}, 29: {12, 13}, 30: {14, 15}, 31: {16, 17}, 32: {18, 19},
------------------Localité:-------------
 33: {20, 21, 22, 23, 24}, 34: {25, 26, 27, 28}, 35: {32, 29, 30, 31}
}
"""

# ------------ TESTS SUR DONNÉES (Validité) --------


def test_undecodable_too_many_losses(hhlrc):
    """
    Vérifie que le système échoue correctement si on perd plus que 'r' symboles.
    Ici r=13. Perte de r + 1 = 14 symboles.
    """
    losses = set(range(hhlrc.R + 1))
    assert hhlrc.symbol_cost(losses) == -1, f"On ne peut pas reconstruire après r + 1 symboles perdus (r={hhlrc.R})!"

def test_decodable_with_max_losses(hhlrc):
    """Vérifie que le système n'échoue pas à la limite de r pertes."""

    # On perd r symboles (indices 0 à 12, soit 13 symboles)
    losses = set(range(hhlrc.R))
    assert hhlrc.symbol_cost(losses) != -1

# --- TESTS DE PERFORMANCE (hhLRC vs Reed-Solomon) ---

@pytest.mark.parametrize("symbol_index", [0,1,2,3])
def test_unePanne_Donnees_Efficacite(hhlrc, symbol_index):
    """Vérifie qu'une seule perte de donnée est réparée à un coût optimisé."""

    cost = hhlrc.symbol_cost({symbol_index})

    assert cost != -1

    # Le coût doit être inférieur au volume total (RS)
    assert cost == 21

def test_deuxPannes_Donnees_Efficacite(hhlrc):
    """Vérifie que deux pertes de données sont réparées à un coût optimisé."""
    symbol_index={0,1}
    cost = hhlrc.symbol_cost(symbol_index)

    assert cost != -1
    assert cost == 23

def test_deuxPannes_Donnees_Sur_Parite_RS_Global(hhlrc):
    """
    Vérifie le cas où la réparation locale échoue/n'est pas optimale et doit
    revenir au décodage RS global (coût = v).
    Symboles {2, 3} sont couverts par P25. Si les deux sont perdus, la parité locale
    ne peut pas les réparer, il faut le RS global.
    """
    symbol_indices = {4, 5}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == hhlrc.C

def test_TroisPannes_Donnees_Efficacite(hhlrc):
    """Vérifie que trois pertes de données sont réparées à un coût optimisé."""
    symbol_index={0,1,2}
    cost = hhlrc.symbol_cost(symbol_index)

    assert cost != -1
    assert cost == 26

# ----------- TESTS SUR PARITÉ ------------------

@pytest.mark.parametrize("symbol_index", [22,23,24])
def test_unePanne_Parite_Efficacite(hhlrc, symbol_index):
    """Vérifie qu'une seule parité est réparée à un faible coût."""

    cost = hhlrc.symbol_cost({symbol_index})

    assert cost != -1
    assert cost == 10


def test_deuxPannes_Parite_Voisines_RS_Global(hhlrc):
    """
    Vérifie que la perte de deux parités proches (P23 et P24) force le RS complet
    si elles sont sur la même localité.
    (Les parités globales ne sont pas locales entre elles).
    """
    symbol_indices = {23, 24}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == hhlrc.C

def test_deuxPannes_Parite_Localité_Differente(hhlrc):
    """
    Vérifie que la perte de deux parités sur
    des localités différentes est réparée a un coût optimisé.
    """
    symbol_indices = {23, 29}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == 18

# ---------------- Tests localité --------------

def test_locality_reparation(hhlrc):
    """
    Vérifie que la reconstruction du symbole de localité (indice 33) est peu coûteuse.
    """
    locality_index = {33}
    cost = hhlrc.symbol_cost(locality_index)

    assert cost != -1
    assert cost == 10
def test_locality_reparation2(hhlrc):
    """
    Vérifie que la reconstruction du symbole de localité (indice 34) est peu coûteuse.
    """
    locality_index = {34}
    cost = hhlrc.symbol_cost(locality_index)

    assert cost != -1
    assert cost == 8
def test_locality_reparation3(hhlrc):
    """
    Vérifie que la reconstruction du symbole de localité (indice 35) est peu coûteuse.
    """
    locality_index = {35}
    cost = hhlrc.symbol_cost(locality_index)

    assert cost != -1
    assert cost == 8

# ----------- Tests combinés (Données, Parité, Localité) ------------

def test_unePanne_Parite_unePanne_Localite(hhlrc):
    """
    Cas 1: Perte d'une Parité Globales (25) et de la Localité (35).
    Doit être réparable sans RS comme ils ne sont pas sur la même localité.
    """
    symbol_indices = {25, 35}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == 16

def test_unePanne_Parite_unePanne_Donnees(hhlrc):
    """
    Cas 2: Perte d'une Donnée (2) et de sa Parité associée (25).
    """
    symbol_indices = {2, 25}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == 29

def test_donnee_parite_localite_mixte_reparable(hhlrc):
    """
    Cas 3: Perte de 3 symboles mixtes (Donnée 0, Parité 23, Localité 35).
    Test la capacité de gérer des pertes sur les trois types de symboles.
    """
    symbol_indices = {0, 23, 35}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == 37

def test_donnee_parite_localite_mixte_reparable_RS(hhlrc):
    """
    Cas 3: Perte de 3 symboles mixtes (Donnée 0, Parité 23, Localité 35).
    Test la capacité de gérer des pertes sur les trois types de symboles qui sont liés.
    """
    symbol_indices = {0, 23, 33} # 3 pertes
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == hhlrc.C
