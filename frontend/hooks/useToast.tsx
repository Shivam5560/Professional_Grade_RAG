import { useState } from "react"

type ToastType = {
  id: string
  title?: string
  description?: string
  variant?: "default" | "destructive"
}

let toastCount = 0

export const useToast = () => {
  const [toasts, setToasts] = useState<ToastType[]>([])

  const toast = ({
    title,
    description,
    variant = "default",
  }: {
    title?: string
    description?: string
    variant?: "default" | "destructive"
  }) => {
    const id = `toast-${++toastCount}`
    const newToast = { id, title, description, variant }
    
    setToasts((prev) => [...prev, newToast])
    
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 3000)
  }

  const dismiss = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  return { toast, toasts, dismiss }
}
