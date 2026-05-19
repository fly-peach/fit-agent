import React, { useState, useRef, useCallback, useEffect } from 'react'
import './index.css'

interface BottomSheetProps {
  open: boolean
  onClose: () => void
  children: React.ReactNode
  snapPoints?: (number | string)[]
  initialSnapIndex?: number
}

const BottomSheet: React.FC<BottomSheetProps> = ({
  open,
  onClose,
  children,
  snapPoints = ['25%', '50%', '90%'],
  initialSnapIndex = 1,
}) => {
  const [currentHeight, setCurrentHeight] = useState<string>(
    typeof snapPoints[initialSnapIndex] === 'number'
      ? `${snapPoints[initialSnapIndex]}px`
      : snapPoints[initialSnapIndex] as string
  )
  const [isDragging, setIsDragging] = useState(false)
  const [isVisible, setIsVisible] = useState(false)

  const sheetRef = useRef<HTMLDivElement>(null)
  const startYRef = useRef(0)
  const startHeightRef = useRef(0)
  const currentSnapIndexRef = useRef(initialSnapIndex)

  // Convert snap point to pixels
  const getSnapPointPx = useCallback((point: number | string): number => {
    if (typeof point === 'number') return point
    if (point.endsWith('%')) {
      return (window.innerHeight * parseFloat(point)) / 100
    }
    return window.innerHeight
  }, [])

  // Calculate closest snap point
  const findClosestSnapPoint = useCallback((height: number): { index: number; height: string } => {
    let closestIndex = 0
    let closestDistance = Infinity

    snapPoints.forEach((point, index) => {
      const px = getSnapPointPx(point)
      const distance = Math.abs(px - height)
      if (distance < closestDistance) {
        closestDistance = distance
        closestIndex = index
      }
    })

    return {
      index: closestIndex,
      height: typeof snapPoints[closestIndex] === 'number'
        ? `${snapPoints[closestIndex]}px`
        : snapPoints[closestIndex] as string,
    }
  }, [snapPoints, getSnapPointPx])

  // Handle open/close animations
  useEffect(() => {
    if (open) {
      setIsVisible(true)
      requestAnimationFrame(() => {
        setCurrentHeight(
          typeof snapPoints[initialSnapIndex] === 'number'
            ? `${snapPoints[initialSnapIndex]}px`
            : snapPoints[initialSnapIndex] as string
        )
      })
    } else {
      setCurrentHeight('0px')
      setTimeout(() => setIsVisible(false), 300)
    }
  }, [open, snapPoints, initialSnapIndex])

  // Handle drag start
  const handleDragStart = useCallback(
    (e: React.TouchEvent | React.MouseEvent) => {
      setIsDragging(true)
      const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY
      startYRef.current = clientY
      startHeightRef.current = sheetRef.current?.offsetHeight || 0
    },
    []
  )

  // Handle drag move
  const handleDragMove = useCallback(
    (e: TouchEvent | MouseEvent) => {
      if (!isDragging) return

      const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY
      const deltaY = startYRef.current - clientY
      let newHeight = startHeightRef.current + deltaY

      // Clamp height
      const minHeight = getSnapPointPx(snapPoints[0])
      const maxHeight = getSnapPointPx(snapPoints[snapPoints.length - 1])
      newHeight = Math.max(minHeight, Math.min(maxHeight, newHeight))

      setCurrentHeight(`${newHeight}px`)
    },
    [isDragging, snapPoints, getSnapPointPx]
  )

  // Handle drag end
  const handleDragEnd = useCallback(() => {
    if (!isDragging) return
    setIsDragging(false)

    const currentPx = sheetRef.current?.offsetHeight || 0
    const { index, height } = findClosestSnapPoint(currentPx)

    currentSnapIndexRef.current = index

    // If dragged below minimum, close
    if (currentPx < getSnapPointPx(snapPoints[0]) * 0.7) {
      onClose()
    } else {
      setCurrentHeight(height)
    }
  }, [isDragging, findClosestSnapPoint, getSnapPointPx, snapPoints, onClose])

  // Add/remove event listeners
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('touchmove', handleDragMove, { passive: false })
      document.addEventListener('touchend', handleDragEnd)
      document.addEventListener('mousemove', handleDragMove)
      document.addEventListener('mouseup', handleDragEnd)
    }

    return () => {
      document.removeEventListener('touchmove', handleDragMove)
      document.removeEventListener('touchend', handleDragEnd)
      document.removeEventListener('mousemove', handleDragMove)
      document.removeEventListener('mouseup', handleDragEnd)
    }
  }, [isDragging, handleDragMove, handleDragEnd])

  // Handle backdrop click
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  if (!isVisible) return null

  return (
    <div className="bottom-sheet-backdrop" onClick={handleBackdropClick}>
      <div
        ref={sheetRef}
        className={`bottom-sheet ${isDragging ? 'dragging' : ''}`}
        style={{ height: currentHeight }}
      >
        {/* Drag Handle */}
        <div className="bottom-sheet-handle" onMouseDown={handleDragStart} onTouchStart={handleDragStart}>
          <div className="bottom-sheet-handle-bar" />
        </div>

        {/* Content */}
        <div className="bottom-sheet-content">
          {children}
        </div>
      </div>
    </div>
  )
}

export default BottomSheet
