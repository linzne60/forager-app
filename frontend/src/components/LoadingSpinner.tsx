import { Loader2 } from "lucide-react"

function LoadingSpinner() {

    return (
        <div className="flex items-center justify-center p-4">
            <Loader2 className="animate-spin text-primary" size={32} />
        </div>
    )
}

export default LoadingSpinner