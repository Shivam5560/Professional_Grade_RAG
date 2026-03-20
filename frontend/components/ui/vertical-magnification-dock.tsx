"use client"

import {
  motion,
  MotionValue,
  useMotionValue,
  useSpring,
  useTransform,
  type SpringOptions,
  AnimatePresence,
} from 'framer-motion'
import React, { Children, cloneElement, useEffect, useMemo, useRef, useState } from 'react'

export type VerticalDockItemData = {
  icon: React.ReactNode
  label: React.ReactNode
  onClick: () => void
  className?: string
}

export type VerticalDockProps = {
  items: VerticalDockItemData[]
  className?: string
  distance?: number
  panelWidth?: number
  baseItemSize?: number
  magnification?: number
  spring?: SpringOptions
}

type DockItemProps = {
  className?: string
  children: React.ReactNode
  onClick?: () => void
  mouseY: MotionValue<number>
  spring: SpringOptions
  distance: number
  baseItemSize: number
  magnification: number
}

type DockLabelProps = {
  className?: string
  children: React.ReactNode
  isHovered?: MotionValue<number>
}

type DockIconProps = {
  className?: string
  children: React.ReactNode
}

function DockItem({
  children,
  className = '',
  onClick,
  mouseY,
  spring,
  distance,
  magnification,
  baseItemSize,
}: DockItemProps) {
  const ref = useRef<HTMLDivElement>(null)
  const isHovered = useMotionValue(0)

  const mouseDistance = useTransform(mouseY, (value) => {
    const rect = ref.current?.getBoundingClientRect() ?? { y: 0, height: baseItemSize }
    return value - rect.y - baseItemSize / 2
  })

  const targetSize = useTransform(
    mouseDistance,
    [-distance, 0, distance],
    [baseItemSize, magnification, baseItemSize]
  )

  const size = useSpring(targetSize, spring)

  return (
    <motion.div
      ref={ref}
      style={{ width: size, height: size }}
      onHoverStart={() => isHovered.set(1)}
      onHoverEnd={() => isHovered.set(0)}
      onFocus={() => isHovered.set(1)}
      onBlur={() => isHovered.set(0)}
      onClick={onClick}
      className={`relative inline-flex items-center justify-center rounded-full border border-border bg-card/90 shadow-lg cursor-pointer ${className}`}
      tabIndex={0}
      role="button"
      aria-haspopup="true"
    >
      {Children.map(children, (child) =>
        React.isValidElement(child)
          ? cloneElement(child as React.ReactElement<{ isHovered?: MotionValue<number> }>, { isHovered })
          : child
      )}
    </motion.div>
  )
}

function DockLabel({ children, className = '', isHovered }: DockLabelProps) {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    if (!isHovered) return
    const unsubscribe = isHovered.on('change', (latest) => {
      setIsVisible(latest === 1)
    })
    return () => unsubscribe()
  }, [isHovered])

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, x: -2 }}
          animate={{ opacity: 1, x: -8 }}
          exit={{ opacity: 0, x: -2 }}
          transition={{ duration: 0.18 }}
          className={`${className} absolute left-full ml-2 w-fit whitespace-pre rounded-md border border-border bg-card px-2 py-1 text-xs text-foreground shadow-sm`}
          role="tooltip"
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

function DockIcon({ children, className = '' }: DockIconProps) {
  return <div className={`flex items-center justify-center text-foreground ${className}`}>{children}</div>
}

export function VerticalMagnificationDock({
  items,
  className = '',
  spring = { mass: 0.1, stiffness: 170, damping: 14 },
  magnification = 68,
  distance = 160,
  panelWidth = 72,
  baseItemSize = 46,
}: VerticalDockProps) {
  const mouseY = useMotionValue(Infinity)
  const isHovered = useMotionValue(0)

  const baseHeight = useMemo(() => items.length * (baseItemSize + 8) + 20, [items.length, baseItemSize])
  const expandedHeight = useMemo(
    () => Math.max(baseHeight, items.length * (magnification + 10) + 20),
    [baseHeight, items.length, magnification]
  )

  const heightRow = useTransform(isHovered, [0, 1], [baseHeight, expandedHeight])
  const height = useSpring(heightRow, spring)

  return (
    <motion.div style={{ height }} className="flex items-center justify-center">
      <motion.div
        onMouseMove={({ pageY }) => {
          isHovered.set(1)
          mouseY.set(pageY)
        }}
        onMouseLeave={() => {
          isHovered.set(0)
          mouseY.set(Infinity)
        }}
        className={`${className} flex flex-col items-center justify-center gap-2 rounded-3xl border border-border bg-card/60 backdrop-blur-md px-2 py-3 shadow-xl`}
        style={{ width: panelWidth }}
        role="toolbar"
        aria-label="Vertical application dock"
      >
        {items.map((item, index) => (
          <DockItem
            key={index}
            onClick={item.onClick}
            className={item.className}
            mouseY={mouseY}
            spring={spring}
            distance={distance}
            magnification={magnification}
            baseItemSize={baseItemSize}
          >
            <DockIcon>{item.icon}</DockIcon>
            <DockLabel>{item.label}</DockLabel>
          </DockItem>
        ))}
      </motion.div>
    </motion.div>
  )
}

export default VerticalMagnificationDock
