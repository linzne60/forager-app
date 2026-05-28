import { useEffect, useState } from "react"
import { useNavigate } from "react-router"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import {

    AlertDialog,
    AlertDialogAction,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { getSessionId } from "@/libs/session"
import { useAuthStore } from "@/stores/authStore"
import { useForageStore } from "@/stores/forageStore"
import UploadZone from "@/components/upload/UploadZone"
import LocationInput from "@/components/upload/LocationInput"
import LoadingSpinner from "@/components/LoadingSpinner"
import type { LocationData } from "@/types"


function IdentifyPage() {
    const navigate = useNavigate()
    const accessToken = useAuthStore((s) => s.accessToken)
    const { status, discoveryId, error: streamError, startStream, reset } = useForageStore()

    const [file, setFile] = useState<File | null>(null)
    const [location, setLocation] = useState<LocationData | null>(null)
    const [submitted, setSubmitted] = useState(false)
    const [disclaimerAccepted, setDisclaimerAccepted] = useState(
        () => localStorage.getItem("forager-disclaimer") === "true"
    )
    const [showDisclaimer, setShowDisclaimer] = useState(false)

    const isLoading = status === "streaming"

    useEffect(() => {
        reset()
    }, [reset])

    useEffect(() => {
        if (submitted && discoveryId) {
            navigate(`/discovery/${discoveryId}`)
        }
    }, [submitted, discoveryId, navigate])

    useEffect(() => {
        if (streamError) toast.error(streamError)
    }, [streamError])

    function handleAcceptDisclaimer() {
        setDisclaimerAccepted(true)
        localStorage.setItem("forager-disclaimer", "true")
        setShowDisclaimer(false)
        submitIdentification()
    }

    function handleSubmit() {
        if (!file) return

        if (!disclaimerAccepted) {
            setShowDisclaimer(true)
            return
        }

        submitIdentification()
    }

    function submitIdentification() {
        if (!file) return

        const formData = new FormData()
        formData.append("photo", file)
        formData.append("session_id", getSessionId())

        if (location?.latitude !== null && location?.latitude !== undefined) {
            formData.append("latitude", String(location.latitude))
            formData.append("longitude", String(location.longitude))
        }

        if (location?.city) formData.append("city", location.city)
        if (location?.state) formData.append("state", location.state)
        if (location?.zip_code) formData.append("zip_code", location.zip_code)

        const photoPreviewUrl = URL.createObjectURL(file)
        setSubmitted(true)
        startStream(formData, accessToken, photoPreviewUrl)
    }

    return (
        <div className="form-page">
            <div className="text-center">
                <h1 className="heading-page">Identify a Species</h1>
                <p className="text-body mt-0.5">
                    Upload a photo and we'll tell you what it is.
                </p>
            </div>
            <UploadZone onFileSelect={setFile} />

            <div className="card-inset flex flex-col gap-4">
                <p className="text-title">Location <span className="text-muted-foreground font-normal">(optional)</span></p>
                <LocationInput onLocationChange={setLocation} />
            </div>

            <Button
                onClick={handleSubmit}
                disabled={!file || isLoading}
                size="lg" className="w-full"
            >
                {isLoading ? "Identifying..." : "Identify"}
            </Button>

            <AlertDialog open={showDisclaimer} onOpenChange={setShowDisclaimer}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Before you continue</AlertDialogTitle>
                        <AlertDialogDescription>
                            Forager is for educational purposes only. Always verify with a qualified expert before consuming anything found in the wild.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogAction onClick={handleAcceptDisclaimer}>
                            I understand
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>


            {isLoading && <LoadingSpinner />}
        </div>
    )
}

export default IdentifyPage
