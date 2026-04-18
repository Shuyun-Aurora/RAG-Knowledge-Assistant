from typing import Generic, TypeVar, List
from pydantic.generics import GenericModel

T = TypeVar("T")

class PageResponse(GenericModel, Generic[T]):
    total: int
    items: List[T]
