"""
Pydantic output schemas for AI extraction.
Schema version is embedded so results remain traceable if the schema evolves.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SCHEMA_VERSION = "image_v1"


class BoundingBox(BaseModel):
    """Coordinates (either normalised [0,1] or pixel values — accept both)."""
    x: float = Field(ge=0)
    y: float = Field(ge=0)
    w: float = Field(ge=0)
    h: float = Field(ge=0)


class PersonRegion(BaseModel):
    bbox: BoundingBox | None = None
    apparent_age_group: str | None = None   # child | teen | adult | senior
    gender_presentation: str | None = None  # masc | femme | androgynous
    is_prominent: bool = False


class ObjectDetection(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    bbox: BoundingBox | None = None
    count: int = 1
    color: str | None = None
    details: list[str] = Field(default_factory=list)


class PlaceCandidate(BaseModel):
    name: str
    country: str | None = None
    region: str | None = None
    place_type: str | None = None   # city | landmark | building | nature | indoor | …
    confidence: float = Field(ge=0, le=1, default=0.5)
    reasoning: str | None = None


class SceneSummary(BaseModel):
    setting: str | None = None          # outdoor | indoor | mixed
    lighting: str | None = None         # daylight | golden_hour | night | artificial
    weather: str | None = None          # clear | cloudy | rain | snow | fog | …
    mood: str | None = None             # free text (celebratory, calm, dramatic, …)
    primary_subject: str | None = None  # short label for the main subject
    description: str                    # 2–4 sentence narrative


class ArtisticNotes(BaseModel):
    summary: str | None = None
    composition: str | None = None
    lighting: str | None = None
    detail: str | None = None
    resolution: str | None = None


class SearchTag(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1, default=0.7)


class ImageExtractionOutput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    ocr_text: str | None = None          # verbatim visible text from image
    short_summary: str | None = None
    search_tags: list[str] = Field(default_factory=list)
    search_tag_details: list[SearchTag] = Field(default_factory=list)
    scene: SceneSummary
    artistic_notes: ArtisticNotes | None = None
    objects: list[ObjectDetection] = Field(default_factory=list)
    place_candidates: list[PlaceCandidate] = Field(default_factory=list)
    person_regions: list[PersonRegion] = Field(default_factory=list)
    confidence_overall: float = Field(ge=0, le=1, default=0.8)
    extraction_notes: str | None = None  # model self-commentary or caveats
