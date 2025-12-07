import { useState } from 'react'
import Map from './components/Map'
import Timeline from './components/Timeline'
import PreferenceForm from './components/PreferenceForm'
import WeatherTimeWidget from './components/WeatherTimeWidget'
import LanguageSwitcher from './components/LanguageSwitcher'
import { translations } from './translations'
import './index.css'
import './widgets.css'
import './buttons.css'
import './language-switcher.css'

function App() {
    const [route, setRoute] = useState(null)
    const [recommendations, setRecommendations] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [step, setStep] = useState('search') // 'search', 'recommendations', 'routing'
    const [currentPreferences, setCurrentPreferences] = useState(null)
    const [language, setLanguage] = useState('es') // 'es' or 'en'

    const t = translations[language]

    const handleSearchRecommendations = async (preferences) => {
        setLoading(true)
        setError(null)
        setCurrentPreferences(preferences)

        try {
            // Step 1: Get fast recommendations with client-side fallback
            const controller = new AbortController()
            const timeoutId = setTimeout(() => {
                controller.abort('Request timeout - please try again')
            }, 30000) // 30s timeout to allow for Google API auto-fetch

            try {
                const response = await fetch('http://localhost:8004/api/optimize/recommend-pois', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(preferences),
                    signal: controller.signal
                })
                clearTimeout(timeoutId)

                if (!response.ok) {
                    throw new Error('Backend error')
                }

                const data = await response.json()
                setRecommendations(data.pois)
                setStep('recommendations')
            } catch (fetchErr) {
                if (fetchErr.name === 'AbortError') {
                    console.error("Request aborted:", fetchErr.message || 'Timeout')
                    throw new Error('La solicitud tardó demasiado. Por favor intente de nuevo.')
                }
                console.error("Backend error:", fetchErr)
                throw fetchErr
            }
        } catch (err) {
            console.error('Error getting recommendations:', err)
            setError(err.message || "Error connecting to server")
            // Clear recommendations on error to avoid showing stale or wrong data
            setRecommendations([])
        } finally {
            setLoading(false)
        }
    }

    const handleRemoveRecommendation = (id) => {
        setRecommendations(prev => prev.filter(poi => poi.id !== id))
    }

    const handleGenerateRoute = async () => {
        if (!currentPreferences) return

        setLoading(true)
        setError(null)

        try {
            // Prepare payload with selected POIs if available
            const payload = { ...currentPreferences }

            // Sanitize start_location: Backend expects Dict[str, float], so remove 'address' string
            if (payload.start_location) {
                const { latitude, longitude } = payload.start_location
                if (latitude && longitude) {
                    payload.start_location = { latitude, longitude }
                } else {
                    payload.start_location = null
                }
            }

            if (recommendations && recommendations.length > 0) {
                payload.selected_poi_ids = recommendations.map(poi => poi.id)
            }

            // Use advanced optimization endpoint
            const response = await fetch('http://localhost:8004/api/optimize/generate-route', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Failed to generate route')
            }

            const data = await response.json()
            setRoute(data)
            setStep('routing')
            console.log('Route generated:', data)
        } catch (err) {
            console.error('Error generating route:', err)
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const handleReset = () => {
        setStep('search')
        setRoute(null)
        setRecommendations(null)
        setCurrentPreferences(null)
    }

    // Helper to get icon based on category
    const getCategoryIcon = (category) => {
        switch (category) {
            case 'Park': return '🌳';
            case 'Shopping': return '🛍️';
            case 'Museum': return '🏛️';
            case 'Dining': return '🍽️';
            case 'Beach': return '🏖️';
            default: return '📍';
        }
    }

    return (
        <div className="app-container">
            <header className="app-header">
                <h1>🗺️ {t.appTitle}</h1>
                <p>{t.appSubtitle}</p>
                <LanguageSwitcher currentLanguage={language} onLanguageChange={setLanguage} />
            </header>

            {/* Weather and Time Widget */}
            <WeatherTimeWidget t={t} language={language} />

            <div className="main-content">
                <aside className="sidebar">
                    <PreferenceForm
                        onSubmit={handleSearchRecommendations}
                        loading={loading}
                        error={error}
                        step={step}
                        onGenerateRoute={handleGenerateRoute}
                        onReset={handleReset}
                        t={t}
                    />
                </aside>

                <main className="content">
                    <div className="map-section">
                        <Map
                            route={route}
                            recommendations={recommendations}
                            step={step}
                            startLocation={currentPreferences?.start_location}
                            language={language}
                            t={t}
                        />
                    </div>

                    {step === 'recommendations' && recommendations && (
                        <div className="recommendations-section">
                            <h3 className="section-title">{t.recommendedPlaces} ({recommendations.length})</h3>
                            <div className="recommendations-grid">
                                {recommendations.map((poi, index) => (
                                    <div key={poi.id} className="recommendation-card-minimal">
                                        <div className="card-index-badge">{index + 1}</div>
                                        <div className="card-icon">
                                            {getCategoryIcon(poi.category)}
                                        </div>
                                        <div className="card-content">
                                            <div className="card-header">
                                                <h4>{poi.name}</h4>
                                                <span className="card-rating">⭐ {poi.rating}</span>
                                            </div>
                                            <p className="card-subtitle">{t[poi.category] || poi.category} • {poi.district}</p>
                                            <div className="card-meta">
                                                <span className="meta-item">
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
                                                    {poi.visit_duration} min
                                                </span>
                                            </div>
                                        </div>
                                        <button
                                            className="btn-delete-poi"
                                            onClick={() => handleRemoveRecommendation(poi.id)}
                                            title={t.deleteFromRoute}
                                        >
                                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                <polyline points="3 6 5 6 21 6"></polyline>
                                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                            </svg>
                                        </button>
                                    </div>
                                ))}
                            </div>
                            <div className="recommendations-actions">
                                <button className="btn-generate-blue" onClick={handleGenerateRoute} disabled={loading}>
                                    {loading ? (
                                        <>
                                            <span className="loading-spinner-white"></span>
                                            {t.generating}
                                        </>
                                    ) : (
                                        <>
                                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                                            </svg>
                                            {t.generateRoute}
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    )}

                    {step === 'routing' && route && (
                        <div className="timeline-section">
                            <Timeline
                                timeline={route.timeline}
                                totalDuration={route.total_duration}
                                totalCost={route.total_cost}
                                fitnessScore={route.fitness_score}
                                t={t}
                                onTimelineUpdate={(newTimeline) => {
                                    // Recalculate total cost from remaining POIs
                                    const newTotalCost = newTimeline.reduce((sum, item) => sum + (item.price || 0), 0)

                                    // Recalculate total duration (sum of visit + travel + wait times)
                                    const newTotalDuration = newTimeline.reduce((sum, item) => {
                                        return sum + (item.visit_duration || 0) + (item.travel_time || 0) + (item.wait_time || 0)
                                    }, 0)

                                    // Update route with new timeline and recalculated values
                                    const updatedRoute = {
                                        ...route,
                                        timeline: newTimeline,
                                        total_cost: newTotalCost,
                                        total_duration: newTotalDuration,
                                        // Update route array (POI objects) based on timeline
                                        route: newTimeline.map(item => ({
                                            id: item.poi_id,
                                            name: item.poi_name,
                                            latitude: item.latitude,
                                            longitude: item.longitude,
                                            category: item.category,
                                            district: item.district,
                                            rating: item.rating,
                                            price: item.price
                                        }))
                                    }

                                    setRoute(updatedRoute)
                                }}
                            />
                            <button className="btn-reset-styled" onClick={handleReset}>
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                                    <path d="M3 3v5h5" />
                                </svg>
                                {t.newSearch}
                            </button>
                        </div>
                    )}
                </main>
            </div>
        </div>
    )
}

export default App
