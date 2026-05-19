import React, { useState, useRef, useCallback } from 'react'
import './index.css'

interface SwipeActionProps {
  leftActions?: { key: string; text: string; color: string }[]
  rightActions?: { key: string; text: string; color: string }[]
  onAction: (key: string) => void
  children: React.ReactNode
}

const SwipeAction: React.FC<SwipeActionProps> = ({
  leftActions = [],
  rightActions = [],
  onAction,
  children,
}) => {
  const [offset, setOffset] = useState(0)
  const [isSwiping, setIsSwiping] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const startXRef = useRef(0)
  const startOffsetRef = useRef(0)

  const leftActionsWidth = leftActions.length * 80
  const rightActionsWidth = rightActions.length * 80

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    startXRef.current = e.touches[0].clientX
    startOffsetRef.current = offset
    setIsSwiping(true)
  }, [offset])

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!isSwiping) return

    const currentX = e.touches[0].clientX
    const deltaX = currentX - startXRef.current
    let newOffset = startOffsetRef.current + deltaX

    // Clamp offset
    newOffset = Math.max(-rightActionsWidth, Math.min(leftActionsWidth, newOffset))
    setOffset(newOffset)
  }, [isSwiping, leftActionsWidth, rightActionsWidth])

  const handleTouchEnd = useCallback(() => {
    setIsSwiping(false)

    // Snap to nearest action or closed
    if (offset > leftActionsWidth * 0.4) {
      setOffset(leftActionsWidth)
    } else if (offset < -rightActionsWidth * 0.4) {
      setOffset(-rightActionsWidth)
    } else {
      setOffset(0)
    }
  }, [offset, leftActionsWidth, rightActionsWidth])

  const handleAction = (key: string) => {
    setOffset(0)
    onAction(key)
  }

  return (
    <div
      ref={containerRef}
      className="swipe-action-container"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Left Actions */}
      <div
        className="swipe-action-left"
        style={{ width: leftActionsWidth }}
      >
        {leftActions.map((action) => (
          <div
            key={action.key}
            className="swipe-action-btn"
            style={{ background: action.color }}
            onClick={() => handleAction(action.key)}
          >
            {action.text}
          </div>
        ))}
      </div>

      {/* Content */}
      <div
        className={`swipe-action-content ${isSwiping ? 'swiping' : ''}`}
        style={{ transform: `translateX(${offset}px)` }}
      >
        {children}
      </div>

      {/* Right Actions */}
      <div
        className="swipe-action-right"
        style={{ width: rightActionsWidth }}
      >
        {rightActions.map((action) => (
          <div
            key={action.key}
            className="swipe-action-btn"
            style={{ background: action.color }}
            onClick={() => handleAction(action.key)}
          >
            {action.text}
          </div>
        ))}
      </div>
    </div>
  )
}

export default SwipeAction
