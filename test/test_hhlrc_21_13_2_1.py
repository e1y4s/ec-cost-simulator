import pytest
from simulator.schema.hhlrc import HHLRC


@pytest.fixture
def hhlrc():
    """
    Crée une instance standard pour les tests.
    s(données), r (parités globales), l (localités), w=1 (fenêtre piggyback)
    """
    return HHLRC(s=21, r=13, l=2, w=1)

"""
{------------------Données:-------------
 {0: set(), 1: set(), 2: set(), 3: set(), 4: set(), 5: set(), 6: set(), 7: set(), 8: set(), 9: set(), 10: set(),
 11: set(), 12: set(), 13: set(), 14: set(), 15: set(), 16: set(), 17: set(), 18: set(), 19: set(), 20: set(),
 -----------------Vide:-------------
 21: set(),
 -------------------Parité:-------------
 22: {0}, 23: {1}, 24: {2}, 25: {3, 4}, 26: {5, 6}, 27: {8, 7}, 28: {9, 10}, 29: {11, 12}, 30: {13, 14}, 31: {16, 15}, 32: {17, 18}, 33: {19, 20},
 ------------------Localité:-------------
 34: {21, 22, 23, 24, 25, 26, 27}, 35: {32, 33, 28, 29, 30, 31}
}
"""

# ------------ TESTS SUR DONNÉES (Validité) --------


def test_undecodable_too_many_losses(hhlrc):
    """
    Vérifie que le système échoue correctement si on perd plus que 'r' symboles.
    Ici r=13. Perte de r + 1 = 14 symboles.
    """
    losses = set(range(hhlrc.R + 1))
    assert hhlrc.symbol_cost(losses) == -1

def test_decodable_with_max_losses(hhlrc):
    """Vérifie que le système n'échoue pas à la limite de r pertes."""

    # On perd r symboles (indices 0 à 12, soit 13 symboles)
    losses = set(range(hhlrc.R))
    assert hhlrc.symbol_cost(losses) != -1

# --- TESTS DE PERFORMANCE (hhLRC vs Reed-Solomon) ---

@pytest.mark.parametrize("symbol_index", [0,1,2])
def test_unePanne_Donnees_Efficacite(hhlrc, symbol_index):
    """Vérifie qu'une seule perte de donnée est réparée à un coût optimisé."""

    cost = hhlrc.symbol_cost({symbol_index})

    assert cost != -1
    assert cost == 22
@pytest.mark.parametrize("symbol_index", [3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20])
def test_unePanne_Donnees_Efficacite2(hhlrc, symbol_index):
    """Vérifie qu'une seule perte de donnée est réparée à un coût optimisé."""

    cost = hhlrc.symbol_cost({symbol_index})

    assert cost != -1
    assert cost == 23


def test_deuxPannes_Donnees_Efficacite(hhlrc):
    """Vérifie que deux pertes de données sont réparées à un coût optimisé."""
    symbol_index={0,1}
    cost = hhlrc.symbol_cost(symbol_index)

    assert cost != -1
    assert cost == 24

def test_deuxPannes_Donnees_Sur_Parite_RS_Global(hhlrc):
    """
    Vérifie le cas où la réparation locale échoue/n'est pas optimale et doit
    revenir au décodage RS global (coût = v).
    Symboles {2, 3} sont couverts par P25. Si les deux sont perdus, la parité locale
    ne peut pas les réparer, il faut le RS global.
    """
    symbol_indices = {3, 4}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == hhlrc.C

def test_TroisPannes_Donnees_Efficacite(hhlrc):
    """Vérifie que trois pertes de données sont réparées à un coût optimisé."""
    symbol_index={0,1,2}
    cost = hhlrc.symbol_cost(symbol_index)

    assert cost != -1
    assert cost == 28

# ----------- TESTS SUR PARITÉ ------------------

@pytest.mark.parametrize("symbol_index", [22,23,24,25,26,27])
def test_unePanne_Parite_Efficacite(hhlrc, symbol_index):
    """Vérifie qu'une seule parité est réparée à un faible coût."""

    cost = hhlrc.symbol_cost({symbol_index})

    assert cost != -1
    assert cost == 14

@pytest.mark.parametrize("symbol_index", [28,29,30,31,32,33])
def test_unePanne_Parite_Efficacite2(hhlrc, symbol_index):
    """Vérifie qu'une seule parité est réparée à un faible coût."""

    cost = hhlrc.symbol_cost({symbol_index})

    assert cost != -1
    assert cost == 12

def test_deuxPannes_Parite_Voisines_RS_Global(hhlrc):
    """
    Vérifie que la perte de deux parités proches (P23 et P24) force le RS global
    si elles sont sur la même localité.
    """
    symbol_indices = {23, 24}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == hhlrc.C

def test_deuxPannes_Parite_Localité_Differente(hhlrc):
    """
    Vérifie que la perte de deux parités (P23 et P29) sur des localités différentes
    est mieux que le RS complet.
    """
    symbol_indices = {23, 29}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == hhlrc.R * 2

def test_TroisPannes_Parite_Efficacite(hhlrc):
    """Vérifie que trois pertes de parités sont réparées à un coût optimisé."""
    symbol_index={1,2,3}
    cost = hhlrc.symbol_cost(symbol_index)

    assert cost != -1
    assert cost == 28

# ---------------- Tests localité --------------

def test_locality_reparation(hhlrc):
    locality_index = {34}
    cost = hhlrc.symbol_cost(locality_index)

    assert cost != -1
    assert cost == 14

def test_locality_reparation2(hhlrc):
    locality_index = {35}
    cost = hhlrc.symbol_cost(locality_index)

    assert cost != -1
    assert cost == 12

# ----------- Tests combinés (Données, Parité, Localité) ------------

def test_unePanne_Parite_unePanne_Localite(hhlrc):
    """
    Cas 1: Perte d'une Parité Globales (25) et de la Localité (35).
    Doit être réparable sans RS complet.
    """
    symbol_indices = {25, 35}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == hhlrc.R * 2

def test_unePanne_Parite_unePanne_Donnees(hhlrc):
    """
    Cas 2: Perte d'une Donnée (2) et de sa Parité associée (25).
    C'est un cas où le mécanisme Piggybacking est censé être plus efficace par rapport à HH.
    """
    symbol_indices = {2, 25}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == 34

def test_donnee_parite_localite_mixte_reparable(hhlrc):
    """
    Cas 3: Perte de 3 symboles mixtes (Donnée 0, Parité 23, Localité 35).
    Test la capacité de gérer des pertes sur les trois types de symboles.
    """
    symbol_indices = {0, 23, 35}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == 42

def test_donnee_parite_localite_mixte_reparable_RS(hhlrc):
    """
    Cas 3: Perte de 3 symboles mixtes (Donnée 0, Parité 23, Localité 34).
    Test la capacité de gérer des pertes sur les trois types de symboles
    qui sont liés.
    """
    symbol_indices = {0, 23, 34}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == hhlrc.C
