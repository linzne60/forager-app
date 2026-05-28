import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { NutritionInfo } from "@/types"

interface Props {
    nutrition: NutritionInfo | null
    bare?: boolean
}


function NutritionPanel({ nutrition, bare = false }: Props) {
    if (!nutrition) return null

    const macros = [
        { label: "Calories", value: nutrition.calories_per_100g, unit: "/100g" },
        { label: "Protein", value: nutrition.protein_g, unit: "g" },
        { label: "Fat", value: nutrition.fat_g, unit: "g" },
        { label: "Carbs", value: nutrition.carbs_g, unit: "g" },
        { label: "Fiber", value: nutrition.fiber_g, unit: "g" },
    ].filter((m) => m.value !== null)

    const content = (
        <div className="flex flex-col gap-4 text-left">

            {/* edible parts */}
            {nutrition.edible_parts.length > 0 && (
                <div>
                    <p className="text-label">Edible parts</p>
                    <p className="text-value text-md mt-0.5 capitalize">
                        {nutrition.edible_parts.join(", ")}
                    </p>
                </div>
            )}

            {/* macros */}
            {macros.length > 0 && (
                <div className="grid grid-cols-3 gap-2">
                    {macros.map((m) => (
                        <div key={m.label} className="stat-chip">
                            <p className="text-label">{m.label}</p>
                            <p className="text-value mt-0.5">
                                {m.value}{m.unit}
                            </p>
                        </div>
                    ))}
                </div>
            )}

            {/* notable nutrients */}
            {nutrition.notable_nutrients.length > 0 && (
                <div>
                    <p className="text-label mb-2">Notable nutrients</p>
                    <div className="flex flex-col gap-1.5 text-sm">
                        {nutrition.notable_nutrients.map((n) => (
                            <div key={n.nutrient} className="flex justify-between">
                                <span>{n.nutrient}</span>
                                <span className="text-muted-foreground">
                                    {n.amount}{n.percent_dv !== null ? ` (${n.percent_dv}% DV)` : ""}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {nutrition.notes && (
                <p className="text-body">{nutrition.notes}</p>
            )}

            <p className="text-label">
                Source: {nutrition.source}
            </p>
        </div>
    )

    if (bare) return content

    return (
        <Card>
            <CardHeader>
                <CardTitle>Nutrition Info</CardTitle>
            </CardHeader>
            <CardContent>{content}</CardContent>
        </Card>
    )
}

export default NutritionPanel
