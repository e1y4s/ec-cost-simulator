import pytest

from simulator.code.hhlrc import HHLRC

CONFIGURATIONS = [(20, 13, 3), (21, 13, 2), (22, 13, 1)]
IDS = [f"s{s}-r{r}-l{l}" for s, r, l in CONFIGURATIONS]

@pytest.fixture
def code():
    return HHLRC(s=20, r=13, l=3)

@pytest.fixture(params=CONFIGURATIONS, ids=IDS)
def any_code(request):
    return HHLRC(*request.param)

def test_the_construction_is_rejected_without_a_piggybacked_parity():
    with pytest.raises(ValueError):
        HHLRC(s=20, r=1, l=1)

def test_the_construction_is_rejected_without_a_local_parity():
    with pytest.raises(ValueError):
        HHLRC(s=20, r=13, l=0)

def test_the_construction_is_rejected_when_localities_outnumber_the_parities():
    with pytest.raises(ValueError):
        HHLRC(s=20, r=3, l=4)

def test_the_first_parity_carries_nothing_and_the_others_split_the_data(code):
    assert code.GROUPS[20] == set()
    assert [sorted(code.GROUPS[i]) for i in range(21, 25)] == [[0], [1], [2], [3]]
    assert sorted(code.GROUPS[25]) == [4, 5]

def test_the_localities_split_the_global_parities(code):
    assert [sorted(code.GROUPS[i]) for i in sorted(code.LOCALITIES)] == [[20, 21, 22, 23, 24], [25, 26, 27, 28], [29, 30, 31, 32]]

def test_no_loss_costs_nothing(any_code):
    assert any_code.symbol_cost(set()) == 0

def test_one_data_loss_reads_the_stripe_plus_its_own_group(any_code):
    for parity in sorted(any_code.PARITIES):
        for lost in any_code.GROUPS[parity]:
            assert any_code.symbol_cost({lost}) == any_code.S + len(any_code.GROUPS[parity]), (parity, lost)

def test_one_parity_loss_is_repaired_inside_its_locality(any_code):
    for locality in sorted(any_code.LOCALITIES):
        for parity in any_code.GROUPS[locality]:
            assert any_code.symbol_cost({parity}) == 2 * len(any_code.GROUPS[locality]), (locality, parity)

def test_one_locality_loss_reads_only_the_parities_it_covers(any_code):
    for locality in sorted(any_code.LOCALITIES):
        assert any_code.symbol_cost({locality}) == 2 * len(any_code.GROUPS[locality]), locality

def test_two_parity_losses_in_distinct_localities_add_up(code):
    assert code.symbol_cost({20, 25}) == 2 * len(code.GROUPS[33]) + 2 * len(code.GROUPS[34])
    assert code.symbol_cost({25, 29}) == 2 * len(code.GROUPS[34]) + 2 * len(code.GROUPS[35])

def test_two_parity_losses_in_one_locality_fall_back_on_a_full_read(code):
    assert code.symbol_cost({20, 21}) == code.C
    assert code.symbol_cost({25, 26}) == code.C

def test_a_locality_and_one_of_its_own_parities_fall_back_on_a_full_read(code):
    assert code.symbol_cost({33, 20}) == code.C
    assert code.symbol_cost({34, 25}) == code.C

def test_a_locality_and_a_parity_it_does_not_cover_add_up(code):
    assert code.symbol_cost({34, 20}) == 2 * len(code.GROUPS[34]) + 2 * len(code.GROUPS[33])

def test_two_data_losses_in_distinct_groups_still_use_the_piggybacks(code):
    assert code.symbol_cost({0, 1}) == 23
    assert code.symbol_cost({0, 1}) < code.C

def test_two_data_losses_in_one_group_fall_back_on_a_full_read(code):
    assert code.symbol_cost({4, 5}) == code.C

def test_three_data_losses_in_distinct_groups_still_use_the_piggybacks(code):
    assert code.symbol_cost({0, 1, 2}) == 26
    assert code.symbol_cost({0, 1, 2}) < code.C

def test_a_data_loss_and_a_parity_loss_add_their_two_routes(code):
    assert code.symbol_cost({0, 22}) == 29

def test_losses_up_to_r_are_decodable(any_code):
    assert any_code.symbol_cost(set(range(any_code.R))) is not None

def test_beyond_r_losses_is_undecodable(any_code):
    assert any_code.symbol_cost(set(range(any_code.R + 1))) is None

def test_without_piggyback_every_repair_reads_the_whole_stripe():
    code = HHLRC(s=8, r=2, l=2)
    for lost in ({0}, {3}, {8}, {9}, {0, 3}):
        assert code.symbol_cost(set(lost)) == code.C, lost
