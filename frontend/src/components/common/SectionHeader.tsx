import type { LucideIcon } from "lucide-react"

interface Props {
    icon: LucideIcon
    label: string
    variant?: "wood" | "muted" | "safe" | "caution" | "danger"
}
    
function SectionHeader({ icon, label, variant }: Props) {
    
    const Icon = icon
    const variantStyles = {
        wood:   { bg: "bg-wood-tint",   text: "text-wood" },                                                                     
        muted:  { bg: "bg-muted",       text: "text-foreground" },
        safe:   { bg: "bg-safe-tint",   text: "text-safe" },                                                                     
        caution:{ bg: "bg-caution-tint",text: "text-caution" },                                                                  
        danger: { bg: "bg-danger-tint", text: "text-danger" },                                                                   
    } 
    const style = variantStyles[variant ?? "muted"]
    
    return (
        <div className={`section-header ${style.bg} ${style.text}`}>
            <Icon size={16} className="shrink-0" />                                                                          
            <p className="text-title">{label}</p>                                                                
        </div>  
    )
}

export default SectionHeader
    