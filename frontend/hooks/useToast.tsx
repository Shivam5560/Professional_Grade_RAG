"use client"

import { useEffect, useState } from "react"

import {
	Toast,
	ToastClose,
	ToastDescription,
	ToastProvider,
	ToastTitle,
	ToastViewport,
} from "@/components/ui/toast"

type ToastItem = {
	id: string
	title?: string
	description?: string
	variant?: "default" | "destructive"
}

let toastsStore: ToastItem[] = []
let listeners: Array<(items: ToastItem[]) => void> = []

const notify = () => {
	listeners.forEach((listener) => listener([...toastsStore]))
}

const addToast = (item: Omit<ToastItem, "id">) => {
	const id = Math.random().toString(36).slice(2, 9)
	toastsStore = [...toastsStore, { id, ...item }]
	notify()

	setTimeout(() => {
		toastsStore = toastsStore.filter((t) => t.id !== id)
		notify()
	}, 3000)
}

export const useToast = () => {
	const [toasts, setToasts] = useState<ToastItem[]>(toastsStore)

	useEffect(() => {
		listeners = [...listeners, setToasts]
		return () => {
			listeners = listeners.filter((listener) => listener !== setToasts)
		}
	}, [])

	const toast = ({
		title,
		description,
		variant = "default",
	}: {
		title?: string
		description?: string
		variant?: "default" | "destructive"
	}) => addToast({ title, description, variant })

	return { toast, toasts }
}

export function Toaster() {
	const { toasts } = useToast()

	return (
		<ToastProvider>
			{toasts.map((toast) => (
				<Toast key={toast.id} variant={toast.variant}>
					{toast.title && <ToastTitle>{toast.title}</ToastTitle>}
					{toast.description && (
						<ToastDescription>{toast.description}</ToastDescription>
					)}
					<ToastClose />
				</Toast>
			))}
			<ToastViewport />
		</ToastProvider>
	)
}
