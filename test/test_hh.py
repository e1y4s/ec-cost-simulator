import pytest

from simulator.code.hh import HH

@pytest.fixture
def code():
    return HH(s=11, r=5)

def test_the_construction_is_rejected_without_a_piggybacked_parity():
    with pytest.raises(ValueError):
        HH(s=11, r=1)

def test_the_first_parity_carries_nothing_and_the_others_split_the_data(code):
    assert [sorted(code.GROUPS[i]) for i in sorted(code.PARITIES)] == [[], [0, 1], [2, 3, 4], [5, 6, 7], [8, 9, 10]]

def test_no_loss_costs_nothing(code):
    assert code.symbol_cost(set()) == 0

def test_one_data_loss_reads_the_stripe_plus_its_own_group(code):
    for parity in sorted(code.PARITIES):
        group = code.GROUPS[parity]
        for lost in group:
            assert code.symbol_cost({lost}) == code.S + len(group), (parity, lost)

def test_two_data_losses_in_distinct_groups_still_use_the_piggybacks(code):
    assert code.symbol_cost({0, 2}) == 19
    assert code.symbol_cost({2, 5}) == 19
    assert code.symbol_cost({0, 2}) < code.C

def test_two_data_losses_in_one_group_fall_back_on_a_full_read(code):
    assert code.symbol_cost({0, 1}) == code.C
    assert code.symbol_cost({2, 3}) == code.C
    assert code.symbol_cost({2, 3, 4}) == code.C

def test_losing_any_parity_falls_back_on_a_full_read(code):
    for parity in sorted(code.PARITIES):
        assert code.symbol_cost({parity}) == code.C, parity

def test_a_data_loss_alongside_a_parity_loss_falls_back_on_a_full_read(code):
    assert code.symbol_cost({0, 11}) == code.C
    assert code.symbol_cost({0, 12}) == code.C
    assert code.symbol_cost({2, 14}) == code.C

def test_three_data_losses_in_distinct_groups_fall_back_on_a_full_read(code):
    assert code.symbol_cost({0, 2, 5}) == code.C
    assert code.symbol_cost({2, 5, 8}) == code.C

def test_losses_up_to_r_are_decodable(code):
    assert code.symbol_cost({0, 1, 2, 3, 4}) == code.C
    assert code.symbol_cost({11, 12, 13, 14, 15}) == code.C

def test_beyond_r_losses_is_undecodable(code):
    assert code.symbol_cost({0, 1, 2, 3, 4, 5}) is None
    assert code.symbol_cost({0, 1, 11, 12, 13, 14}) is None

def test_a_single_piggyback_group_never_beats_a_full_read():
    code = HH(s=8, r=2)
    assert code.GROUPS[9] == set(range(8))
    for lost in ({0}, {3}, {7}):
        assert code.symbol_cost(set(lost)) == code.C, lost
        assert code.sequential_read_cost(set(lost)) == code.S, lost
