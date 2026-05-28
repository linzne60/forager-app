import { useState } from "react"
import { Button } from "@/components/ui/button"


interface Props {
    heatmapUrl: string | null
    photoUrl: string | null
}


function HeroImage({ heatmapUrl, photoUrl }: Props) {
    const [showHeatmap, setShowHeatmap] = useState(false)

    return (
        <div className="flex flex-col gap-4">
            {(photoUrl || heatmapUrl) && (
                <div className="flex flex-col gap-3">
                    <div className="card-section">
                        <img
                            src={showHeatmap && heatmapUrl ? heatmapUrl : photoUrl ?? ""}
                            className="w-full aspect-4/3 object-cover bg-muted"
                        />
                    </div>
                    {heatmapUrl && (
                        <Button
                            type="button"
                            variant="outline"
                            size="md" className="w-full"
                            onClick={() => setShowHeatmap(!showHeatmap)}
                        >
                            {showHeatmap ? "Show original photo" : "Show what the model saw"}
                        </Button>
                    )}
                </div>
            )}
        </div>
    )
}

export default HeroImage
