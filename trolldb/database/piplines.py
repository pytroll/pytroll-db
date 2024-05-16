"""The module which defines some convenience classes to facilitate the use of aggregation pipelines in MongoDB."""

from typing import Any, Self


class PipelineBooleanDict(dict):
    """A subclass of dict which overrides the behaviour of bitwise `OR` (``|``) and bitwise `AND` (``&``).

    This class makes it easier to chain and nest `And/Or` operations.

    The operators are only defined for operands of type :class:`PipelineDict`. For each of the aforementioned operators,
    the result will be a dictionary with a single key/value pair. The key is either ``$or`` or ``$and`` depending on the
    operator being used. The corresponding value is a list with two elements only. The first element of the list is the
    left operand and the second element is the right operand.

    Example:
        .. code-block:: python

            pd1 = PipelineDict({"number": 2})
            pd2 = PipelineDict({"kind": 1})

            pd_and = pd1 & pd2  # is equivalent to the following
            pd_and_literal = PipelineDict({"$and": [{"number": 2}, {"kind": 1}]})

            pd_or = pd1 | pd2  # is equivalent to the following
            pd_or_literal = PipelineDict({"$or": [{"number": 2}, {"kind": 1}]})
    """

    def __or__(self, other: Self):
        """Implements the bitwise or operator, i.e. ``|``."""
        return PipelineBooleanDict({"$or": [self, other]})

    def __and__(self, other: Self):
        """Implements the bitwise and operator, i.e. ``&``."""
        return PipelineBooleanDict({"$and": [self, other]})


class PipelineAttribute:
    """A class which defines a single pipeline attribute on which boolean operations will be performed.

    The boolean operations are in the form of boolean dicts of type :class:`PipelineBooleanDict`.
    """

    def __init__(self, key: str) -> None:
        """The constructor which specifies the pipeline attribute to work with."""
        self.__key = key

    def __eq__(self, other: Any) -> PipelineBooleanDict:
        """Implements the equality operator, i.e. ``==``.

        This makes a boolean filter in which the attribute can match any of the items in ``other`` if it is a list, or
        the ``other`` itself, otherwise.
        """
        if isinstance(other, list):
            return PipelineBooleanDict(**{"$or": [{self.__key: v} for v in other]})
        return PipelineBooleanDict(**{self.__key: other})

    def __aux_operators(self, other: Any, operator: str) -> PipelineBooleanDict:
        """An auxiliary function to perform comparison operations."""
        return PipelineBooleanDict(**{self.__key: {operator: other}} if other else {})

    def __ge__(self, other: Any) -> PipelineBooleanDict:
        """Implements the `greater than or equal to` operator, i.e. ``>=``."""
        return self.__aux_operators(other, "$gte")

    def __gt__(self, other: Any) -> PipelineBooleanDict:
        """Implements the `greater than` operator, i.e. ``>``."""
        return self.__aux_operators(other, "$gt")

    def __le__(self, other: Any) -> PipelineBooleanDict:
        """Implements the `less than or equal to` operator, i.e. ``<=``."""
        return self.__aux_operators(other, "$lte")

    def __lt__(self, other: Any) -> PipelineBooleanDict:
        """Implements the `less than` operator, i.e. ``<``."""
        return self.__aux_operators(other, "$le")


class Pipelines(list):
    """A class which defines a list of pipelines.

    Each item in the list is a dictionary with its key being the literal string ``"$match"`` and its corresponding value
    being of type :class:`PipelineBooleanDict`. The``"$match"`` key is what actually triggers the matching operation in
    the MongoDB aggregation pipeline. The condition against which the matching will be performed is given by the value
    which is a simply a boolean pipeline dictionary which has a hierarchical structure.
    """

    def __iadd__(self, other: PipelineBooleanDict) -> Self:
        """Implements the augmented (aka in-place) addition operator, i.e. ``+=``.

        This is similar to :func:`extend` function of a list.
        """
        self.extend([{"$match": other}])
        return self

    def __add__(self, other: PipelineBooleanDict) -> Self:
        """Implements the addition operator, i.e. ``+``.

        This is similar to :func:`append` function of a list.
        """
        self.append({"$match": other})
        return self
