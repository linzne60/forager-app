import { useRef, useState } from "react"
import { ImagePlus } from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"


interface Props {
    onFileSelect: (file: File) => void
}

function UploadZone({ onFileSelect }: Props) {
    const [preview, setPreview] = useState<string | null>(null)
    const inputRef = useRef<HTMLInputElement>(null)

    const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"]

    function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0]

        if (!file) return

        if (!ACCEPTED_TYPES.includes(file.type)) {
            toast.error("Unsupported file type. Please upload a JPEG, PNG, or WebP image.")
            e.target.value = ""
            return
        }

        setPreview(URL.createObjectURL(file))
        onFileSelect(file)
    }

    return (
        <div
            className="upload-zone"
            onClick={() => inputRef.current?.click()}
        >
            <input
                ref={inputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={handleFileChange}
            />
            {preview ? (
                <img
                    src={preview}
                    alt="Selected plant"
                    className="w-full max-h-72 object-cover rounded-lg"
                />
            ) : (
                <>
                    <div className="icon-container">
                        <ImagePlus size={28} className="text-primary" />
                    </div>
                    <div className="text-center">
                        <p className="font-medium">Tap to take a photo</p>
                        <p className="text-body mt-0.5">
                            or select from your library
                        </p>
                    </div>
                </>
            )}
            {preview && (
                <Button
                    variant="outline"
                    onClick={(e) => {
                        e.stopPropagation()
                        inputRef.current?.click()
                    }}
                >
                    Change photo
                </Button>
            )}
        </div>
    )
}

export default UploadZone
