import { useState } from "react"
import { Link } from "react-router"
import { Camera, ShieldCheck, BookOpen, ChevronDown, ExternalLink } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from "@/components/ui/collapsible"
import heroImage from "@/assets/blue-ridge-mnts.jpg"
import appalachiaMap from "@/assets/appalachia-map.jpg"


function HomePage() {
    const [mapOpen, setMapOpen] = useState(false)

    return (

        <div className="page-hero">
            
            {/* Hero image */}
            <div className="card-hero">
                <img
                    src={heroImage}
                    alt="Blue Ridge Mountains in autumn"
                    className="w-full aspect-video object-cover"
                />
            </div>

            <div className="hero-content">
                <h1 className="heading-hero">
                forager <span className="font-extralight text-muted-foreground">/ appalachia</span>
                </h1>
                
                <p className="text-hero max-w-100">
                    Every trail has a secret. Snap a photo and discover the wild kitchen hidden in the hills.
                </p>

                <Button asChild size="lg" className="px-10 rounded-2xl w-full max-w-xs mt-2 transition-all hover:scale-[1.02]">
                    <Link to="/identify">Start Exploring</Link>
                </Button>
            </div>

            {/* About the app */}
            <div className="card-inset flex flex-col divide-y divide-border/50 text-left">
                <Feature
                    icon={Camera}
                    title="Instant Identification"
                    description="Wondering what that is? Snap a photo to instantly identify wild plants and fungi across 100+ Appalachian species."
                />
                <Feature
                    icon={ShieldCheck}
                    title="Safety Information"
                    description="Forage with confidence. Access clear safety guides and warnings so you can explore the woods without the worry."
                />
                <Feature
                    icon={BookOpen}
                    title="Personal Journal"
                    description="Your digital field guide. Save your secret spots and build a personal history of every wild thing you discover."
                />
            </div>

            {/* Appalachia region */}
            <div className="card-inset flex flex-col gap-3 text-left">
                <h2 className="heading-section">Discover Nature’s Wild Pantry</h2>
                <p className="text-body leading-relaxed">
                    The Appalachians stretch from New York to Georgia, forming one of the most biodiverse landscapes on Earth. 
                    Walking these trails feels like stepping into a massive, wild kitchen. You might find pungent wild ramps 
                    in a spring hollow or spot golden chanterelles tucked under an old oak tree. It is a land of endless discovery. 
                    Your next favorite find is just a few steps away.
                </p>

                <Collapsible open={mapOpen} onOpenChange={setMapOpen}>
                    <CollapsibleTrigger className="flex items-center gap-1.5 text-link">
                        <ChevronDown
                            size={16}
                            className={`transition-transform ${mapOpen ? "rotate-180" : ""}`}
                        />
                        {mapOpen ? "Hide" : "View"} region map
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                        <div className="mt-3 card-section">
                            <img
                                src={appalachiaMap}
                                alt="Map of the Appalachian region"
                                className="w-full object-contain bg-white"
                            />
                        </div>
                        <a
                            href="https://www.nps.gov/appa/planyourvisit/upload/APPA_Map.pdf"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 text-link mt-2"
                        >
                            <ExternalLink size={14} />
                            Full trail map (NPS)
                        </a>
                    </CollapsibleContent>
                </Collapsible>
            </div>

        </div>
    )
}


interface FeatureProps {
    icon: React.ComponentType<{ size?: number; className?: string }>
    title: string
    description: string
}

function Feature({ icon: Icon, title, description }: FeatureProps) {
    return (
        <div className="flex gap-3 items-start py-4 first:pt-0 last:pb-0">
            <div className="icon-container-sm shrink-0">
                <Icon size={18} className="text-primary" />
            </div>
            <div>
                <h3 className="heading-section">{title}</h3>
                <p className="text-body mt-0.5">{description}</p>
            </div>
        </div>
    )
}


export default HomePage
