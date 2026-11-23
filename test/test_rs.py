import pytest

from simulator.code.rs import RS

@pytest.fixture
def code():
    return RS(s=11, r=5)

def test_the_construction_is_rejected_without_a_parity():
    with pytest.raises(ValueError):
        RS(s=11, r=0)

def test_settings_describe_the_construction(code):
    assert code.get_settings()["n"] == 16
    assert code.N == 16 and code.S == 11 and code.R == 5
    assert code.D == 1 and code.C == 11

def test_no_loss_costs_nothing(code):
    assert code.symbol_cost(set()) == 0

def test_any_repair_reads_the_whole_stripe(code):
    for lost in ({0}, {5}, {11}, {15}, {0, 1}, {0, 11}, {11, 12}):
        assert code.symbol_cost(set(lost)) == code.C, lost

def test_the_cost_does_not_depend_on_what_was_lost(code):
    costs = {code.symbol_cost({i}) for i in range(code.N)}
    assert costs == {code.C}

def test_losses_up_to_r_are_decodable(code):
    assert code.symbol_cost(set(range(code.R))) == code.C

def test_beyond_r_losses_is_undecodable(code):
    assert code.symbol_cost(set(range(code.R + 1))) is None

def test_a_single_substripe_means_one_sequential_read_per_fragment(code):
    assert code.sequential_read_cost({0}) == code.S
