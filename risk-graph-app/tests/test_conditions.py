from app.conditions import conditions_match, evaluate_condition
from app.models import Condition, Effect
from app.state import apply_effects


def test_conditions_evaluate_all_ops() -> None:
    vars_ = {"a": 3, "b": True, "c": "x"}
    assert evaluate_condition(Condition(var="a", op="greater_than", value=2), vars_)
    assert evaluate_condition(Condition(var="a", op="greater_or_equal", value=3), vars_)
    assert evaluate_condition(Condition(var="a", op="less_than", value=4), vars_)
    assert evaluate_condition(Condition(var="a", op="less_or_equal", value=3), vars_)
    assert evaluate_condition(Condition(var="c", op="equals", value="x"), vars_)
    assert evaluate_condition(Condition(var="c", op="not_equals", value="y"), vars_)
    assert evaluate_condition(Condition(var="b", op="is_true"), vars_)
    assert not evaluate_condition(Condition(var="b", op="is_false"), vars_)
    assert conditions_match(
        [Condition(var="a", op="greater_or_equal", value=3), Condition(var="b", op="is_true")],
        vars_,
    )


def test_effects_mutate_state_correctly() -> None:
    vars_ = {"n": 2, "flag": False}
    new_vars = apply_effects(
        vars_,
        [
            Effect(var="n", op="increment", value=3),
            Effect(var="n", op="decrement", value=1),
            Effect(var="flag", op="set", value=True),
        ],
    )
    assert new_vars["n"] == 4
    assert new_vars["flag"] is True
