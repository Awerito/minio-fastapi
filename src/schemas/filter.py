from enum import Enum
from pydantic import BaseModel, Field


class Sorting(str, Enum):
    top = "top"
    new = "new"


class MemesFilter(BaseModel):
    sort_by: Sorting = Field(
        Sorting.new, title="Sort by", description="The sorting order"
    )
    page: int = Field(
        1, title="Page number", description="The page number to retrieve", gt=0
    )
    limit: int = Field(
        10,
        title="Page size",
        description="The number of items to retrieve per page",
        gt=0,
        lt=101,
    )
