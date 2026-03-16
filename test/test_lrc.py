import pytest
from simulator.schema.lrc import LRC


@pytest.fixture
def lrc():
    # s     : {0, 1, 2, 3, 4, 5, 6, 7}
    # r     : {8, 9, 10}
    # l     : {11, 12, 13, 14}
    # 0-7   : {}
    # 8-10  : {}
    # 11    : {0, 1}
    # 12    : {2, 3, 4}
    # 13    : {5, 6, 7}
    # 14    : {8, 9, 10}
    return LRC(s=8, r=3, l=4)

def test_no_loss(lrc):
    assert lrc.symbol_cost({}) == 0

def test_one_loss(lrc):
    assert lrc.symbol_cost({0}) == 2
    assert lrc.symbol_cost({11}) == 2
    assert lrc.symbol_cost({2}) == 3
    assert lrc.symbol_cost({12}) == 3

def test_two_losses_uncorrelated(lrc):
    assert lrc.symbol_cost({0, 2}) == 5
    assert lrc.symbol_cost({11, 2}) == 5
    assert lrc.symbol_cost({11, 12}) == 5
    assert lrc.symbol_cost({2, 5}) == 6
    assert lrc.symbol_cost({12, 5}) == 6
    assert lrc.symbol_cost({12, 13}) == 6

def test_two_losses_correlated(lrc):
    assert lrc.symbol_cost({0, 1}) == 8
    assert lrc.symbol_cost({0, 11}) == 8
    assert lrc.symbol_cost({2, 3}) == 8
    assert lrc.symbol_cost({2, 12}) == 8

def test_max_arbitrary_losses(lrc):
    assert lrc.symbol_cost({0, 2, 5}) == 8
    assert lrc.symbol_cost({11, 2, 5}) == 8
    assert lrc.symbol_cost({11, 12, 5}) == 8
    assert lrc.symbol_cost({11, 12, 13}) == 8
    assert lrc.symbol_cost({2, 5, 8}) == 8
    assert lrc.symbol_cost({12, 5, 8}) == 8
    assert lrc.symbol_cost({12, 13, 8}) == 8
    assert lrc.symbol_cost({12, 13, 14}) == 8
    assert lrc.symbol_cost({0, 1, 11}) == 8
    assert lrc.symbol_cost({2, 3, 12}) == 8
    assert lrc.symbol_cost({5, 6, 13}) == 8
    assert lrc.symbol_cost({8, 9, 14}) == 8

def test_max_tolerable_losses(lrc):
    assert lrc.symbol_cost({0, 2, 5, 8}) == 8
    assert lrc.symbol_cost({11, 12, 13, 14}) == 8
    assert lrc.symbol_cost({11, 12, 5, 8}) == 8
    assert lrc.symbol_cost({0, 12, 13, 8}) == 8

def test_min_untolerable_losses(lrc):
    assert lrc.symbol_cost({0, 1, 2, 5}) == -1
    assert lrc.symbol_cost({0, 2, 3, 5}) == -1
    assert lrc.symbol_cost({2, 5, 8, 9}) == -1
    assert lrc.symbol_cost({11, 12, 5, 6}) == -1
    assert lrc.symbol_cost({12, 13, 8, 9}) == -1