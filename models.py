"""Data models for scraped price output."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PriceRow(BaseModel):
    """One price entry for a specific kW range or tariff."""

    kw_range: str = Field(..., description="e.g. AC 7-22 kW, DC 50 kW")
    unit: str = Field(default="kWh", description="kWh or minute")
    price: float = Field(..., description="Numeric price")
    note: Optional[str] = Field(default=None)


class ProviderPrice(BaseModel):
    """Full result for one scraped URL."""

    provider_name: str = Field(..., description="Provider or site name")
    source_url: str = Field(..., description="URL that was scraped")
    scraped_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    currency: str = Field(default="TRY", description="TRY, EUR, USD, etc.")
    prices: list[PriceRow] = Field(default_factory=list)
    raw_notes: Optional[str] = Field(default=None)
    status: str = Field(default="success", description="success | no_data | partial | failed")
    error: Optional[str] = Field(default=None)
