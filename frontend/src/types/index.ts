// shared TS types

export interface Location {
    latitude: number | null
    longitude: number | null
    city: string | null
    state: string | null
    zip_code?: string | null
}

export interface User {
    id: string
    email: string | null
    display_name: string
    oauth_provider: string
    default_location: Location | null
    dietary_info: Record<string, unknown> | null
    created_at: string
}

export interface AuthResponse {
    access_token: string
    user: User
}

export interface SpeciesResult {
    common_name: string
    scientific_name: string | null
    confidence: number
}

export interface NotableNutrient {
    nutrient: string
    amount: string
    percent_dv: number | null
}


export interface NutritionInfo {
    species: string
    common_name: string
    confidence: string
    source: string
    edible_parts: string[]
    calories_per_100g: number | null
    protein_g: number | null
    fat_g: number | null
    carbs_g: number | null
    fiber_g: number | null
    notable_nutrients: NotableNutrient[]
    notes: string | null
}

export interface WeatherSnapshot {
    temperature: number
    temperature_unit: string
    short_forecast: string
    detailed_forecast: string | null
    wind_speed: string | null
    wind_direction: string | null
    precip_probability: number | null
    is_daytime: boolean | null
}

 export interface SafetyDetails {                                                         
    confidence_tier: "strong_match" | "possible_match" | "uncertain" | "no_result"
    candidates: {
        species: string                                                                  
        confidence: number
        safety_verdict: string                                                           
        warning_message: string | null
    }[] | null
    safety_info: {
        edibility: string[] | string | null
        edible_parts: string[]
        preparation: { edible?: string; medicinal?: string; warning?: string } | string | null
        sources: string[]
    } | null
    safety_verdict: string | null
    lookalike_findings: Record<string, unknown>[] | null                                 
    protection_findings: Record<string, unknown>[] | null
    warning_message: string                                                              
}

export interface DiscoveryResponse {
    id: string
    user_id: string | null
    session_id: string | null
    photo_url: string | null
    heatmap_url: string | null
    discovered_at: string | null
    location: Location | null
    species_prediction: SpeciesResult | null
    all_predictions: SpeciesResult[] | null
    safety_verdict: string | null
    safety_details: SafetyDetails | null
    nutrition_info: NutritionInfo | null
    weather_context: WeatherSnapshot | null
    user_notes: string | null
}

export interface DiscoveryListItem {
    id: string
    photo_url: string | null
    species_prediction: SpeciesResult | null
    confidence_score: number | null
    safety_verdict: string | null
    discovered_at: string | null
    location: Location | null
    user_notes: string | null
}

export interface DiscoveryQueryParams {
    limit?: number
    cursor?: string
    q?: string
    safety?: string
    confidence_min?: number
    confidence_max?: number
    date_from?: string
    date_to?: string
}

export interface LocationData {
    latitude: number | null
    longitude: number | null
    city: string
    state: string
    zip_code: string
}

export interface SavedLocation {
    id: string
    label: string
    city: string | null
    state: string | null
    latitude: number
    longitude: number
    is_pinned: boolean
    created_at: string
}

export interface CurrentWeather {
    temperature: number
    temperature_unit: string
    short_forecast: string
    wind_speed: string | null
    wind_direction: string | null
    precip_probability: number | null
}

export interface ForecastDay {
    name: string
    date: string
    temperature_high: number
    temperature_low: number
    temperature_unit: string
    short_forecast: string
    precip_probability: number | null
}

export interface PlanningWeather {
    current: CurrentWeather
    forecast: ForecastDay[]
}

export interface ClassifyEventData {
    discovery_id: string
    predictions: { species: string; confidence: number }[]
    heatmap_url: string
}

export interface NutritionEventData {
    nutrition_info: NutritionInfo | null
}

export interface WeatherEventData {
    weather_context: WeatherSnapshot | null
}

export interface CompleteEventData {
    discovery_id: string
    enrichment_status: string
}

export interface ErrorEventData {
    message: string
}

export type ForageEvent =
    | { event: "classify"; data: ClassifyEventData }
    | { event: "safety_static"; data: SafetyDetails }
    | { event: "nutrition"; data: NutritionEventData }
    | { event: "weather"; data: WeatherEventData }
    | { event: "complete"; data: CompleteEventData }
    | { event: "error"; data: ErrorEventData }