import { useEffect, useState } from "react"
import { useParams, useNavigate, Link } from "react-router"
import { Trash2, ChevronLeft, Cherry } from "lucide-react"
import { api } from "@/libs/api"
import { useAuth } from "@/hooks/useAuth"
import { useForageStore } from "@/stores/forageStore"
import { Button } from "@/components/ui/button"
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import LoadingSpinner from "@/components/LoadingSpinner"
import HeroImage from "@/components/results/HeroImage"
import ResultsPanel from "@/components/results/ResultsPanel"
import NutritionPanel from "@/components/results/NutritionPanel"
import WeatherPanel from "@/components/results/WeatherPanel"
import type { DiscoveryResponse, SafetyDetails } from "@/types"
import SectionHeader from "@/components/common/SectionHeader"
import NotesPanel from "@/components/results/NotesPanel"


function Skeleton({ className = "", label }: { className?: string; label?: string }) {
    return (
        <div className={`animate-pulse rounded-xl bg-muted flex items-center justify-center gap-2 ${className}`}>
            {label && <span className="text-body">{label}</span>}
        </div>
    )
}


function DiscoveryDetailPage() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const { isAuthenticated, user } = useAuth()

    // live stream state
    const {
        status: streamStatus,
        discoveryId,
        photoPreviewUrl,
        classifyData,
        safetyStaticData,
        nutritionData,
        weatherData,
    } = useForageStore()

    const isLive = id === discoveryId && (streamStatus === "streaming" || streamStatus === "complete")

    // replay state (fetched from API)
    const [discovery, setDiscovery] = useState<DiscoveryResponse | null>(null)
    const [isLoading, setIsLoading] = useState(!isLive)
    const [error, setError] = useState<string | null>(null)

    const isOwner = isAuthenticated && (
        isLive || discovery?.user_id === user?.id
    )

    // fetch from API in replay mode
    useEffect(() => {
        if (isLive || !id) return

        async function fetchDiscovery() {
            try {
                const data = await api.getDiscovery(id!)
                setDiscovery(data)
            } catch {
                setError("Discovery not found.")
            } finally {
                setIsLoading(false)
            }
        }
        fetchDiscovery()
    }, [id, isLive])

    async function handleDelete() {
        if (!id) return
        try {
            await api.deleteDiscovery(id)
            navigate("/journal")
        } catch {
            setError("Failed to delete. Please try again.")
        }
    }

    // replay mode: loading/error
    if (!isLive && isLoading) return <LoadingSpinner />
    if (!isLive && (error || !discovery)) return <p className="text-error p-4">{error ?? "Not found."}</p>

    const photoUrl = isLive ? photoPreviewUrl : discovery!.photo_url
    const heatmapUrl = isLive ? (classifyData?.heatmap_url ?? null) : discovery!.heatmap_url

    const safetyDetails: SafetyDetails | null = isLive
        ? safetyStaticData ?? null
        : discovery!.safety_details
            ? { ...discovery!.safety_details, safety_verdict: discovery!.safety_verdict }
            : null

    const speciesName = isLive
        ? classifyData?.predictions[0]?.species ?? null
        : discovery!.species_prediction?.common_name ?? null

    const nutritionInfo = isLive
        ? nutritionData?.nutrition_info ?? null
        : discovery!.nutrition_info

    const weatherContext = isLive
        ? weatherData?.weather_context ?? null
        : discovery!.weather_context

    const isStreaming = isLive && streamStatus === "streaming"

    return (
        <div className="page-wide">
            <Link
                to="/journal"
                className="link-back -mb-2"
            >
                <ChevronLeft size={16} />
                Journal
            </Link>

            <HeroImage
                heatmapUrl={heatmapUrl}
                photoUrl={photoUrl}
            />

            {safetyDetails ? (
                <ResultsPanel
                    safety={safetyDetails}
                    speciesName={speciesName}
                />
            ) : isStreaming ? (
                <Skeleton className="h-24" label="Analyzing..." />
            ) : null}

            {isOwner && (
                <>  
                    {weatherContext ? (
                        <WeatherPanel weather={weatherContext} />
                    ) : isStreaming ? (
                        <Skeleton className="h-28" label="Checking weather..." />
                    ) : null}

                    {nutritionInfo ? (
                        <div className="card-section bg-muted/60">
                            <SectionHeader icon={Cherry} label="Nutrition Details" variant="muted"/>

                            <div className="card-body pb-4">                                                                                         
                                <NutritionPanel nutrition={nutritionInfo} bare />
                            </div> 
                        </div>
                    ) : isStreaming && safetyDetails?.confidence_tier === "strong_match" ? (
                        <Skeleton className="h-40" label="Loading nutrition..." />
                    ) : null}

                    {/* Notes — available once discovery is persisted */}
                    {(!isLive || streamStatus === "complete") && (
                        <NotesPanel discoveryId={id!} initialNotes={discovery?.user_notes ?? null}/>
                    )}
                </>
            )}

            {/* guest prompt */}
            {!isAuthenticated && !isStreaming && (
                <div className="card-prompt">
                    <p className="text-title">Want the full picture?</p>
                    <p className="text-body max-w-xs">
                        Sign in to see nutrition details, weather context, and save discoveries to your journal.
                    </p>
                    <Button asChild className="px-6">
                        <Link to="/login">Sign in</Link>
                    </Button>
                </div>
            )}

            {/* disclaimer */}
            {!isStreaming && safetyDetails && (
                <p className="text-label text-center px-4">
                    Forager is for educational purposes only. Always verify with a qualified expert before consuming anything found in the wild.
                </p>
            )}

            {/* delete discovery */}
            {isOwner && streamStatus !== "streaming" && (
                <AlertDialog>
                    <AlertDialogTrigger asChild>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="self-center btn-subtle"
                        >
                            <Trash2 size={14} />
                            Delete this discovery
                        </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent size="sm">
                        <AlertDialogHeader>
                            <AlertDialogTitle>Delete this discovery?</AlertDialogTitle>
                            <AlertDialogDescription>
                                This can't be undone.
                            </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                            <AlertDialogCancel variant="ghost">Cancel</AlertDialogCancel>
                            <AlertDialogAction variant="destructive" onClick={handleDelete}>Delete</AlertDialogAction>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialog>
            )}
        </div>
    )
}

export default DiscoveryDetailPage
