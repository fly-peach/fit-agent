import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { userApi } from '../services/user'
import type { UserProfile, UserSettings } from '../services/user'

export function useUser() {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [settings, setSettings] = useState<UserSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      navigate('/login')
      return
    }

    const fetchUser = async () => {
      try {
        const profileData = await userApi.getProfile()
        setProfile(profileData)
        const settingsData = await userApi.getSettings()
        setSettings(settingsData)
      } catch {
        navigate('/login')
      } finally {
        setLoading(false)
      }
    }

    fetchUser()
  }, [navigate])

  return { profile, settings, loading, setProfile, setSettings }
}