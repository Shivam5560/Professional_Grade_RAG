"use client"

import { useEffect, useState } from "react"

import {
	Toast,
	ToastAction,
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
	duration?: number | null
	actions?: Array<{
		label: string
		altText: string
		onClick: () => void
		className?: string
	}>
	onDismiss?: () => void
}

let toastsStore: ToastItem[] = []
let listeners: Array<(items: ToastItem[]) => void> = []
const timeouts = new Map<string, ReturnType<typeof setTimeout>>()

const notify = () => {
	listeners.forEach((listener) => listener([...toastsStore]))
}

const removeToast = (id: string) => {
	const timeout = timeouts.get(id)
	if (timeout) {
		clearTimeout(timeout)
		timeouts.delete(id)
	}
	toastsStore = toastsStore.filter((toast) => toast.id !== id)
	notify()
}

const addToast = (item: Omit<ToastItem, "id">) => {
	const id = Math.random().toString(36).slice(2, 9)
	toastsStore = [...toastsStore, { id, ...item }]
	notify()

	if (item.duration !== null) {
		const timeout = setTimeout(() => removeToast(id), item.duration ?? 3000)
		timeouts.set(id, timeout)
	}

	return id
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
		duration,
	}: {
		title?: string
		description?: string
		variant?: "default" | "destructive"
		duration?: number | null
	}) => addToast({ title, description, variant, duration })

	const confirm = ({
		title,
		description,
		confirmLabel = "Yes",
		cancelLabel = "No",
		variant = "default",
	}: {
		title: string
		description?: string
		confirmLabel?: string
		cancelLabel?: string
		variant?: "default" | "destructive"
	}) =>
		new Promise<boolean>((resolve) => {
			const id = addToast({
				title,
				description,
				variant,
				duration: null,
				actions: [
					{
						label: cancelLabel,
						altText: cancelLabel,
						onClick: () => {
							resolve(false)
							removeToast(id)
						},
						className: "bg-muted text-foreground hover:bg-muted/80",
					},
					{
						label: confirmLabel,
						altText: confirmLabel,
						onClick: () => {
							resolve(true)
							removeToast(id)
						},
						className:
							variant === "destructive"
								? "bg-destructive text-destructive-foreground hover:bg-destructive/90"
								: "bg-foreground text-background hover:bg-foreground/90",
					},
				],
				onDismiss: () => resolve(false),
			})
		})

	return { toast, confirm, toasts }
}

export function Toaster() {
	const { toasts } = useToast()

	return (
		<ToastProvider>
			{toasts.map((toast) => (
				<Toast
					key={toast.id}
					variant={toast.variant}
					duration={toast.duration === null ? 600000 : toast.duration}
					onOpenChange={(open) => {
						if (!open) {
							toast.onDismiss?.()
							removeToast(toast.id)
						}
					}}
				>
					{toast.title && <ToastTitle>{toast.title}</ToastTitle>}
					{toast.description && (
						<ToastDescription>{toast.description}</ToastDescription>
					)}
					{toast.actions && toast.actions.length > 0 && (
						<div className="mt-4 flex flex-wrap items-center gap-2">
							{toast.actions.map((action) => (
								<ToastAction
									key={action.label}
									altText={action.altText}
									onClick={action.onClick}
									className={action.className}
								>
									{action.label}
								</ToastAction>
							))}
						</div>
					)}
					<ToastClose />
				</Toast>
			))}
			<ToastViewport />
		</ToastProvider>
	)
}
