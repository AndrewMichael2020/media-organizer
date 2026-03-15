"""
Pydantic output schemas for AI extraction.
Schema version is embedded so results remain traceable if the schema evolves.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SCHEMA_VERSION = "image_v1"

ConfidenceLevel = Literal["low", "medium", "high", "unknown"]


class EvidenceHypothesis(BaseModel):
    label: str
    confidence: ConfidenceLevel = "unknown"
    evidence: list[str] = Field(default_factory=list)


class ImageSummary(BaseModel):
    strict_caption: str | None = None
    primary_scene: str = "other"
    secondary_scenes: list[str] = Field(default_factory=list)
    indoor_outdoor: str = "unknown"
    environment_type: str = "unknown"
    image_type: str = "unknown"
    location_cues: list[str] = Field(default_factory=list)
    time_of_day: str | None = None
    season_cues: list[str] = Field(default_factory=list)
    historical_modernity_cues: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = "unknown"


class PeopleOverview(BaseModel):
    people_count_visible: int = 0
    crowd_density: str = "none"
    group_structure: str = "unknown"
    dominant_activity: str = "unknown"
    confidence: ConfidenceLevel = "unknown"


class PersonEntry(BaseModel):
    visibility: str = "unknown"
    apparent_age_band: str = "unknown"
    clothing_items: list[str] = Field(default_factory=list)
    uniform_indicators: list[str] = Field(default_factory=list)
    accessories: list[str] = Field(default_factory=list)
    posture: str = "unknown"
    actions: list[str] = Field(default_factory=list)
    visible_expression_cues: list[str] = Field(default_factory=list)
    carried_or_worn_gear: list[str] = Field(default_factory=list)
    visual_signature_cues: list[str] = Field(default_factory=list)
    role_hypotheses: list[EvidenceHypothesis] = Field(default_factory=list)
    confidence: ConfidenceLevel = "unknown"


class ObjectEntry(BaseModel):
    object_label: str
    count_estimate: int = 1
    significance: str = "low"
    evidence: list[str] = Field(default_factory=list)


class TextRegion(BaseModel):
    text: str
    context: str = "signage"
    confidence: ConfidenceLevel = "unknown"


class SettingAnalysis(BaseModel):
    setting_type_hypotheses: list[EvidenceHypothesis] = Field(default_factory=list)
    place_type_hypotheses: list[EvidenceHypothesis] = Field(default_factory=list)
    public_private: str = "unknown"
    institutional_commercial_leisure: str = "unknown"
    built_environment_economic_signal: str = "unknown"
    technical_signal: str = "unknown"
    visible_logos: list[str] = Field(default_factory=list)
    visible_insignia: list[str] = Field(default_factory=list)
    organization_text_cues: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = "unknown"


class LocationMeta(BaseModel):
    place_name_candidate: str | None = None
    nearest_city_candidate: str | None = None
    province_or_state_candidate: str | None = None
    country_candidate: str | None = None
    location_source: str = "unknown"
    location_precision: str = "unknown"
    location_confidence: ConfidenceLevel = "unknown"
    location_evidence: list[str] = Field(default_factory=list)


class OperationalContext(BaseModel):
    scene_function_hypotheses: list[EvidenceHypothesis] = Field(default_factory=list)
    security_presence: str = "unknown"
    covert_or_plainclothes_indicators: list[str] = Field(default_factory=list)
    damage_indicators: list[str] = Field(default_factory=list)
    threat_indicators: list[str] = Field(default_factory=list)
    mobility_context: str = "unknown"
    infrastructure_status: str = "unknown"
    confidence: ConfidenceLevel = "unknown"


class LandscapeAnalysis(BaseModel):
    terrain_type: str = "unknown"
    slope_character: str = "unknown"
    rock_type_visual_cues: list[str] = Field(default_factory=list)
    snow_ice_presence: str = "unknown"
    water_features: str = "unknown"
    vegetation_zone: str = "unknown"
    route_or_access_cues: list[str] = Field(default_factory=list)
    exposure_level: str = "unknown"
    weather_visibility_cues: str = "unknown"
    confidence: ConfidenceLevel = "unknown"


class SensitivityReview(BaseModel):
    flags: list[str] = Field(default_factory=list)
    severity: str = "low"
    reasons: list[str] = Field(default_factory=list)


class QualityReview(BaseModel):
    image_quality: str | None = None
    occlusion_level: str | None = None
    framing: str = "unknown"
    limitations: list[str] = Field(default_factory=list)


class ImageExtractionOutput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    image_summary: ImageSummary
    people_overview: PeopleOverview
    people: list[PersonEntry] = Field(default_factory=list)
    objects: list[ObjectEntry] = Field(default_factory=list)
    text_regions: list[TextRegion] = Field(default_factory=list)
    setting_analysis: SettingAnalysis
    location_meta: LocationMeta
    operational_context: OperationalContext
    landscape_analysis: LandscapeAnalysis
    sensitivity_review: SensitivityReview
    quality_review: QualityReview
