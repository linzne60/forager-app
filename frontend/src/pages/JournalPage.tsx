import { useEffect, useRef, useState } from "react"
import { Link } from "react-router"
import { Leaf } from "lucide-react"
import { api } from "@/libs/api"
import DiscoveryCard from "@/components/journal/DiscoveryCard"
import JournalFilters from "@/components/journal/JournalFilters"
import LoadingSpinner from "@/components/LoadingSpinner"
import { Button } from "@/components/ui/button"
import type { DiscoveryListItem, DiscoveryQueryParams } from "@/types"


function JournalPage() {
    const [discoveries, setDiscoveries] = useState<DiscoveryListItem[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [hasMore, setHasMore] = useState(true)
    const [filters, setFilters] = useState<DiscoveryQueryParams>({})

    const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
    const limit = 20

    async function fetchDiscoveries(params: DiscoveryQueryParams, cursor?: string) {
        setIsLoading(true)

        try {
            const data = await api.getDiscoveries({ ...params, limit, cursor })

            if (!cursor) {
                setDiscoveries(data)
            } else {
                setDiscoveries((prev) => [...prev, ...data])
            }
            setHasMore(data.length === limit)
        } catch {
            setError("Failed to load Journal. Please try again.")
        } finally {
            setIsLoading(false)
        }
    }

    // fetch on mount and whenever filters change (debounced for text search)
    useEffect(() => {
        if (debounceTimer.current) {
            clearTimeout(debounceTimer.current)
        }

        debounceTimer.current = setTimeout(() => {
            fetchDiscoveries(filters)
        }, filters.q ? 300 : 0)

        return () => {
            if (debounceTimer.current) {
                clearTimeout(debounceTimer.current)
            }
        }
    }, [filters])

    async function handleDelete(id: string) {
        try {
            await api.deleteDiscovery(id)
            setDiscoveries((prev) => prev.filter((d) => d.id !== id))
        } catch {
            setError("Failed to delete. Please try again.")
        }
    }

    function handleLoadMore() {
        const lastItem = discoveries[discoveries.length - 1]
        if (lastItem?.discovered_at) {
            fetchDiscoveries(filters, lastItem.discovered_at)
        }
    }

    function handleFiltersChange(next: DiscoveryQueryParams) {
        setFilters(next)
    }

    const showEmptyState = !isLoading && discoveries.length === 0
    const hasActiveFilters = !!filters.q

    return (
        <div className="page-wide">
            <div className="pt-4 text-center">
                <h1 className="heading-page">Journal</h1>
                    <p className="text-body mt-0.5">
                        Revisit your observations!
                    </p>
            </div>

            <div className="sticky-bar">
                <JournalFilters filters={filters} onFiltersChange={handleFiltersChange} />
            </div>

            {isLoading && discoveries.length === 0 && <LoadingSpinner />}

            {error && <p className="text-error">{error}</p>}

            {showEmptyState && (
                hasActiveFilters ? (
                    <div className="empty-state">
                        <p className="text-body">No discoveries match your filters.</p>
                        <Button
                            variant="outline"
                            onClick={() => setFilters({})}
                        >
                            Clear filters
                        </Button>
                    </div>
                ) : (
                    <div className="empty-state py-16">
                        <div className="icon-container">
                            <Leaf size={28} className="text-primary" />
                        </div>
                        <div>
                            <p className="heading-section text-lg">No discoveries yet</p>
                            <p className="text-body mt-1">
                                Head outside and identify your first plant!
                            </p>
                        </div>
                        <Button asChild className="px-6">
                            <Link to="/identify">Start Foraging</Link>
                        </Button>
                    </div>
                )
            )}

            {discoveries.length > 0 && (
                <>
                    <div className="flex flex-col gap-6">
                        {discoveries.map((d) => (
                            <DiscoveryCard key={d.id} discovery={d} onDelete={handleDelete} />
                        ))}
                    </div>
                    {hasMore && (
                        <Button
                            variant="outline"
                            size="md" className="w-full"
                            onClick={handleLoadMore}
                            disabled={isLoading}
                        >
                            {isLoading ? "Loading..." : "Load more"}
                        </Button>
                    )}
                </>
            )}
        </div>
    )
}

export default JournalPage
