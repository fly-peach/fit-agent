import React, { useState, useRef, useCallback } from 'react'
import { Spin } from 'antd'
import './PullToRefresh.css'

interface PullToRefreshProps {
  onRefresh: () => Promise<void>
  children: React.ReactNode
}

const PullToRefresh: React.FC<PullToRefreshProps> = ({ onRefresh, children }) => {
  const [pulling, setPulling] = useState(false)
  const [pullDistance, setPullDistance] = useState(0)
  const [refreshing, setRefreshing] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const startYRef = useRef(0)
  const isPullingRef = useRef(false)

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    // Only trigger when scrolled to top
    if (containerRef.current && containerRef.current.scrollTop > 0) {
      return
    }
    isPullingRef.current = true
    startYRef.current = e.touches[0].clientY
    setPulling(true)
  }, [])

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!isPullingRef.current) return

    const currentY = e.touches[0].clientY
    const deltaY = currentY - startYRef.current

    // Only allow pulling down
    if (deltaY > 0) {
      // Apply resistance to pull distance
      const resistance = 0.5
      const distance = Math.min(deltaY * resistance, 100)
      setPullDistance(distance)
    }
  }, [])

  const handleTouchEnd = useCallback(async () => {
    if (!isPullingRef.current) return
    isPullingRef.current = false
    setPulling(false)

    // If pulled enough distance, trigger refresh
    if (pullDistance > 60) {
      setRefreshing(true)
      setPullDistance(0)
      try {
        await onRefresh()
      } finally {
        setRefreshing(false)
      }
    } else {
      setPullDistance(0)
    }
  }, [pullDistance, onRefresh])

  return (
    <div
      ref={containerRef}
      className="pull-to-refresh-container"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Pull indicator */}
      <div
        className="pull-to-refresh-indicator"
        style={{ height: pullDistance }}
      >
        {refreshing ? (
          <Spin size="small" />
        ) : (
          <div className="pull-to-refresh-arrow">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{
                transform: pullDistance > 60 ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s',
              }}
            >
              <polyline points="18 15 12 9 6 15" />
            </svg>
          </div>
        )}
        {pulling && (
          <span className="pull-to-refresh-text">
            {pullDistance > 60 ? '释放刷新' : '下拉刷新'}
          </span>
        )}
      </div>

      {/* Content */}
      <div
        className="pull-to-refresh-content"
        style={{
          transform: `translateY(${pullDistance}px)`,
          transition: pulling ? 'none' : 'transform 0.3s',
        }}
      >
        {children}
      </div>
    </div>
  )
}

export default PullToRefresh
