import type { ForageEvent } from "@/types"
import { useAuthStore } from "@/stores/authStore"

export async function* streamForage(
    formData: FormData,
    accessToken: string | null,
): AsyncGenerator<ForageEvent> {
    const headers: HeadersInit = accessToken
        ? { Authorization: `Bearer ${accessToken}` }
        : {}

    let response = await fetch("/api/forage/stream", {
        method: "POST",
        headers,
        body: formData,
    })

    if (response.status === 401) {
        await useAuthStore.getState().refreshAccessToken()
        const freshToken = useAuthStore.getState().accessToken
        response = await fetch("/api/forage/stream", {
            method: "POST",
            headers: freshToken ? { Authorization: `Bearer ${freshToken}` } : {},
            body: formData,
        })
    }

    if (!response.ok) {
        const text = await response.text()
        const detail = (() => { try { return JSON.parse(text).detail } catch { return null } })()
        throw new Error(detail ?? text ?? `HTTP ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
        throw new Error("Response body is not readable")
    }

    const decoder = new TextDecoder()
    let buffer = ""

    try {
        while (true) {
            const { done, value } = await reader.read()
            if (done) break

            buffer += decoder.decode(value, { stream: true })

            const parts = buffer.split("\n\n")
            buffer = parts.pop() ?? ""

            for (const part of parts) {
                const event = parseSSEBlock(part)
                if (event) yield event
            }
        }

        if (buffer.trim()) {
            const event = parseSSEBlock(buffer)
            if (event) yield event
        }
    } finally {
        reader.releaseLock()
    }
}

function parseSSEBlock(block: string): ForageEvent | null {
    let eventName = ""
    let dataStr = ""

    for (const line of block.split("\n")) {
        if (line.startsWith("event: ")) {
            eventName = line.slice(7).trim()
        } else if (line.startsWith("data: ")) {
            dataStr = line.slice(6)
        }
    }

    if (!eventName || !dataStr) return null

    try {
        const data = JSON.parse(dataStr)
        return { event: eventName, data } as ForageEvent
    } catch {
        return null
    }
}
