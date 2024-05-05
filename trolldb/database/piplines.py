from typing import Any, Self


class PipelineDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __or__(self, other: Self):
        return PipelineDict(**{"$or": [self, other]})

    def __and__(self, other: Self):
        return PipelineDict(**{"$and": [self, other]})


class PipelineAttribute:
    def __init__(self, key: str):
        self.__key = key

    def __eq__(self, other: Any) -> PipelineDict:
        if isinstance(other, list):
            return PipelineDict(**{"$or": [{self.__key: v} for v in other]})
        return PipelineDict(**{self.__key: other})

    def __aux_operators(self, other: Any, operator: str) -> PipelineDict:
        return PipelineDict(**{self.__key: {operator: other}} if other else {})

    def __ge__(self, other: Any) -> PipelineDict:
        return self.__aux_operators(other, "$gte")

    def __gt__(self, other: Any) -> PipelineDict:
        return self.__aux_operators(other, "$gt")

    def __le__(self, other: Any) -> PipelineDict:
        return self.__aux_operators(other, "$lte")

    def __lt__(self, other: Any) -> PipelineDict:
        return self.__aux_operators(other, "$le")


class Pipelines(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __iadd__(self, other):
        self.extend([{"$match": other}])
        return self

    def __add__(self, other):
        self.append({"$match": other})
        return self
