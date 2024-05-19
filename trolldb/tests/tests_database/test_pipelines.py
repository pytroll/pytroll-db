"""Tests for the pipelines and applying comparison operations on them."""
from trolldb.database.piplines import PipelineAttribute, PipelineBooleanDict
from trolldb.test_utils.common import assert_equal, compare_by_operator_name


def test_pipeline_boolean_dict():
    """Checks the pipeline boolean dict for bitwise `and/or` operators."""
    pd1 = PipelineBooleanDict({"number": 2})
    pd2 = PipelineBooleanDict({"kind": 1})

    pd_and = pd1 & pd2
    pd_and_literal = PipelineBooleanDict({"$and": [{"number": 2}, {"kind": 1}]})
    assert pd_and == pd_and_literal

    pd_or = pd1 | pd2
    pd_or_literal = PipelineBooleanDict({"$or": [{"number": 2}, {"kind": 1}]})
    assert pd_or == pd_or_literal


def test_pipeline_attribute():
    """Tests different comparison operators for a pipeline attribute in a list and as a single item."""
    for op in ["$eq", "$gte", "$gt", "$lte", "$lt"]:
        assert_equal(
            compare_by_operator_name(op, PipelineAttribute("letter"), "A"),
            PipelineBooleanDict({"letter": {op: "A"}} if op != "$eq" else {"letter": "A"})
        )
        assert_equal(
            compare_by_operator_name(op, PipelineAttribute("letter"), ["A", "B"]),
            PipelineBooleanDict({"$or": [
                {"letter": {op: "A"} if op != "$eq" else "A"},
                {"letter": {op: "B"} if op != "$eq" else "B"}
            ]})
        )
