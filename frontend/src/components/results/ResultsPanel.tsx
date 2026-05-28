import { ShieldCheck, ShieldAlert, ShieldX, CircleCheck, ChefHat, ScanEye, ChevronRight } from "lucide-react"
import SectionHeader from "../common/SectionHeader"
import type { SafetyDetails } from "@/types"


interface Props {
    safety: SafetyDetails
    speciesName: string | null
}


const verdictConfig = {
    safe: {
        icon: ShieldCheck,
        label: "Safe to forage",
        color: "text-safe",
        bg: "bg-safe-tint",
        border: "border-safe/30",
    },
    caution: {
        icon: ShieldAlert,
        label: "Use caution",
        color: "text-caution",
        bg: "bg-caution-tint",
        border: "border-caution/30",
    },
    danger: {
        icon: ShieldX,
        label: "Do not consume",
        color: "text-danger",
        bg: "bg-danger-tint",
        border: "border-danger/30",
    },
}


function formatSpeciesName(name: string): string {
    return name.replace(/_/g, " ")
}


function ResultsPanel({ safety, speciesName }: Props) {
    const verdict = safety.safety_verdict as keyof typeof verdictConfig
    const style = verdictConfig[verdict] ?? verdictConfig.caution
    const Icon = style.icon
    const tier = safety.confidence_tier
    const info = safety.safety_info

    return (
        <div className="flex flex-col gap-5 text-left">

            {/* species id */}
            {tier === "strong_match" && speciesName && (
                <div className="card-section">
                    <SectionHeader icon={CircleCheck} label="Species Identified" variant="wood"/>
                    <div className="card-body py-4 flex flex-col gap-1.5">
                        <h2 className="heading-content capitalize">
                            {formatSpeciesName(speciesName)}
                        </h2>
                        {info?.edibility && (
                            <p className="text-body capitalize inline-flex items-center gap-1.5">
                                Verdict <ChevronRight size={16}/> {Array.isArray(info.edibility)
                                    ? info.edibility.map(formatSpeciesName).join(" · ")
                                    : formatSpeciesName(info.edibility)}
                            </p>
                        )}
                    </div>
                </div>
            )}

            {/* safety context */}
            <div className="card-section">
                <SectionHeader icon={Icon} label={style.label} variant={verdict}/>
                <p className="text-body card-body">{safety.warning_message}</p>
            </div>

            {/* preparation info*/}
            {tier === "strong_match" && info?.preparation && (
                <div className="card-section">
                    <SectionHeader icon={ChefHat} label="Preparation" variant="muted"/>
                    {typeof info.preparation === "string" ? (
                        <p className="text-body card-body">{info.preparation}</p>
                        ) : (
                            <div className="card-body py-4 flex flex-col gap-1.5">
                                {info.preparation.edible && (
                                    <div>
                                        <p className="text-title">Edible Use</p>
                                        <p className="text-body">{info.preparation.edible}</p>
                                    </div>
                                )}

                                {info.preparation.medicinal && (
                                    <div>
                                        <p className="text-title">Medicinal Use</p>
                                        <p className="text-body">{info.preparation.medicinal}</p>
                                    </div>
                                )}    
                            </div>
                        )}
                </div>
            )}

            {/* candidates for possible_match and uncertain tiers */}
            {(tier === "possible_match" || tier === "uncertain") && safety.candidates && (
                <div className="card-section">
                    <SectionHeader icon={ScanEye} label="Possible Matches" variant="muted"/>
                    {safety.candidates.map((c) => (
                        <div key={c.species} className="flex items-center justify-between card-body bg-muted/60 border border-border/50">
                            <span className="text-title capitalize">{formatSpeciesName(c.species)}</span>
                            <div className="flex items-center gap-2 text-xs">
                                <span className="text-muted-foreground">{Math.round(c.confidence * 100)}%</span>
                                <span className={
                                    c.safety_verdict === "safe" ? "text-safe"
                                    : c.safety_verdict === "danger" ? "text-danger"
                                    : "text-caution"
                                }>
                                    {c.safety_verdict}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default ResultsPanel
