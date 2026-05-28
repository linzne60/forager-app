import { useState } from "react"
import { Textarea } from "@/components/ui/textarea"
import { Pencil, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { api } from "@/libs/api"
import { toast } from "sonner"


interface Props {
    discoveryId: string
    initialNotes: string | null
}


function NotesPanel({ discoveryId, initialNotes }: Props) {
    const [notes, setNotes] = useState(initialNotes ?? "")
    const [isSaving, setIsSaving] = useState(false)
    const [isEditingNotes, setIsEditingNotes] = useState(false)
    const [savedNotes, setSavedNotes] = useState(initialNotes ?? "")

    async function handleSave() {
        if (!discoveryId) return
        setIsSaving(true)
        try {
            await api.updateDiscovery(discoveryId, notes)
            setSavedNotes(notes)
            setIsEditingNotes(false)
        } catch {
            toast.error("Failed to save notes.")
        } finally {
            setIsSaving(false)
        }
    }

    function handleCancel() {
        setNotes(savedNotes)
        setIsEditingNotes(false)
    }

    return (
        <div className="flex flex-col gap-3">
            {isEditingNotes ? (
                <>
                    <label htmlFor="notes" className="text-title">
                        {notes ? "Edit notes" : "Add notes"}
                    </label>
                    <Textarea
                        id="notes"
                        placeholder="Add notes about this find..."
                        className="min-h-24 bg-background"
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        rows={3}
                    />
                    <div className="flex gap-2 justify-end">
                        <Button
                            onClick={handleCancel}
                            variant="ghost"
                            size="sm"
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={handleSave}
                            disabled={isSaving || (!notes && !savedNotes)}
                            size="sm"
                        >
                            {isSaving ? "Saving..." : "Save"}
                        </Button>
                    </div>
                </>
            ) : (
                <>
                    {notes ? (
                        <>
                            <div className="flex items-center justify-between">
                                <p className="text-title">Notes</p>
                                <Button
                                    onClick={() => setIsEditingNotes(true)}
                                    variant="ghost"
                                    size="sm"
                                    className="link-muted"
                                >
                                    <Pencil size={14} />
                                    Edit
                                </Button>
                            </div>
                            <p className="text-sm text-foreground whitespace-pre-wrap">{notes}</p>
                        </>
                    ) : (
                        <Button
                            onClick={() => setIsEditingNotes(true)}
                            variant="ghost"
                            size="sm"
                            className="self-start px-0 py-2 btn-subtle"
                        >
                            <Plus size={14} />
                            Add a note
                        </Button>
                    )}
                </>
            )}
        </div>
    )
}

export default NotesPanel
