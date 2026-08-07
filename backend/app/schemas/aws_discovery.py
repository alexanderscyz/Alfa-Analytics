import uuid

from pydantic import BaseModel, Field, field_validator

from app.schemas.cloud_resource import CloudResourceResponse


class MultiRegionDiscoveryRequest(BaseModel):
    regions: list[str] = Field(min_length=1, max_length=10)

    @field_validator("regions")
    @classmethod
    def normalize_regions(cls, regions: list[str]) -> list[str]:
        normalized_regions = list(
            dict.fromkeys(region.strip() for region in regions),
        )

        if any(not region for region in normalized_regions):
            raise ValueError("Regions cannot be empty")

        return normalized_regions


class RegionDiscoveryResult(BaseModel):
    region: str
    status: str
    resource_count: int
    duration_ms: int
    error_message: str | None = None


class MultiRegionDiscoveryResponse(BaseModel):
    cloud_account_id: uuid.UUID
    status: str
    requested_regions: list[str]
    successful_regions: list[str]
    failed_regions: list[str]
    resource_count: int
    resources: list[CloudResourceResponse]
    region_results: list[RegionDiscoveryResult]
