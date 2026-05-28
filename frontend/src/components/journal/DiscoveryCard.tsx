import { useRef, useState } from "react"
import { Link } from "react-router"
import { Trash2, ShieldCheck, ShieldAlert, ShieldX } from "lucide-react"
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog"

import type { DiscoveryListItem } from "@/types"


interface Props {
    discovery: DiscoveryListItem
    onDelete?: (id: string) => void
}


function DiscoveryCard({ discovery, onDelete }: Props) {
    const [offsetX, setOffsetX] = useState(0)
    const [confirmOpen, setConfirmOpen] = useState(false)
    const startX = useRef(0)
    const startY = useRef(0)
    const swiping = useRef(false)
    const DELETE_THRESHOLD = 80

    function handleTouchStart(e: React.TouchEvent) {
        startX.current = e.touches[0].clientX
        startY.current = e.touches[0].clientY
        swiping.current = false
    }

    function handleTouchMove(e: React.TouchEvent) {
        const dx = e.touches[0].clientX - startX.current
        const dy = e.touches[0].clientY - startY.current

        if (!swiping.current && Math.abs(dy) > Math.abs(dx)) return
        swiping.current = true

        const clamped = Math.max(-DELETE_THRESHOLD, Math.min(0, dx))
        setOffsetX(clamped)
    }

    function handleTouchEnd() {
        if (Math.abs(offsetX) >= DELETE_THRESHOLD) {
            setOffsetX(-DELETE_THRESHOLD)
        } else {
            setOffsetX(0)
        }
    }

    const date = discovery.discovered_at
        ? new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" })
            .format(new Date(discovery.discovered_at))
        : null

    const location = [discovery.location?.city, discovery.location?.state]
        .filter(Boolean)
        .join(", ") || discovery.location?.zip_code || ""

    const meta = [date, location].filter(Boolean).join(" · ")


    return (
        <>
            <div className="relative overflow-hidden rounded-xl">
                {onDelete && (
                    <button
                        className="absolute inset-y-0 right-0 w-20 bg-destructive flex items-center justify-center text-white"
                        onClick={() => setConfirmOpen(true)}
                    >
                        <Trash2 size={20} />
                    </button>
                )}

                {/* swipeable card */}
                <Link
                    to={`/discovery/${discovery.id}`}
                    className="relative block bg-background transition-transform"
                    style={{ transform: `translateX(${offsetX}px)` }}
                    onTouchStart={onDelete ? handleTouchStart : undefined}
                    onTouchMove={onDelete ? handleTouchMove : undefined}
                    onTouchEnd={onDelete ? handleTouchEnd : undefined}
                    onClick={(e) => {
                        if (Math.abs(offsetX) > 4) {
                            e.preventDefault()
                            setOffsetX(0)
                        }
                    }}
                >
                    {discovery.photo_url && (
                        <img
                            src={discovery.photo_url}
                            alt={discovery.species_prediction?.common_name ?? "plant"}
                            className="w-full aspect-3/2 object-cover"
                        />
                    )}

                    <div className="flex flex-col items-center gap-1 px-2 pt-3 pb-2">
                        <h3 className="heading-section capitalize leading-tight truncate max-w-full flex items-center gap-1.5">
                            {discovery.species_prediction?.common_name?.replace(/_/g, " ") ?? "Unidentified"}
                            {discovery.safety_verdict === "safe" ? (
                                <ShieldCheck size={16} className="text-safe shrink-0" />
                            ) : discovery.safety_verdict === "danger" ? (
                                <ShieldX size={16} className="text-danger shrink-0" />
                            ) : discovery.safety_verdict && discovery.safety_verdict !== "unknown" ? (
                                <ShieldAlert size={16} className="text-caution shrink-0" />
                            ) : null}
                        </h3>
                        {meta && (
                            <p className="text-label">{meta}</p>
                        )}
                    </div>
                </Link>
            </div>

            {onDelete && (
                <AlertDialog open={confirmOpen} onOpenChange={(open) => {
                    setConfirmOpen(open)
                    if (!open) setOffsetX(0)
                }}>
                    <AlertDialogContent size="sm">
                        <AlertDialogHeader>
                            <AlertDialogTitle>Delete this discovery?</AlertDialogTitle>
                            <AlertDialogDescription>
                                This can't be undone.
                            </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                            <AlertDialogCancel variant="ghost">Cancel</AlertDialogCancel>
                            <AlertDialogAction
                                variant="destructive"
                                onClick={() => onDelete(discovery.id)}
                            >
                                Delete
                            </AlertDialogAction>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialog>
            )}
        </>
    )
}

export default DiscoveryCard
