import pytest
from simulator.schema.hh import HH


@pytest.fixture
def hh():
    # s     : {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
    # r     : {11, 12, 13, 14, 15}
    # 0-10  : {}
    # 11    : {}
    # 12    : {0, 1}
    # 13    : {2, 3, 4}
    # 14    : {5, 6, 7}
    # 15    : {8, 9, 10}
    return HH(s=11, r=5)

def test_no_loss(hh):
    assert hh.symbol_cost({}) == 0

def test_one_parity_loss(hh):
    assert hh.symbol_cost({11}) == 22
    assert hh.symbol_cost({12}) == 22
    assert hh.symbol_cost({13}) == 22

def test_two_parity_losses(hh):
    assert hh.symbol_cost({11, 12}) == 22
    assert hh.symbol_cost({11, 13}) == 22
    assert hh.symbol_cost({12, 13}) == 22
    assert hh.symbol_cost({13, 14}) == 22

def test_one_data_loss(hh):
    assert hh.symbol_cost({0}) == 13
    assert hh.symbol_cost({2}) == 14
    assert hh.symbol_cost({5}) == 14
    assert hh.symbol_cost({8}) == 14

def test_one_data_and_one_parity_loss_uncorrelated(hh):
    assert hh.symbol_cost({0, 11}) == 22
    assert hh.symbol_cost({0, 13}) == 22
    assert hh.symbol_cost({2, 11}) == 22
    assert hh.symbol_cost({2, 12}) == 22
    assert hh.symbol_cost({2, 14}) == 22

def test_two_data_losses_uncorrelated(hh):
    assert hh.symbol_cost({0, 2}) == 19
    assert hh.symbol_cost({2, 5}) == 19

def test_one_data_and_one_parity_loss_correlated(hh):
    assert hh.symbol_cost({0, 12}) == 22
    assert hh.symbol_cost({2, 13}) == 22

def test_two_data_losses_correlated(hh):
    assert hh.symbol_cost({0, 1}) == 22
    assert hh.symbol_cost({2, 3}) == 22

def test_two_data_and_one_parity_loss_uncorrelated(hh):
    assert hh.symbol_cost({0, 2, 11}) == 22
    assert hh.symbol_cost({0, 2, 14}) == 22
    assert hh.symbol_cost({2, 5, 11}) == 22
    assert hh.symbol_cost({2, 5, 12}) == 22
    assert hh.symbol_cost({2, 5, 15}) == 22

def test_three_data_losses_uncorrelated(hh):
    assert hh.symbol_cost({0, 2, 5}) == 22
    assert hh.symbol_cost({2, 5, 8}) == 22

def test_two_data_and_one_parity_loss_correlated(hh):
    assert hh.symbol_cost({0, 1, 12}) == 22
    assert hh.symbol_cost({2, 3, 13}) == 22

def test_three_data_losses_correlated(hh):
    assert hh.symbol_cost({2, 3, 4}) == 22

def test_max_arbitrary_losses(hh):
    assert hh.symbol_cost({0, 1, 2, 3, 4}) == 22
    assert hh.symbol_cost({0, 1, 11, 12, 13}) == 22
    assert hh.symbol_cost({11, 12, 13, 14, 15}) == 22

def test_min_untolerable_losses(hh):
    assert hh.symbol_cost({0, 1, 2, 3, 4, 5}) == -1
    assert hh.symbol_cost({0, 1, 11, 12, 13, 14}) == -1
