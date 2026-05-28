import { useState } from "react"
import { MapPin } from "lucide-react"
import { toast } from "sonner"
import { Input } from "@/components/ui/input"
import type { LocationData } from "@/types"


interface Props {
    onLocationChange: (location: LocationData) => void
}


function LocationInput({ onLocationChange }: Props) {
    const [status, setStatus] = useState<"idle" | "detecting" | "detected">("idle")
    const [city, setCity] = useState("")
    const [state, setState] = useState("")
    const [zipCode, setZipCode] = useState("")

    function handleDetect() {
        setStatus("detecting")
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                setStatus("detected")
                onLocationChange({
                    latitude: pos.coords.latitude,
                    longitude: pos.coords.longitude,
                    city: "",
                    state: "",
                    zip_code: "",
                })
            },
            (err) => {
                setStatus("idle")
                if (err.code === 1) {
                    toast.error("Location permission denied. Check your browser settings.")
                } else if (err.code === 2) {
                    toast.error("Could not determine location. Try again.")
                } else if (err.code === 3) {
                    toast.error("Location request timed out. Try again.")
                } else {
                    toast.error(err.message)
                }
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 300_000 }
        )
    }

    function handleManualChange(newCity: string, newState: string, newZip: string) {
        setCity(newCity)
        setState(newState)
        setZipCode(newZip)
        onLocationChange({ latitude: null, longitude: null, city: newCity, state: newState, zip_code: newZip })
    }

    return (
        <div className="flex flex-col gap-3">
            <button
                type="button"
                onClick={handleDetect}
                disabled={status === "detecting"}
                className="field-action"
            >
                <MapPin size={18} className="text-primary shrink-0" />
                <span className="font-medium">
                    {status === "detecting" ? "Detecting..." : status === "detected" ? "Location detected" : "Use my location"}
                </span>
                {status === "detected" && (
                    <span className="ml-auto text-label">GPS</span>
                )}
            </button>

            <p className="form-divider">or enter manually</p>

            <div className="flex gap-2">
                <Input
                    placeholder="City"
                    className="flex-1"
                    value={city}
                    onChange={(e) => handleManualChange(e.target.value, state, zipCode)}
                />
                <Input
                    placeholder="State"
                    className="w-20"
                    value={state}
                    onChange={(e) => handleManualChange(city, e.target.value, zipCode)}
                />
            </div>

            <p className="form-divider">or</p>

            <Input
                placeholder="Zip code"
                value={zipCode}
                onChange={(e) => handleManualChange(city, state, e.target.value)}
            />
        </div>
    )
}

export default LocationInput
