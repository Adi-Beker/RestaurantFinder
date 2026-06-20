from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

# ── Auth models ──


class UserCreate(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    id: int
    username: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── AI models ──


class AIRecommendation(BaseModel):
    restaurant_name: str
    city: str
    reason: str


# ── Refresh job models ──


class RefreshJobCreated(BaseModel):
    job_id: str


class RefreshJobStatus(BaseModel):
    status: str
    result: dict | None = None
    finished_at: str | None = None
    error: str | None = None


# ── Restaurant models ──


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


# ── Discover catalogue models ──


class DiscoverRestaurant(BaseModel):
    id: int
    osm_id: str
    name: str
    city: str
    country: str
    cuisine: str
    address: str
    lat: float
    lon: float
    price_level: int
    rating: float
    is_open: bool


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str