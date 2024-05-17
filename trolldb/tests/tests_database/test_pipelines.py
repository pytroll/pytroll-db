"""Documentation to be added."""
from trolldb.database.piplines import PipelineBooleanDict


def test_pipeline_boolean_dict():
    """Documentation to be added."""
    pd1 = PipelineBooleanDict({"number": 2})
    pd2 = PipelineBooleanDict({"kind": 1})

    pd_and = pd1 & pd2
    pd_and_literal = PipelineBooleanDict({"$and": [{"number": 2}, {"kind": 1}]})
    assert pd_and == pd_and_literal

    pd_or = pd1 | pd2
    pd_or_literal = PipelineBooleanDict({"$or": [{"number": 2}, {"kind": 1}]})
    assert pd_or == pd_or_literal
