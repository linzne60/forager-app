import { create } from "zustand"
import { streamForage } from "@/libs/sse"
import type {
    ClassifyEventData,
    SafetyDetails,
    NutritionEventData,
    WeatherEventData,
} from "@/types"

type ForageStatus = "idle" | "streaming" | "complete" | "error"

interface ForageState {
    status: ForageStatus
    discoveryId: string | null
    photoPreviewUrl: string | null

    classifyData: ClassifyEventData | null
    safetyStaticData: SafetyDetails | null
    nutritionData: NutritionEventData | null
    weatherData: WeatherEventData | null

    error: string | null

    startStream: (formData: FormData, accessToken: string | null, photoPreviewUrl: string) => Promise<void>
    reset: () => void
}

const initialState = {
    status: "idle" as ForageStatus,
    discoveryId: null,
    photoPreviewUrl: null,
    classifyData: null,
    safetyStaticData: null,
    nutritionData: null,
    weatherData: null,
    error: null,
}

export const useForageStore = create<ForageState>()((set, get) => ({
    ...initialState,

    reset: () => {
        const { photoPreviewUrl } = get()
        if (photoPreviewUrl) URL.revokeObjectURL(photoPreviewUrl)
        set(initialState)
    },

    startStream: async (formData, accessToken, photoPreviewUrl) => {
        set({ ...initialState, status: "streaming", photoPreviewUrl })

        try {
            for await (const event of streamForage(formData, accessToken)) {
                switch (event.event) {
                    case "classify":
                        set({
                            discoveryId: event.data.discovery_id,
                            classifyData: event.data,
                        })
                        break

                    case "safety_static":
                        set({ safetyStaticData: event.data })
                        break

                    case "nutrition":
                        set({ nutritionData: event.data })
                        break

                    case "weather":
                        set({ weatherData: event.data })
                        break

                    case "complete":
                        set({ status: "complete" })
                        break

                    case "error":
                        set({ status: "error", error: event.data.message })
                        break
                }
            }
        } catch (err) {
            const message = err instanceof Error ? err.message : "Stream failed"
            set({ status: "error", error: message })
        }
    },
}))
