import { useEffect, useRef, useState } from "react"
import { MapPin, Pin, Trash2, Plus, Droplets, Wind, ChevronDown } from "lucide-react"
import { api } from "@/libs/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { WeatherIcon } from "@/components/results/WeatherPanel"
import LocationInput from "@/components/upload/LocationInput"
import LoadingSpinner from "@/components/LoadingSpinner"
import type { SavedLocation, ForecastDay, CurrentWeather, PlanningWeather, LocationData } from "@/types"


function PlanningPage() {
    const [locations, setLocations] = useState<SavedLocation[]>([])
    const [current, setCurrent] = useState<CurrentWeather | null>(null)
    const [forecast, setForecast] = useState<ForecastDay[]>([])
    const [activeLocation, setActiveLocation] = useState<SavedLocation | null>(null)
    const [isLoadingLocations, setIsLoadingLocations] = useState(true)
    const [isLoadingWeather, setIsLoadingWeather] = useState(false)
    const [listExpanded, setListExpanded] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const weatherCache = useRef<Map<string, PlanningWeather>>(new Map())

    // Add location form
    const [showAddForm, setShowAddForm] = useState(false)
    const [newLabel, setNewLabel] = useState("")
    const [newLocation, setNewLocation] = useState<LocationData | null>(null)
    const [isSaving, setIsSaving] = useState(false)

    useEffect(() => {
        loadLocations()
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    async function loadLocations() {
        try {
            const data = await api.getLocations()
            setLocations(data)

            // Auto-load weather for pinned location
            const pinned = data.find((loc) => loc.is_pinned)
            if (pinned) {
                setActiveLocation(pinned)
                setListExpanded(false)
                loadWeather(pinned)
            }
        } catch {
            setError("Failed to load locations.")
        } finally {
            setIsLoadingLocations(false)
        }
    }

    async function loadWeather(location: SavedLocation) {
        // Use cached data if available
        const cached = weatherCache.current.get(location.id)
        if (cached) {
            setCurrent(cached.current)
            setForecast(cached.forecast)
            return
        }

        setIsLoadingWeather(true)
        setCurrent(null)
        setForecast([])
        try {
            const data = await api.getPlanningWeather(location.latitude, location.longitude)
            weatherCache.current.set(location.id, data)
            setCurrent(data.current)
            setForecast(data.forecast)
        } catch {
            setError("Unable to fetch weather. Try again later.")
        } finally {
            setIsLoadingWeather(false)
        }
    }

    function handleSelectLocation(location: SavedLocation) {
        setActiveLocation(location)
        setListExpanded(false)
        loadWeather(location)
    }

    async function handlePin(id: string) {
        try {
            await api.pinLocation(id)
            const updated = await api.getLocations()
            setLocations(updated)
        } catch {
            setError("Failed to pin location.")
        }
    }

    async function handleDelete(id: string) {
        try {
            await api.deleteLocation(id)
            setLocations((prev) => prev.filter((loc) => loc.id !== id))
            weatherCache.current.delete(id)
            if (activeLocation?.id === id) {
                setActiveLocation(null)
                setCurrent(null)
                setForecast([])
                setListExpanded(true)
            }
        } catch {
            setError("Failed to delete location.")
        }
    }

    const canSave = newLabel.trim() && newLocation && (
        newLocation.latitude != null || (newLocation.city && newLocation.state) || newLocation.zip_code
    )

    async function handleAddLocation() {
        if (!canSave || !newLocation) return

        setIsSaving(true)
        try {
            const created = await api.createLocation({
                label: newLabel.trim(),
                city: newLocation.city || undefined,
                state: newLocation.state || undefined,
                zip_code: newLocation.zip_code || undefined,
                latitude: newLocation.latitude ?? undefined,
                longitude: newLocation.longitude ?? undefined,
            })
            setLocations((prev) => [...prev, created])
            setNewLabel("")
            setNewLocation(null)
            setShowAddForm(false)

            // Select the newly created location
            setActiveLocation(created)
            setListExpanded(false)
            loadWeather(created)
        } catch {
            setError("Failed to save location.")
        } finally {
            setIsSaving(false)
        }
    }

    if (isLoadingLocations) return <LoadingSpinner />

    // split today from remaining days
    const todayForecast = forecast.length > 0 ? forecast[0] : null
    const remainingForecast = forecast.slice(1)

    return (
        <div className="page-wide">
            <h1 className="heading-page">Planning</h1>

            {error && (
                <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            {/* location section */}
            <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                    <h2 className="heading-section">Saved Locations</h2>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowAddForm(!showAddForm)}
                    >
                        <Plus size={14} />
                        {showAddForm ? "Cancel" : "Add"}
                    </Button>
                </div>

                {showAddForm && (
                    <div className="card-inset flex flex-col gap-3 text-left">
                        <div className="flex flex-col gap-1.5">
                            <Label htmlFor="location-label">Label</Label>
                            <Input
                                id="location-label"
                                placeholder="e.g. Blue Ridge Parkway"
                                value={newLabel}
                                onChange={(e) => setNewLabel(e.target.value)}
                            />
                        </div>
                        <LocationInput onLocationChange={setNewLocation} />
                        <Button
                            onClick={handleAddLocation}
                            disabled={isSaving || !canSave}
                        >
                            {isSaving ? "Saving..." : "Save Location"}
                        </Button>
                    </div>
                )}

                {/* collapsed: show active location with expand button */}
                {!listExpanded && activeLocation && (
                    <button
                        type="button"
                        className="list-card border-primary bg-primary/5 hover:bg-primary/10 w-full text-left"
                        onClick={() => setListExpanded(true)}
                    >
                        <MapPin size={16} className="text-primary shrink-0" />
                        <div className="flex-1 min-w-0">
                            <p className="text-title truncate">{activeLocation.label}</p>
                            {(activeLocation.city || activeLocation.state) && (
                                <p className="text-label truncate">
                                    {[activeLocation.city, activeLocation.state].filter(Boolean).join(", ")}
                                </p>
                            )}
                        </div>
                        <ChevronDown size={16} className="text-muted-foreground shrink-0" />
                    </button>
                )}

                {/* expanded: full location list */}
                {listExpanded && (
                    <>
                        {locations.length === 0 && !showAddForm ? (
                            <div className="card-prompt">
                                <MapPin size={24} className="text-muted-foreground" />
                                <p className="text-body">
                                    No saved locations yet. Add your favorite foraging spots!
                                </p>
                            </div>
                        ) : (
                            <div className="flex flex-col gap-2">
                                {locations.map((loc) => (
                                    <div
                                        key={loc.id}
                                        className={`list-card ${
                                            activeLocation?.id === loc.id
                                                ? "border-primary bg-primary/5"
                                                : ""
                                        }`}
                                        onClick={() => handleSelectLocation(loc)}
                                    >
                                        <MapPin size={16} className="text-muted-foreground shrink-0" />
                                        <div className="flex-1 min-w-0">
                                            <p className="text-title truncate">{loc.label}</p>
                                            {(loc.city || loc.state) && (
                                                <p className="text-label truncate">
                                                    {[loc.city, loc.state].filter(Boolean).join(", ")}
                                                </p>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-1 shrink-0">
                                            <button
                                                type="button"
                                                className={`btn-icon-inline ${
                                                    loc.is_pinned
                                                        ? "text-primary"
                                                        : "hover:text-foreground"
                                                }`}
                                                onClick={(e) => { e.stopPropagation(); handlePin(loc.id) }}
                                                title={loc.is_pinned ? "Pinned" : "Pin this location"}
                                            >
                                                <Pin size={14} />
                                            </button>
                                            <button
                                                type="button"
                                                className="btn-icon-inline hover:text-destructive"
                                                onClick={(e) => { e.stopPropagation(); handleDelete(loc.id) }}
                                                title="Delete"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* weather content */}
            {isLoadingWeather && <LoadingSpinner />}

            {/* featured card */}
            {current && todayForecast && (
                <div className="card-inset p-5 text-left">
                    <p className="text-label mb-3">Today</p>
                    <div className="flex items-start gap-4">
                        <WeatherIcon forecast={current.short_forecast} size={48} className="text-primary shrink-0 mt-1" />
                        <div className="flex-1 min-w-0">
                            <p className="heading-page">
                                {current.temperature}°{current.temperature_unit}
                            </p>
                            <p className="text-body mt-0.5">{current.short_forecast}</p>
                            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-label">
                                <span>
                                    H: {todayForecast.temperature_high}° L: {todayForecast.temperature_low}°
                                </span>
                                {current.precip_probability != null && current.precip_probability > 0 && (
                                    <span className="flex items-center gap-0.5">
                                        <Droplets size={11} />
                                        {current.precip_probability}%
                                    </span>
                                )}
                                {current.wind_speed && (
                                    <span className="flex items-center gap-0.5">
                                        <Wind size={11} />
                                        {current.wind_direction} {current.wind_speed}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* remaining days */}
            {remainingForecast.length > 0 && (
                <div className="card-section bg-muted/60 divide-y divide-border/50">
                    {remainingForecast.map((day) => (
                        <div key={`${day.date}-${day.name}`} className="flex items-center gap-3 px-4 py-3">
                            <WeatherIcon forecast={day.short_forecast} size={20} className="text-muted-foreground shrink-0" />
                            <div className="flex-1 min-w-0">
                                <div className="flex items-baseline gap-2">
                                    <p className="text-title">{day.name}</p>
                                    <p className="text-label">{formatDate(day.date)}</p>
                                </div>
                                <p className="text-label truncate">{day.short_forecast}</p>
                            </div>
                            <div className="text-right shrink-0">
                                <p className="heading-section">
                                    {day.temperature_high}° / {day.temperature_low}°
                                </p>
                                {day.precip_probability != null && day.precip_probability > 0 && (
                                    <p className="text-label flex items-center gap-0.5 justify-end">
                                        <Droplets size={10} />
                                        {day.precip_probability}%
                                    </p>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}


function formatDate(dateStr: string): string {
    const [, month, day] = dateStr.split("-")
    return `${parseInt(month)}/${parseInt(day)}`
}


export default PlanningPage
