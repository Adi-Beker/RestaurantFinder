from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class RestaurantBase(BaseModel):
    """Shared fields for restaurant models."""

    name: str
    city: str
    country: str
    cuisine: str
    price_level: int = Field(ge=1, le=5)
    rating: float = Field(ge=1.0, le=5.0)
    is_open: bool


class Restaurant(RestaurantBase):
    """Response model that includes the server-generated ID."""

    id: int


class RestaurantCreate(RestaurantBase):
    """Incoming payload model with validation and normalization."""

    @model_validator(mode="after")
    def normalize_text_fields(self) -> "RestaurantCreate":
        """Normalize text fields for cleaner and more consistent data."""
        self.name = self.name.strip()
        self.city = self.city.strip().title()
        self.country = self.country.strip().title()
        self.cuisine = self.cuisine.strip().title()
        return self