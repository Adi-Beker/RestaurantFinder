from collections.abc import Generator
from typing import Annotated

from fastapi import Depends

from app.repository import RestaurantRepository

_repository = RestaurantRepository()


def get_repository() -> Generator[RestaurantRepository, None, None]:
    """Provide repository to endpoints."""
    yield _repository


RepositoryDep = Annotated[RestaurantRepository, Depends(get_repository)]