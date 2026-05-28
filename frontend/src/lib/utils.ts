import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function verdictTextColor(verdict: string | null) {
    switch (verdict) {
        case "safe": return "text-safe"
        case "caution": return "text-caution"
        case "danger": return "text-danger"
        default: return "text-muted-foreground"
    }
}

export function verdictStrokeColor(verdict: string | null) {
    switch (verdict) {
        case "safe": return "stroke-safe"
        case "caution": return "stroke-caution"
        case "danger": return "stroke-danger"
        default: return "stroke-primary"
    }
}
