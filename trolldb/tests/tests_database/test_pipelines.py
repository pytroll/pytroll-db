"""Tests for the pipelines and applying comparison operations on them."""
from trolldb.database.pipelines import PipelineAttribute, PipelineBooleanDict, Pipelines
from trolldb.test_utils.common import compare_by_operator_name


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
        assert (
                compare_by_operator_name(op, PipelineAttribute("letter"), "A") ==
                PipelineBooleanDict({"letter": {op: "A"}} if op != "$eq" else {"letter": "A"})
        )
        assert (
                compare_by_operator_name(op, PipelineAttribute("letter"), ["A", "B"]) ==
                PipelineBooleanDict({"$or": [
                    {"letter": {op: "A"} if op != "$eq" else "A"},
                    {"letter": {op: "B"} if op != "$eq" else "B"}
                ]})
        )


def test_pipelines():
    """Tests the elements of Pipelines."""
    pipelines = Pipelines()
    pipelines += PipelineAttribute("platform_name") == "P"
    pipelines += PipelineAttribute("sensor") == ["SA", "SB"]

    pipelines_literal = [
        {"$match":
             {"platform_name": "P"}
         },
        {"$match":
             {"$or": [{"sensor": "SA"}, {"sensor": "SB"}]}
         }
    ]

    for p1, p2 in zip(pipelines, pipelines_literal, strict=False):
        assert p1 == p2
