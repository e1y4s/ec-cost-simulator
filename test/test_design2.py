import pytest

from simulator.code.design2 import DESIGN2

@pytest.fixture
def code():
    return DESIGN2(s=10, r=4)

def test_the_construction_is_rejected_below_three_parities():
    with pytest.raises(ValueError):
        DESIGN2(s=10, r=2)

def test_the_partition_splits_the_data_into_r_minus_one_groups(code):
    assert len(code.PARTITION) == code.R - 1
    assert [sorted(g) for g in code.PARTITION] == [[0, 1, 2, 3], [4, 5, 6], [7, 8, 9]]
    assert set().union(*code.PARTITION) == set(range(code.S))

def test_the_number_of_substripes_follows_the_parities(code):
    assert code.D == 2 * code.R - 3
    assert DESIGN2(s=10, r=3).D == 3

def test_no_loss_costs_nothing(code):
    assert code.symbol_cost(set()) == 0

def test_one_data_loss_follows_the_formula_of_the_article(code):
    for group in code.PARTITION:
        expected = (code.R - 2) * code.S + (code.R - 1) * len(group)
        for lost in group:
            assert code.symbol_cost({lost}) == expected, (sorted(group), lost)

def test_a_larger_group_costs_more_than_a_smaller_one(code):
    assert code.symbol_cost({0}) == 32
    assert code.symbol_cost({5}) == 29

def test_article_example_three():
    assert DESIGN2(s=10, r=3).symbol_cost({0}) == 20

def test_the_smallest_code_repairs_one_data_fragment_economically():
    small = DESIGN2(s=4, r=3)
    assert small.C == 12
    for lost in range(small.S):
        assert small.symbol_cost({lost}) == 8

def test_losing_a_parity_reads_the_whole_stripe(code):
    for parity in range(code.S, code.N):
        assert code.symbol_cost({parity}) == code.C, parity

def test_two_losses_in_one_group_read_the_whole_stripe(code):
    assert code.symbol_cost({0, 1}) == code.C

def test_two_losses_in_distinct_groups_read_the_whole_stripe(code):
    assert code.symbol_cost({1, 5}) == code.C
    assert code.symbol_cost({7, 9}) == code.C

def test_a_data_loss_alongside_a_parity_loss_reads_the_whole_stripe(code):
    assert code.symbol_cost({0, 10}) == code.C

def test_every_multiple_loss_reads_the_whole_stripe():
    small = DESIGN2(s=4, r=3)
    for lost in ((0, 1), (0, 2), (4, 5), (0, 4), (0, 1, 2)):
        assert small.symbol_cost(set(lost)) == small.C, lost

def test_beyond_r_losses_is_undecodable(code):
    assert code.symbol_cost({0, 1, 2, 3, 4}) is None
