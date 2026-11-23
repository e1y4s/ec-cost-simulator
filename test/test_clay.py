import pytest

from simulator.code.clay import CLAY

@pytest.fixture
def code():
    return CLAY(s=3, r=3, d=5)

def y_section(code: CLAY, fragment: int) -> int:
    return code._internal(fragment) // code.Q

def test_the_construction_is_rejected_outside_the_helper_range():
    with pytest.raises(ValueError):
        CLAY(s=3, r=3, d=3)
    with pytest.raises(ValueError):
        CLAY(s=3, r=3, d=6)

def test_the_helpers_fix_the_number_of_substripes(code):
    assert code.Q == code.HELPERS - code.S + 1
    assert code.D == code.Q ** code.SECTIONS
    assert (code.Q, code.D, code.SECTIONS, code.C) == (3, 9, 2, 27)

def test_a_shortened_code_inserts_virtual_fragments():
    shortened = CLAY(s=3, r=2, d=4)
    assert shortened.VIRTUAL == 1
    assert {shortened.symbol_cost({i}) for i in range(shortened.N)} == {16}

def test_no_loss_costs_nothing(code):
    assert code.symbol_cost(set()) == 0

@pytest.mark.parametrize("s,r,d", [(2, 2, 3), (3, 3, 5), (3, 3, 4), (3, 2, 4), (4, 3, 6), (16, 4, 19), (17, 10, 26)])
def test_one_loss_reaches_the_cut_set_bound(s, r, d):
    code = CLAY(s, r, d)
    for lost in range(code.N):
        assert code.symbol_cost({lost}) == d * code.D // code.Q

def test_article_example_twenty_sixteen_nineteen():
    code = CLAY(16, 4, 19)
    assert code.D == 1024
    assert code.normalized_cost({0}) == pytest.approx(0.297, abs=1e-3)

def test_the_y_sections_group_the_fragments_by_q(code):
    assert [y_section(code, i) for i in range(code.N)] == [0, 0, 0, 1, 1, 1]

def test_two_losses_in_one_y_section_stay_economical(code):
    assert code.symbol_cost({0, 1}) == 24
    assert code.symbol_cost({3, 4}) == 24
    assert code.symbol_cost({0, 1}) < code.C

def test_two_losses_in_distinct_y_sections_read_the_whole_stripe(code):
    assert code.symbol_cost({0, 3}) == code.C
    assert code.symbol_cost({2, 5}) == code.C

def test_a_y_section_holds_at_most_q_minus_one_losses(code):
    assert code.symbol_cost({0, 1, 2}) == code.C

def test_a_narrower_y_section_leaves_no_room_for_two_losses():
    narrow = CLAY(s=3, r=3, d=4)
    assert narrow.Q == 2
    for lost in ((0, 1), (0, 2), (4, 5)):
        assert narrow.symbol_cost(set(lost)) == narrow.C, lost

def test_a_wider_code_keeps_the_same_shape():
    wide = CLAY(s=4, r=3, d=6)
    assert (wide.Q, wide.D, wide.C) == (3, 27, 108)
    assert wide.symbol_cost({0}) == 54
    assert wide.symbol_cost({0, 1}) == 90
    assert wide.symbol_cost({0, 3}) == wide.C

def test_sequential_reads_depend_on_the_y_section(code):
    assert code.sequential_read_cost({0}) == 5
    assert code.sequential_read_cost({3}) == 15

def test_beyond_r_losses_is_undecodable(code):
    assert code.symbol_cost({0, 1, 2, 3, 4, 5}) is None
    assert code.sequential_read_cost({0, 1, 2, 3, 4, 5}) is None
    assert CLAY(2, 2, 3).symbol_cost({0, 1, 2}) is None

def test_the_average_cost_over_single_losses(code):
    assert code.avg_normalized_cost(1).AVG == pytest.approx(15 / 27)
