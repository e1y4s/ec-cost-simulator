import pytest
from simulator.schema.hhlrc import HHLRC


@pytest.fixture
def hhlrc():
    """
    Crée une instance standard pour les tests.
    s=22 (données), r=13 (parités globales), l=1 (localités), w=1 (fenêtre piggyback)
    """
    return HHLRC(s=22, r=13, l=1, w=1)

"""
{------------------Données:-------------
 0: set(), 1: set(), 2: set(), 3: set(), 4: set(), 5: set(), 6: set(), 7: set(),
 8: set(), 9: set(), 10: set(), 11: set(), 12: set(), 13: set(), 14: set(), 15: set(), 16: set(), 17: set(), 18: set(), 19: set(), 20: set(), 21: set(),
 -----------------Vide:-------------
 22: set(),
 -------------------Parité:-------------
 23: {0}, 24: {1}, 25: {2, 3}, 26: {4, 5}, 27: {6, 7}, 28: {8, 9}, 29: {10, 11}, 30: {12, 13}, 31: {14, 15}, 32: {16, 17}, 33: {18, 19}, 34: {20, 21},
 ------------------Localité:-------------
 35: {32, 33, 34, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31}
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

    losses = set(range(hhlrc.R))
    assert hhlrc.symbol_cost(losses) != -1
    assert hhlrc.symbol_cost(losses)== hhlrc.C

# --- TESTS DE PERFORMANCE (hhLRC vs Reed-Solomon) ---

@pytest.mark.parametrize("symbol_index", [0,1])
def test_unePanne_Donnees_Efficacite(hhlrc, symbol_index):
    """Vérifie qu'une seule perte de donnée est réparée à un coût optimisé."""

    cost = hhlrc.symbol_cost({symbol_index})

    assert cost != -1
    assert cost == 23

@pytest.mark.parametrize("symbol_index", [2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21])
def test_unePanne_Donnees_Efficacite2(hhlrc, symbol_index):
    """Vérifie qu'une seule perte de donnée est réparée à un coût optimisé."""

    cost = hhlrc.symbol_cost({symbol_index})

    assert cost != -1
    assert cost == 24

def test_deuxPannes_Donnees_Efficacite(hhlrc):
    """Vérifie que deux pertes de données sont réparées à un coût optimisé."""
    symbol_index={0,1}
    cost = hhlrc.symbol_cost(symbol_index)

    assert cost != -1
    assert cost == 26

def test_deuxPannes_Donnees_Sur_Parite_RS_Global(hhlrc):
    """
    Vérifie le cas où la réparation locale échoue/n'est pas optimale et doit
    revenir au décodage RS global (coût = v).
    Symboles {2, 3} sont couverts par P25. Si les deux sont perdus, la parité locale
    ne peut pas les réparer, il faut le RS global.
    """
    symbol_indices = {2, 3}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == hhlrc.C

def test_TroisPannes_Donnees_Efficacite(hhlrc):
    """Vérifie que trois pertes de données sont réparées à un coût optimisé."""
    symbol_index={0,1,2}
    cost = hhlrc.symbol_cost(symbol_index)

    assert cost != -1
    assert cost == 30

@pytest.mark.parametrize("symbol_index", [{1, 2, 3}])
def test_TroisPannes_Donnees_RS(hhlrc, symbol_index):
    """
    Vérifie que 2 pertes de données sur une même parité est n'est reparable
    qu'avec un RS complet
    """
    cost = hhlrc.symbol_cost(symbol_index)

    assert cost != -1

    assert cost == hhlrc.C

# ----------- TESTS SUR PARITÉ ------------------

@pytest.mark.parametrize("symbol_index", [23,24,25,26,27,28,29,30,31,32,33,34])
def test_unePanne_Parite_Efficacite(hhlrc, symbol_index):
    """Vérifie qu'une seule parité est réparée à un faible coût."""

    cost = hhlrc.symbol_cost({symbol_index})

    assert cost != -1
    assert cost == hhlrc.R * 2

def test_deuxPannes_Parite_Voisines_RS_Global(hhlrc):

    symbol_indices = {23, 24}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == hhlrc.C

# ---------------- Tests localité --------------

def test_locality_reparation(hhlrc):
    """
    Vérifie que la perte du symbole de localité (indice 35) est égale
    au nombre de parité.
    """
    locality_index = hhlrc.S + hhlrc.R # Indice 35
    cost = hhlrc.symbol_cost({locality_index})

    assert cost != -1
    assert cost == hhlrc.R * 2

# ----------- Tests combinés (Données, Parité, Localité) ------------

def test_unePanne_Parite_unePanne_Localite(hhlrc):
    """
    Cas 1: Perte d'une Parité Globales (25) et de la Localité (35).
    Doit être réparable en RS global .
    """
    symbol_indices = {25, 35}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == hhlrc.C

def test_unePanne_Parite_unePanne_Donnees(hhlrc):
    """
    Cas 2: Perte d'une Donnée (2) et de sa Parité associée (25).
    C'est un cas où le mécanisme Piggybacking est censé être le plus efficace.
    """
    symbol_indices = {2, 25}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == 44

def test_donnee_parite_localite_mixte_reparable(hhlrc):
    """
    Cas 3: Perte de 3 symboles mixtes (Donnée 0, Parité 23, Localité 35).
    Test la capacité de gérer des pertes sur les trois types de symboles.
    """
    symbol_indices = {0, 23, 35}
    cost = hhlrc.symbol_cost(symbol_indices)

    assert cost != -1
    assert cost == hhlrc.C