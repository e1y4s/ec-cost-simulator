import itertools

import pytest

from simulator.code.clay import CLAY
from simulator.code.design2 import DESIGN2
from simulator.code.hh import HH
from simulator.code.hhlrc import HHLRC
from simulator.code.lrc import LRC
from simulator.code.rs import RS
from simulator.code.code import Code, SymbolState

CODES = [RS(10, 4), RS(6, 3), HH(10, 4), HH(6, 3), LRC(10, 4, 1), LRC(10, 4, 3), HHLRC(10, 4, 1), HHLRC(10, 4, 3), HHLRC(6, 3, 2), DESIGN2(10, 4), DESIGN2(6, 3), CLAY(10, 4, 13), CLAY(10, 4, 11), CLAY(6, 3, 8)]
IDS = [f"{c.get_short_name()}-n{c.N}-s{c.S}-a{c.D}" for c in CODES]
LOSSES = (1, 2, 3)

def patterns(code: Code, count: int):
    return map(set, itertools.combinations(range(code.N), count))

def read_count(code: Code, inventory: list[list[SymbolState]]) -> int:
    return sum(1 for i in range(code.N) for z in range(code.D) if inventory[i][z] == SymbolState.READ)

@pytest.mark.parametrize("code", CODES, ids=IDS)
def test_no_loss_costs_nothing(code: Code):
    assert code.symbol_cost(set()) == 0
    assert code.sequential_read_cost(set()) == 0

@pytest.mark.parametrize("code", CODES, ids=IDS)
def test_a_single_loss_is_always_repairable(code: Code):
    for lost in patterns(code, 1):
        assert code.symbol_cost(lost) is not None, lost

@pytest.mark.parametrize("code", CODES, ids=IDS)
def test_more_losses_than_parities_is_undecodable(code: Code):
    lost = set(range(code.R + 1))
    assert code.symbol_cost(lost) is None

@pytest.mark.parametrize("code", CODES, ids=IDS)
def test_cost_never_exceeds_a_full_read(code: Code):
    for count in LOSSES:
        for lost in patterns(code, count):
            cost = code.symbol_cost(lost)
            if cost is None:
                continue
            assert 0 < cost <= code.C, (lost, cost)

@pytest.mark.parametrize("code", CODES, ids=IDS)
def test_sequential_cost_is_bounded_by_the_symbol_cost(code: Code):
    for count in LOSSES:
        for lost in patterns(code, count):
            cost = code.symbol_cost(lost)
            if cost is None:
                continue
            sequential = code.sequential_read_cost(lost)
            assert 1 <= sequential <= cost, (lost, sequential, cost)

@pytest.mark.parametrize("code", CODES, ids=IDS)
def test_the_inventory_marks_exactly_what_the_cost_charges(code: Code):
    for count in LOSSES:
        for lost in patterns(code, count):
            inventory = code._init_inventory(lost)
            cost = code.symbol_cost(lost, inventory)
            if cost is None:
                continue
            assert read_count(code, inventory) == cost, lost

@pytest.mark.parametrize("code", CODES, ids=IDS)
def test_a_repair_computes_every_lost_symbol(code: Code):
    for count in LOSSES:
        for lost in patterns(code, count):
            inventory = code._init_inventory(lost)
            if code.symbol_cost(lost, inventory) is None:
                continue
            for i in range(code.N):
                expected = SymbolState.COMPUTED if i in lost else None
                for z in range(code.D):
                    state = inventory[i][z]
                    if expected is None:
                        assert state in (SymbolState.NOT_READ, SymbolState.READ), (lost, i, z)
                    else:
                        assert state == expected, (lost, i, z)

@pytest.mark.parametrize("code", CODES, ids=IDS)
def test_an_instance_holds_no_scenario_state(code: Code):
    cases = [lost for count in LOSSES for lost in patterns(code, count)]
    forward = [(code.symbol_cost(lost), code.sequential_read_cost(lost)) for lost in cases]
    backward = [(code.symbol_cost(lost), code.sequential_read_cost(lost)) for lost in reversed(cases)]
    assert forward == list(reversed(backward))

@pytest.mark.parametrize("code", CODES, ids=IDS)
def test_repeated_calls_are_deterministic(code: Code):
    for count in LOSSES:
        for lost in patterns(code, count):
            first = (code.symbol_cost(lost), code.sequential_read_cost(lost))
            second = (code.symbol_cost(lost), code.sequential_read_cost(lost))
            assert first == second, lost

@pytest.mark.parametrize("code", CODES, ids=IDS)
def test_an_analytic_shortcut_agrees_with_the_inventory_route(code: Code):
    for count in LOSSES:
        for lost in patterns(code, count):
            inventory = code._init_inventory(lost)
            cost = code.symbol_cost(lost, inventory)
            if cost is None:
                assert code.sequential_read_cost(lost) is None, lost
                assert code.normalized_cost(lost) is None, lost
                continue
            assert code.sequential_read_cost(lost) == Code._sequential_cost(code, inventory), lost
            assert code.normalized_cost(lost) == pytest.approx(cost / code.D / code.S), lost

@pytest.mark.parametrize("code", CODES, ids=IDS)
def test_a_code_names_itself(code: Code):
    assert code.get_name() and code.get_name() == code.NAME
    assert code.get_short_name() and code.get_short_name() == code.SHORT_NAME

@pytest.mark.parametrize("code", CODES, ids=IDS)
def test_settings_describe_the_construction(code: Code):
    settings = code.get_settings()
    assert settings["n"] == code.N
    assert settings["s"] == code.S
    assert settings["r"] == code.R
    assert settings[r"$\rho$"] == pytest.approx(code.N / code.S)
