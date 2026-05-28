import {
    Sun,
    Moon,
    Cloud,
    CloudRain,
    CloudSnow,
    CloudLightning,
    CloudDrizzle,
    CloudFog,
    CloudSun,
    Snowflake,
} from "lucide-react"
import type { WeatherSnapshot } from "@/types"


interface Props {
    weather: WeatherSnapshot
}


function WeatherIcon({ forecast, size, className }: { forecast: string | null; size: number; className?: string }) {
    if (!forecast) return <Cloud size={size} className={className} />

    const f = forecast.toLowerCase()

    if (f.includes("thunder") || f.includes("lightning")) return <CloudLightning size={size} className={className} />
    if (f.includes("snow") || f.includes("blizzard")) return <CloudSnow size={size} className={className} />
    if (f.includes("sleet") || f.includes("ice") || f.includes("freezing")) return <Snowflake size={size} className={className} />
    if (f.includes("fog") || f.includes("mist") || f.includes("haze")) return <CloudFog size={size} className={className} />
    if (f.includes("drizzle")) return <CloudDrizzle size={size} className={className} />
    if (f.includes("rain") || f.includes("shower")) return <CloudRain size={size} className={className} />
    if (f.includes("partly") || f.includes("mostly sunny")) return <CloudSun size={size} className={className} />
    if (f.includes("sunny") || f.includes("clear")) return <Sun size={size} className={className} />
    if (f.includes("night") || f.includes("overnight")) return <Moon size={size} className={className} />
    if (f.includes("cloud") || f.includes("overcast")) return <Cloud size={size} className={className} />

    return <Cloud size={size} className={className} />
}


function WeatherPanel({ weather }: Props) {
    const parts = [
        `${weather.temperature}°${weather.temperature_unit}`,
        weather.short_forecast,
        weather.precip_probability != null ? `${weather.precip_probability}% precip` : null,
    ].filter(Boolean)

    return (
        <div className="card-inset flex items-center gap-3 text-left">
            <WeatherIcon forecast={weather.short_forecast} size={20} className="text-muted-foreground shrink-0" />
            <div>
                <p className="text-label">Conditions when found</p>
                <p className="text-title">{parts.join(" · ")}</p>
            </div>
        </div>
    )
}

export { WeatherIcon }
export default WeatherPanel
