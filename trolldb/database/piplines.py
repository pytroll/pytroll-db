"""The module which defines some convenience classes to facilitate the use of aggregation pipelines."""

from typing import Any, Self


class PipelineDict(dict):
    """A subclass of dict which overrides the behaviour of bitwise or ``|`` and bitwise and ``&``.

    The operators are only defined for operands of type :class:`PipelineDict`. For each of the aforementioned operators,
    the result will be a dictionary with a single key/value pair. The key is either ``$or`` or ``$and`` depending on the
    operator being used. The corresponding value is a list with two elements only. The first element of the list is the
    left operand and the second element is the right operand.

    Example:
         ```
            pd1 = PipelineDict({"number": 2})
            pd2 = PipelineDict({"kind": 1})
            pd3 = pd1 & pd2

         ```
    """

    def __or__(self, other: Self):
        """TODO."""
        return PipelineDict({"$or": [self, other]})

    def __and__(self, other: Self):
        """TODO."""
        return PipelineDict({"$and": [self, other]})


class PipelineAttribute:
    """TODO."""

    def __init__(self, key: str):
        """TODO."""
        self.__key = key

    def __eq__(self, other: Any) -> PipelineDict:
        """TODO."""
        if isinstance(other, list):
            return PipelineDict(**{"$or": [{self.__key: v} for v in other]})
        return PipelineDict(**{self.__key: other})

    def __aux_operators(self, other: Any, operator: str) -> PipelineDict:
        """TODO."""
        return PipelineDict(**{self.__key: {operator: other}} if other else {})

    def __ge__(self, other: Any) -> PipelineDict:
        """TODO."""
        return self.__aux_operators(other, "$gte")

    def __gt__(self, other: Any) -> PipelineDict:
        """TODO."""
        return self.__aux_operators(other, "$gt")

    def __le__(self, other: Any) -> PipelineDict:
        """TODO."""
        return self.__aux_operators(other, "$lte")

    def __lt__(self, other: Any) -> PipelineDict:
        """TODO."""
        return self.__aux_operators(other, "$le")


class Pipelines(list):
    """TODO."""
    def __init__(self, *args, **kwargs):
        """TODO."""
        super().__init__(*args, **kwargs)

    def __iadd__(self, other):
        """TODO."""
        self.extend([{"$match": other}])
        return self

    def __add__(self, other):
        """TODO."""
        self.append({"$match": other})
        return self