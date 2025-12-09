import { useState, useEffect, useRef } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function LocationSearch({ onLocationSelect, initialValue = '' }) {
    const [searchTerm, setSearchTerm] = useState(initialValue)
    const [suggestions, setSuggestions] = useState([])
    const [loading, setLoading] = useState(false)
    const [showSuggestions, setShowSuggestions] = useState(false)
    const searchTimeout = useRef(null)

    useEffect(() => {
        if (searchTerm.length < 3) {
            setSuggestions([])
            return
        }

        // Debounce search
        if (searchTimeout.current) {
            clearTimeout(searchTimeout.current)
        }

        searchTimeout.current = setTimeout(() => {
            searchLocation(searchTerm)
        }, 500)

        return () => {
            if (searchTimeout.current) {
                clearTimeout(searchTimeout.current)
            }
        }
    }, [searchTerm])

    const searchLocation = async (query) => {
        setLoading(true)
        try {
            // Use backend proxy to avoid CORS issues
            const response = await fetch(
                `${API_URL}/api/geocoding/search?q=${encodeURIComponent(query)}&limit=5`
            )

            if (!response.ok) {
                throw new Error('Geocoding request failed')
            }

            const data = await response.json()

            setSuggestions(data.map(item => ({
                display_name: item.display_name,
                lat: item.lat,
                lon: item.lon,
                address: item.address
            })))
            setShowSuggestions(true)
        } catch (error) {
            console.error('Error searching location:', error)
            setSuggestions([])
        } finally {
            setLoading(false)
        }
    }

    const handleSelectSuggestion = (suggestion) => {
        setSearchTerm(suggestion.display_name)
        setShowSuggestions(false)
        onLocationSelect({
            address: suggestion.display_name,
            latitude: suggestion.lat,
            longitude: suggestion.lon
        })
    }

    const handleUseCurrentLocation = () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    const { latitude, longitude } = position.coords

                    // Reverse geocode to get address using backend proxy
                    try {
                        const response = await fetch(
                            `${API_URL}/api/geocoding/reverse?lat=${latitude}&lon=${longitude}`
                        )

                        if (!response.ok) {
                            throw new Error('Reverse geocoding failed')
                        }

                        const data = await response.json()

                        setSearchTerm(data.display_name)
                        onLocationSelect({
                            address: data.display_name,
                            latitude,
                            longitude
                        })
                    } catch (error) {
                        console.error('Error reverse geocoding:', error)
                        setSearchTerm(`${latitude}, ${longitude}`)
                        onLocationSelect({
                            address: `${latitude}, ${longitude}`,
                            latitude,
                            longitude
                        })
                    }
                },
                (error) => {
                    console.error('Error getting location:', error)
                    alert('No se pudo obtener tu ubicación. Por favor ingresa tu dirección manualmente.')
                }
            )
        } else {
            alert('Tu navegador no soporta geolocalización')
        }
    }

    return (
        <div className="location-search">
            <div className="search-input-container">
                <input
                    type="text"
                    className="location-input"
                    placeholder="Ej: Av. Larco 1234, Miraflores o busca un lugar"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                />
                <button
                    type="button"
                    className="btn-location"
                    onClick={handleUseCurrentLocation}
                    title="Usar mi ubicación actual"
                >
                    📍 Mi Ubicación
                </button>
            </div>

            {loading && (
                <div className="search-loading">
                    <span className="loading-spinner-small"></span>
                    Buscando...
                </div>
            )}

            {showSuggestions && suggestions.length > 0 && (
                <div className="suggestions-dropdown">
                    {suggestions.map((suggestion, index) => (
                        <div
                            key={index}
                            className="suggestion-item"
                            onClick={() => handleSelectSuggestion(suggestion)}
                        >
                            <div className="suggestion-icon">📍</div>
                            <div className="suggestion-content">
                                <div className="suggestion-name">
                                    {suggestion.address?.road || suggestion.address?.suburb || 'Ubicación'}
                                </div>
                                <div className="suggestion-address">{suggestion.display_name}</div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <small style={{
                display: 'block',
                marginTop: '0.5rem',
                color: 'var(--text-secondary)',
                fontSize: '0.85rem'
            }}>
                💡 Puedes buscar por dirección, distrito o punto de referencia
            </small>
        </div>
    )
}

export default LocationSearch
