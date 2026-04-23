import { useState, useEffect, useCallback } from 'react'

export function useApi<T>(
  fetchFn: () => Promise<T>,
  autoFetch: boolean = true
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(autoFetch)
  const [error, setError] = useState<Error | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchFn()
      setData(result)
      return result
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'))
      throw err
    } finally {
      setLoading(false)
    }
  }, [fetchFn])

  useEffect(() => {
    if (autoFetch) {
      fetch()
    }
  }, [autoFetch, fetch])

  return { data, loading, error, fetch, setData }
}