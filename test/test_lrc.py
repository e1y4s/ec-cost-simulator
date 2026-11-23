import pytest

from simulator.code.lrc import LRC

@pytest.fixture
def code():
    return LRC(s=8, r=3, l=4)

def test_the_construction_is_rejected_without_a_local_parity():
    with pytest.raises(ValueError):
        LRC(s=8, r=3, l=0)

def test_the_construction_is_rejected_when_localities_outnumber_the_fragments():
    with pytest.raises(ValueError):
        LRC(s=8, r=3, l=12)

def test_each_locality_covers_a_slice_of_the_data_and_global_parities(code):
    assert [sorted(code.GROUPS[i]) for i in sorted(code.LOCALITIES)] == [[0, 1], [2, 3, 4], [5, 6, 7], [8, 9, 10]]

def test_no_loss_costs_nothing(code):
    assert code.symbol_cost(set()) == 0

def test_one_loss_reads_its_locality_and_nothing_else(code):
    for locality in sorted(code.LOCALITIES):
        group = code.GROUPS[locality]
        for lost in group:
            assert code.symbol_cost({lost}) == len(group), (locality, lost)

def test_losing_a_local_parity_reads_its_own_group(code):
    for locality in sorted(code.LOCALITIES):
        assert code.symbol_cost({locality}) == len(code.GROUPS[locality]), locality

def test_losses_in_distinct_localities_add_up(code):
    assert code.symbol_cost({0, 2}) == len(code.GROUPS[11]) + len(code.GROUPS[12])
    assert code.symbol_cost({2, 5}) == len(code.GROUPS[12]) + len(code.GROUPS[13])
    assert code.symbol_cost({11, 2}) == len(code.GROUPS[11]) + len(code.GROUPS[12])
    assert code.symbol_cost({11, 12}) == len(code.GROUPS[11]) + len(code.GROUPS[12])

def test_two_losses_in_one_locality_fall_back_on_a_full_read(code):
    assert code.symbol_cost({0, 1}) == code.C
    assert code.symbol_cost({2, 3}) == code.C
    assert code.symbol_cost({5, 6}) == code.C

def test_a_local_parity_and_one_of_its_group_fall_back_on_a_full_read(code):
    assert code.symbol_cost({11, 0}) == code.C
    assert code.symbol_cost({12, 2}) == code.C

def test_one_loss_per_locality_stays_decodable_beyond_r(code):
    assert code.symbol_cost({0, 2, 5, 8}) == code.C
    assert code.symbol_cost({11, 12, 13, 14}) == code.C
    assert code.symbol_cost({11, 12, 5, 8}) == code.C

def test_two_losses_in_one_locality_beyond_r_is_undecodable(code):
    assert code.symbol_cost({0, 1, 2, 5}) is None
    assert code.symbol_cost({2, 5, 8, 9}) is None
    assert code.symbol_cost({11, 12, 5, 6}) is None

def test_three_losses_never_beat_a_full_read(code):
    for lost in ({0, 2, 5}, {11, 2, 5}, {11, 12, 13}, {2, 3, 12}, {8, 9, 14}):
        assert code.symbol_cost(set(lost)) == code.C, lost
