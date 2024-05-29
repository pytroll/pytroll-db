"""The module which defines some convenience classes to facilitate the use of aggregation pipelines in MongoDB."""

from typing import Any, Self


class PipelineBooleanDict(dict):
    """A subclass of dict which overrides the behavior of bitwise `or` ``|`` and bitwise `and` ``&``.

    This class makes it easier to chain and nest `"and/or"` operations.

    The operators are only defined for operands of type :class:`PipelineBooleanDict`. For each of the aforementioned
    operators, the result will be a dictionary with a single key/value pair. The key is either ``$or`` or ``$and``
    depending on the operator being used. The corresponding value is a list with two elements only. The first element
    of the list is the content of the left operand and the second element is the content of the right operand.

    Example:
        .. code-block:: python

            pd1 = PipelineBooleanDict({"number": 2})
            pd2 = PipelineBooleanDict({"kind": 1})

            pd_and = pd1 & pd2
            pd_and_literal = PipelineBooleanDict({"$and": [{"number": 2}, {"kind": 1}]})
            # The following evaluates to True
            pd_and == pd_and_literal

            pd_or = pd1 | pd2
            pd_or_literal = PipelineBooleanDict({"$or": [{"number": 2}, {"kind": 1}]})
            # The following evaluates to True
            pd_or == pd_or_literal
    """

    def __or__(self, other: Self) -> Self:
        """Implements the bitwise or operator, i.e. ``|``."""
        return PipelineBooleanDict({"$or": [self, other]})

    def __and__(self, other: Self) -> Self:
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

        Warning:
            Note how ``==`` behaves differently for :class:`PipelineBooleanDict` and :class:`PipelineAttribute`.
            In the former, it asserts equality as per the standard behaviour of the operator in Python. However, in the
            latter it acts as a filter and not an assertion of equality.

        Example:
            .. code-block:: python

                pa_list = PipelineAttribute("letter") == ["A", "B"]
                pd_list = PipelineBooleanDict({"$or": [{"letter": "A"}, {"letter": "B"}]
                # The following evaluates to True
                pa_list == pd_list

                pa_single = PipelineAttribute("letter") == "A"
                pd_single = PipelineBooleanDict({"letter": "A"})
                # The following evaluates to True
                pa_single == pd_single
        """
        if isinstance(other, list):
            return PipelineBooleanDict(**{"$or": [{self.__key: v} for v in other]})
        return PipelineBooleanDict(**{self.__key: other})

    def __aux_operators(self, other: Any, operator: str) -> PipelineBooleanDict:
        """An auxiliary function to perform comparison operations.

        Note:
            The operators herein have similar behaviour to ``==`` in the sense that they make comparison filters and are
            not to be interpreted as comparison assertions.
        """
        if isinstance(other, list):
            return PipelineBooleanDict(**{"$or": [{self.__key: {operator: v}} for v in other]})

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
        return self.__aux_operators(other, "$lt")


class Pipelines(list):
    """A class which defines a list of pipelines.

    Each item in the list is a dictionary with its key being the literal string ``"$match"`` and its corresponding value
    being of type :class:`PipelineBooleanDict`. The ``"$match"`` key is what actually triggers the matching operation in
    the MongoDB aggregation pipeline. The condition against which the matching will be performed is given by the value
    which is a simply a boolean pipeline dictionary and has a hierarchical structure.

    Example:
        .. code-block:: python

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

            # The following evaluates to True
            pipelines == pipelines_literal
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
