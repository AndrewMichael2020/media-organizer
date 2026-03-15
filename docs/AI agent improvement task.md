INSTRUCTION FOR CODEX AGENT

Refine the existing Gemini 3.1 Flash image extractor for archival / near-OSINT image analysis. Keep the current extractor and schema where they already work. Improve the AI extraction behavior, prompt wording, field quality, and normalization. Prefer a small canonical field set. If the current extractor already has nearby fields, align them to this target shape instead of rewriting the whole pipeline.

Use a fixed schema with prescribed fields. Keep the schema compact and stable. The model should fill known fields consistently rather than inventing structure.

TARGET OUTPUT SHAPE

Use these top-level sections:

1. image_summary
2. people_overview
3. people
4. objects
5. text_regions
6. setting_analysis
7. operational_context
8. landscape_analysis
9. sensitivity_review
10. quality_review

FIELD SET

1. image_summary

Purpose:
Summarize what the image visibly is.

Fields:

- strict_caption
- primary_scene
- secondary_scenes
- indoor_outdoor
- environment_type
- image_type
- location_cues
- time_of_day
- season_cues
- historical_modernity_cues
- confidence

Suggested values:

primary_scene:

- urban_street
- beach
- waterfront_nonbeach
- park
- residential
- industrial_site
- healthcare
- laboratory
- classroom
- conference
- office
- transit_area
- crowd_event
- checkpoint_or_security_area
- damaged_built_environment
- active_conflict_or_aftermath
- emergency_response_scene
- mountain_landscape
- alpine_climbing_scene
- rock_climbing_scene
- glacier_or_snowfield
- trail_or_backcountry
- other

image_type:

- candid_photo
- posed_photo
- screenshot
- surveillance_like
- scanned_document_photo
- press_photo_like
- promotional_photo_like
- unknown

environment_type:

- public
- semi_public
- private
- institutional
- commercial
- natural
- unknown

Example:
"strict_caption": "Two climbers stand on a rocky ridge with snow patches and a steep mountain face in the background."

2. people_overview

Purpose:
Provide quick scene-level human presence.

Fields:

- people_count_visible
- crowd_density
- group_structure
- dominant_activity
- confidence

Suggested values:

crowd_density:

- none
- sparse
- moderate
- dense

group_structure:

- alone
- pair
- small_group
- large_group
- crowd
- unknown

dominant_activity:

- walking
- waiting
- observing
- presentation
- leisure
- transit
- clinical_work
- lab_work
- security_activity
- emergency_response
- crowd_gathering
- climbing
- belaying
- scrambling
- mountaineering
- skiing_or_snow_travel
- unknown

3. people

Purpose:
Describe visible people for retrieval and operational interpretation.

Fields per person:

- visibility
- apparent_age_band
- clothing_items
- uniform_indicators
- accessories
- posture
- actions
- visible_expression_cues
- carried_or_worn_gear
- visual_signature_cues
- role_hypotheses
- confidence

Suggested values:

visibility:

- full_body
- upper_body
- partial_body
- face_only
- back_view
- occluded

apparent_age_band:

- child
- teen
- adult
- older_adult
- unknown

posture:

- standing
- sitting
- walking_posture
- crouching
- climbing_posture
- belaying_posture
- kneeling
- lying
- unknown

actions:

- walking
- standing
- sitting
- climbing
- belaying
- rappelling_possible
- scrambling
- observing
- carrying_equipment
- presenting
- treating_patient_possible
- operating_equipment
- guarding_possible
- loitering_possible
- scanning_surroundings_possible
- unknown

visible_expression_cues:

- smiling_visible
- neutral_expression_visible
- strain_visible
- distress_visible
- open_mouth_as_if_speaking
- face_not_clear
- unknown

Examples of clothing_items:

- helmet
- harness
- ropes_visible
- carabiners_visible
- crampons_possible
- ice_axe_visible
- puffy_jacket
- shell_jacket
- camouflage_clothing
- body_armor_possible
- scrubs
- lab_coat
- gloves
- safety_glasses
- high_visibility_vest
- swimsuit
- heavy_outerwear
- protective_mask
- plainclothes_tactical_style_possible
- military_boots_possible

Examples of carried_or_worn_gear:

- radio_device
- backpack
- camera
- tripod
- clipboard
- laptop
- climbing_rope
- ice_axe
- trekking_poles
- avalanche_gear_possible
- weapon_possible
- concealed_bulk_possible
- medical_bag
- none_visible

Examples of visual_signature_cues:

- matching_nonuniform_attire_possible
- tactical_accessory_without_uniform
- earpiece_possible
- concealed_item_outline_possible
- coordinated_plainclothes_group_possible
- face_covering_possible
- military_haircut_possible
- stance_consistent_with_security_awareness
- none_visible

Suggested role_hypotheses:

- swimmer
- beachgoer
- tourist
- participant
- bystander
- staff_member
- service_worker
- athlete
- coach_or_instructor
- research_or_fieldwork_personnel
- medical_staff
- lab_staff
- security_personnel
- plainclothes_security_possible
- emergency_responder
- speaker_or_presenter
- photographer_or_media
- climber
- belayer
- mountaineer
- skier_or_alpine_traveler
- displaced_person_possible
- unknown

Role rule:
Use broad role labels. Strong visual indicators are enough for broad role hypotheses. Do not narrow into specific job titles.

Good:
{
"visibility": "full_body",
"apparent_age_band": "adult",
"clothing_items": ["helmet", "harness", "shell_jacket"],
"uniform_indicators": ["none_visible"],
"accessories": [],
"posture": "climbing_posture",
"actions": ["climbing"],
"visible_expression_cues": ["face_not_clear"],
"carried_or_worn_gear": ["climbing_rope", "carabiners_visible"],
"visual_signature_cues": ["none_visible"],
"role_hypotheses": [
{
"label": "climber",
"confidence": "high",
"evidence": ["helmet", "harness", "rope system", "rock face context"]
}
],
"confidence": "high"
}

Additional good example:
{
"visibility": "full_body",
"apparent_age_band": "adult",
"clothing_items": ["plainclothes_tactical_style_possible", "military_boots_possible"],
"uniform_indicators": ["none_visible"],
"accessories": [],
"posture": "standing",
"actions": ["observing", "scanning_surroundings_possible"],
"visible_expression_cues": ["neutral_expression_visible"],
"carried_or_worn_gear": ["radio_device", "concealed_bulk_possible"],
"visual_signature_cues": ["tactical_accessory_without_uniform", "coordinated_plainclothes_group_possible"],
"role_hypotheses": [
{
"label": "plainclothes_security_possible",
"confidence": "medium",
"evidence": ["radio device", "military-style boots", "coordinated plainclothes appearance", "security-aware posture"]
}
],
"confidence": "medium"
}

4. objects

Purpose:
Capture high-information objects and equipment.

Fields:

- object_label
- count_estimate
- significance
- evidence

Suggested object_label examples:

- vehicle
- armored_vehicle_possible
- ambulance
- police_vehicle_possible
- drone_possible
- camera
- microphone
- tripod
- laptop
- clipboard
- placard
- barricade
- roadblock
- sandbags
- medical_stretcher
- weapon_possible
- protective_barrier
- radio_equipment
- industrial_equipment
- lab_equipment
- damaged_vehicle
- debris
- fire_or_smoke_visible
- climbing_rope
- fixed_rope_possible
- anchor_system_possible
- carabiner_cluster
- ice_axe
- crampons_possible
- avalanche_probe_possible
- tent_or_bivy_possible
- route_marker_possible
- insignia_patch_possible
- armband_possible
- unmarked_vehicle_possible

significance:

- high
- medium
- low

5. text_regions

Purpose:
Integrate OCR-fed text and its visible context.

Fields:

- text
- context
- confidence

Suggested context values:

- signage
- badge
- uniform_text
- vehicle_marking
- placard
- storefront
- whiteboard
- document_fragment
- building_marking
- checkpoint_marking
- trail_sign
- route_marker
- equipment_label

Use OCR text if supplied. Do not invent text.

6. setting_analysis

Purpose:
Classify place, scene function, affiliation cues, and broad socioeconomic setting cues.

Fields:

- setting_type_hypotheses
- place_type_hypotheses
- public_private
- institutional_commercial_leisure
- built_environment_economic_signal
- technical_signal
- visible_logos
- visible_insignia
- organization_text_cues
- confidence

Suggested setting_type_hypotheses:

- urban_public_space
- resort_or_hospitality
- clinical_interior
- laboratory_workspace
- office_workspace
- educational_space
- industrial_zone
- transit_area
- public_event_space
- natural_fieldsite
- checkpoint_or_security_area
- emergency_response_scene
- conflict_affected_area
- damaged_infrastructure_zone
- alpine_environment
- climbing_crag
- glacier_travel_zone
- mountain_hut_or_basecamp
- unknown

Suggested place_type_hypotheses:

- urban_waterfront
- city_street
- residential_block
- hospital_or_clinic
- laboratory
- school_or_classroom
- office
- industrial_facility
- transit_platform
- roadside_checkpoint
- damaged_city_block
- shelter_or_staging_area
- rock_wall_or_crag
- alpine_ridge
- glacier_or_snowfield
- mountain_trail
- basecamp
- unknown

public_private:

- public
- semi_public
- private
- unknown

institutional_commercial_leisure:

- institutional
- commercial
- leisure
- civic
- residential
- natural
- unknown

built_environment_economic_signal:

- luxury
- middle_class
- working_class_or_utilitarian
- impoverished_or_deprived
- mixed
- not_applicable
- unknown

technical_signal:

- low
- medium
- high
- unknown

Examples:

- luxury resort lobby -> built_environment_economic_signal = luxury
- ordinary city apartment block -> middle_class or working_class_or_utilitarian depending on cues
- visibly neglected or damaged deprived setting -> impoverished_or_deprived if strong visible evidence
- mountain face, glacier, remote ridge -> not_applicable

7. operational_context

Purpose:
Add compact operational meaning for difficult environments.

Fields:

- scene_function_hypotheses
- security_presence
- covert_or_plainclothes_indicators
- damage_indicators
- threat_indicators
- mobility_context
- infrastructure_status
- confidence

Suggested scene_function_hypotheses:

- routine_public_activity
- leisure_activity
- transit_or_movement
- institutional_work
- clinical_activity
- lab_activity
- media_coverage
- security_operation
- emergency_response
- checkpoint_control
- displacement_or_evacuation_possible
- conflict_aftermath_possible
- crowd_monitoring
- climbing_activity
- alpine_ascent_or_descent
- rescue_or_technical_access
- unknown

security_presence:

- none_visible
- low
- medium
- high
- unknown

covert_or_plainclothes_indicators examples:

- coordinated_plainclothes_group_possible
- tactical_accessories_without_uniform
- concealed_bulk_possible
- earpiece_or_radio_possible
- military_style_footwear_possible
- unmarked_vehicle_association_possible
- controlled_perimeter_behavior_possible
- none_visible

mobility_context:

- pedestrian_flow
- vehicle_flow
- blocked_route
- controlled_access
- staging_area
- evacuation_like
- vertical_progression
- rope_protected_movement
- unknown

infrastructure_status:

- normal
- damaged
- heavily_damaged
- temporary_barriers_present
- smoke_or_fire_present
- utility_disruption_possible
- natural_terrain
- unknown

damage_indicators examples:

- shattered_windows
- rubble
- scorch_marks
- collapsed_wall
- damaged_vehicle
- broken_road_surface
- smoke_visible
- fire_visible
- rockfall_debris
- avalanche_debris_possible
- crevasse_visible

threat_indicators examples:

- visible_weapon_possible
- protective_posture
- armored_vehicle_possible
- checkpoint_barrier
- blast_damage_possible
- active_smoke_or_fire
- crowd_control_barrier
- exposure_to_fall_hazard
- avalanche_hazard_possible
- crevasse_hazard_possible
- none_visible

8. landscape_analysis

Purpose:
Strengthen outdoor, mountain, climbing, and terrain reading.

Fields:

- terrain_type
- slope_character
- rock_type_visual_cues
- snow_ice_presence
- water_features
- vegetation_zone
- route_or_access_cues
- exposure_level
- weather_visibility_cues
- confidence

Suggested terrain_type:

- flat_urban
- beach
- forest
- trail
- talus_or_scree
- rock_wall
- alpine_ridge
- glacier
- snowfield
- mixed_mountain_terrain
- desert_or_barren
- water_edge
- unknown

slope_character:

- flat
- gentle
- steep
- very_steep
- vertical_or_near_vertical
- unknown

rock_type_visual_cues:

- slabby_rock_possible
- blocky_rock_possible
- chossy_or_loose_rock_possible
- glacier_polished_possible
- stratified_rock_possible
- not_clear

snow_ice_presence:

- none_visible
- patchy_snow
- continuous_snow
- glacier_ice_possible
- mixed_snow_rock
- unknown

water_features:

- none_visible
- lake
- river
- waterfall
- surf_or_ocean
- shoreline
- glacial_stream
- unknown

vegetation_zone:

- urban
- beach_margin
- forested
- subalpine
- alpine
- barren_high_alpine
- unknown

route_or_access_cues:

- trail_visible
- cairn_or_marker_possible
- fixed_protection_possible
- rope_line_visible
- road_access_visible
- scramble_line_possible
- glacier_track_possible
- unknown

exposure_level:

- low
- moderate
- high
- extreme
- unknown

weather_visibility_cues:

- clear
- overcast
- fog_or_cloud_obscuration
- blowing_snow_possible
- stormy_possible
- smoke_haze_possible
- unknown

9. sensitivity_review

Purpose:
Provide machine-usable risk signaling.

Fields:

- flags
- severity
- reasons

Suggested flags:

- minor_possible
- partial_nudity
- medical_context
- distress_possible
- violence_visible
- dead_or_injured_person_possible
- law_enforcement_present
- military_or_armed_presence_possible
- private_information_visible
- graphic_damage_possible
- high_exposure_or_fall_risk
- none

severity:

- low
- medium
- high

10. quality_review

Purpose:
Explain uncertainty and extraction limits.

Fields:

- image_quality
- occlusion_level
- framing
- limitations

Suggested framing:

- close_up
- medium_shot
- wide_shot
- cropped_subject
- obstructed_view
- unknown

PROMPT UPDATE

Revise the existing extractor prompt so the model fills this canonical field set consistently.

Use instruction language like:

"Analyze the attached image for archival and operational metadata extraction. Return JSON only and match the provided schema exactly. Fill the prescribed fields only. Prefer direct visual observations. Use null, unknown, or empty arrays when uncertain. Every hypothesis must include short visual evidence phrases. Use broad role labels only. Pay special attention to place cues, visible text, logos, insignia, equipment, barriers, damage, smoke, emergency cues, terrain, climbing or mountaineering gear, landscape type, scene function, and plainclothes or covert-security visual signatures when present. If OCR text is provided separately, use it as input context rather than guessing additional text. Do not infer identity, nationality, ethnicity, religion, relationship status, internal emotional state, allegiance, or responsibility. Describe only what is visible in the image and keep the output compact."

NORMALIZATION RULES

After generation:

1. parse JSON
2. validate against local schema
3. normalize enum values
4. trim long text
5. cap arrays
6. remove hypotheses with empty evidence
7. map overly narrow role labels to the nearest broad label
8. map invalid values to unknown
9. suppress detailed claims that are not visually supported

Examples of role normalization:

- marine_biologist -> research_or_fieldwork_personnel
- combat_medic -> emergency_responder or medical_staff
- alpine_guide -> coach_or_instructor or mountaineer depending on evidence
- infantry_sergeant -> security_personnel
- undercover_officer -> plainclothes_security_possible

ARRAY CAPS

Keep output compact:

- secondary_scenes: max 5
- role_hypotheses per person: max 3
- setting_type_hypotheses: short list only
- place_type_hypotheses: short list only
- scene_function_hypotheses: short list only
- visible_logos: short list only
- visible_insignia: short list only
- organization_text_cues: short list only
- covert_or_plainclothes_indicators: short list only
- damage_indicators: short list only
- threat_indicators: short list only
- route_or_access_cues: short list only
- evidence per item: max 3 to 5 short phrases
- limitations: short list only
- reasons: short list only

GOOD OUTPUT EXAMPLES

Good role:
{
"label": "mountaineer",
"confidence": "high",
"evidence": ["helmet", "ice axe", "crampons possible", "snow and ridge terrain"]
}

Good setting:
{
"setting_type_hypotheses": [
{
"label": "alpine_environment",
"confidence": "high",
"evidence": ["high rocky ridge", "patchy snow", "exposed terrain"]
}
],
"place_type_hypotheses": [
{
"label": "alpine_ridge",
"confidence": "high",
"evidence": ["narrow ridge line", "steep drop-offs", "rock and snow mix"]
}
],
"public_private": "natural",
"institutional_commercial_leisure": ["natural"],
"built_environment_economic_signal": "not_applicable",
"technical_signal": "medium",
"visible_logos": [],
"visible_insignia": [],
"organization_text_cues": [],
"confidence": "high"
}

Good landscape:
{
"terrain_type": "mixed_mountain_terrain",
"slope_character": "steep",
"rock_type_visual_cues": ["blocky_rock_possible"],
"snow_ice_presence": "mixed_snow_rock",
"water_features": "none_visible",
"vegetation_zone": "alpine",
"route_or_access_cues": ["scramble_line_possible"],
"exposure_level": "high",
"weather_visibility_cues": "clear",
"confidence": "medium"
}

Good operational context:
{
"scene_function_hypotheses": [
{
"label": "security_operation",
"confidence": "medium",
"evidence": ["controlled perimeter", "coordinated personnel placement", "restricted movement cues"]
}
],
"security_presence": "medium",
"covert_or_plainclothes_indicators": ["coordinated_plainclothes_group_possible", "earpiece_or_radio_possible"],
"damage_indicators": [],
"threat_indicators": ["crowd_control_barrier"],
"mobility_context": "controlled_access",
"infrastructure_status": "normal",
"confidence": "medium"
}

FINAL STANDARD

The extractor should produce a compact, fixed-shape, evidence-backed JSON record that is useful for archival and near-OSINT image work across ordinary civic images, hostile environments, and mountain or climbing landscapes. It should be strong at place cues, text cues, logos, insignia, equipment, barriers, damage, terrain, climbing / mountaineering indicators, salient objects, plainclothes or covert-security visual signatures, and broad role hypotheses grounded in visible evidence.
