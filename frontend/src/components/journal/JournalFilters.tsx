import { useState } from "react"
import { Search, SlidersHorizontal } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet"
import type { DiscoveryQueryParams } from "@/types"


interface Props {
    filters: DiscoveryQueryParams
    onFiltersChange: (filters: DiscoveryQueryParams) => void
}


function JournalFilters({ filters, onFiltersChange }: Props) {
    const [open, setOpen] = useState(false)
    const [localFrom, setLocalFrom] = useState(filters.date_from ?? "")
    const [localTo, setLocalTo] = useState(filters.date_to ?? "")

    const hasDateFilter = !!filters.date_from || !!filters.date_to

    function handleOpenChange(isOpen: boolean) {
        if (isOpen) {
            setLocalFrom(filters.date_from ?? "")
            setLocalTo(filters.date_to ?? "")
        }
        setOpen(isOpen)
    }

    function handleApply() {
        onFiltersChange({
            ...filters,
            date_from: localFrom || undefined,
            date_to: localTo || undefined,
        })
        setOpen(false)
    }

    function handleClear() {
        setLocalFrom("")
        setLocalTo("")
        onFiltersChange({
            ...filters,
            date_from: undefined,
            date_to: undefined,
        })
        setOpen(false)
    }

    return (
        <div className="flex gap-2">
            <div className="relative flex-1">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <Input
                    placeholder="Search species, location, notes..."
                    className="pl-9"
                    value={filters.q ?? ""}
                    onChange={(e) => onFiltersChange({ ...filters, q: e.target.value || undefined })}
                />
            </div>

            <Sheet open={open} onOpenChange={handleOpenChange}>
                <SheetTrigger asChild>
                    <Button
                        variant="outline"
                        size="icon-md"
                        className={`shrink-0 ${hasDateFilter ? "border-primary text-primary" : ""}`}
                    >
                        <SlidersHorizontal size={18} />
                    </Button>
                </SheetTrigger>
                <SheetContent side="bottom" className="rounded-t-2xl px-6 pb-10">
                    <SheetHeader>
                        <SheetTitle className="text-lg font-light">Date range</SheetTitle>
                        <SheetDescription className="sr-only">Filter by date</SheetDescription>
                    </SheetHeader>

                    <div className="flex items-center gap-3 pt-4">
                        <Input
                            type="date"
                            className="flex-1"
                            value={localFrom}
                            onChange={(e) => setLocalFrom(e.target.value)}
                        />
                        <span className="text-body">to</span>
                        <Input
                            type="date"
                            className="flex-1"
                            value={localTo}
                            onChange={(e) => setLocalTo(e.target.value)}
                        />
                    </div>

                    <div className="flex gap-2 pt-6">
                        <Button
                            variant="ghost"
                            className="flex-1"
                            onClick={handleClear}
                        >
                            Clear
                        </Button>
                        <Button
                            className="flex-1"
                            onClick={handleApply}
                        >
                            Apply
                        </Button>
                    </div>
                </SheetContent>
            </Sheet>
        </div>
    )
}

export default JournalFilters
