import { useState, useEffect } from 'react'

function WeatherTimeWidget({ t, language, startLocation }) {
    const [currentTime, setCurrentTime] = useState(new Date())
    const [weather, setWeather] = useState(null)
    const [loading, setLoading] = useState(true)

    // Default coordinates (Lima center)
    const DEFAULT_LAT = -12.0464
    const DEFAULT_LNG = -77.0428

    useEffect(() => {
        // Update time every second
        const timer = setInterval(() => {
            setCurrentTime(new Date())
        }, 1000)

        // Fetch weather for current location
        fetchWeather()

        return () => clearInterval(timer)
    }, [startLocation]) // Re-fetch when startLocation changes

    const fetchWeather = async () => {
        // Use startLocation if provided, otherwise default to Lima center
        const lat = startLocation?.latitude || DEFAULT_LAT
        const lng = startLocation?.longitude || DEFAULT_LNG

        try {
            const response = await fetch(
                `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m&timezone=America/Lima`
            )
            const data = await response.json()
            setWeather(data.current)
            setLoading(false)
        } catch (error) {
            console.error('Error fetching weather:', error)
            setLoading(false)
        }
    }

    const getWeatherDescription = (code) => {
        // This could be moved to translations too if needed, but for now we'll keep it simple
        // or map codes to translation keys
        const weatherCodes = {
            0: { desc: 'Despejado', icon: '☀️' },
            1: { desc: 'Mayormente despejado', icon: '🌤️' },
            2: { desc: 'Parcialmente nublado', icon: '⛅' },
            3: { desc: 'Nublado', icon: '☁️' },
            45: { desc: 'Neblina', icon: '🌫️' },
            48: { desc: 'Niebla', icon: '🌫️' },
            51: { desc: 'Llovizna ligera', icon: '🌦️' },
            53: { desc: 'Llovizna moderada', icon: '🌦️' },
            55: { desc: 'Llovizna intensa', icon: '🌧️' },
            61: { desc: 'Lluvia ligera', icon: '🌧️' },
            63: { desc: 'Lluvia moderada', icon: '🌧️' },
            65: { desc: 'Lluvia intensa', icon: '⛈️' },
            80: { desc: 'Chubascos', icon: '🌧️' },
            95: { desc: 'Tormenta', icon: '⛈️' }
        }
        return weatherCodes[code] || { desc: 'Desconocido', icon: '🌡️' }
    }

    const formatTime = (date) => {
        const locale = language === 'en' ? 'en-US' : 'es-PE'
        return date.toLocaleTimeString(locale, {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        })
    }

    const formatDate = (date) => {
        const locale = language === 'en' ? 'en-US' : 'es-PE'
        return date.toLocaleDateString(locale, {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        })
    }

    const getRainProbability = () => {
        if (!weather) return 0
        const code = weather.weather_code
        if (code >= 51 && code <= 65) return 80
        if (code >= 80 && code <= 82) return 90
        if (code >= 95) return 95
        if (code >= 2 && code <= 3) return 20
        return 5
    }

    if (loading) {
        return (
            <div className="weather-time-widget">
                <div className="widget-card">
                    <div className="loading-spinner"></div>
                </div>
            </div>
        )
    }

    const weatherInfo = weather ? getWeatherDescription(weather.weather_code) : null
    const rainProb = getRainProbability()

    let rainProbText = t.lowProb
    if (rainProb > 70) rainProbText = t.highProb
    else if (rainProb > 30) rainProbText = t.mediumProb

    let windText = t.moderate
    if (weather?.wind_speed_10m > 20) windText = t.windy

    return (
        <div className="weather-time-widget">
            {/* Time Card */}
            <div className="widget-card time-card">
                <div className="card-icon">🕐</div>
                <div className="card-content">
                    <div className="card-title">{t.currentTime}</div>
                    <div className="card-value">{formatTime(currentTime)}</div>
                    <div className="card-subtitle">{formatDate(currentTime)}</div>
                </div>
            </div>

            {/* Weather Card */}
            <div className="widget-card weather-card">
                <div className="card-icon">{weatherInfo?.icon || '🌡️'}</div>
                <div className="card-content">
                    <div className="card-title">{startLocation ? (t.weatherAtLocation || 'Clima en tu ubicación') : t.weatherInLima}</div>
                    <div className="card-value">
                        {weather?.temperature_2m ? `${Math.round(weather.temperature_2m)}°C` : '--°C'}
                    </div>
                    <div className="card-subtitle">{weatherInfo?.desc || t.loading}</div>
                </div>
            </div>

            {/* Rain Probability Card */}
            <div className="widget-card rain-card">
                <div className="card-icon">
                    {rainProb > 70 ? '🌧️' : rainProb > 30 ? '🌦️' : '☀️'}
                </div>
                <div className="card-content">
                    <div className="card-title">{t.rainProb}</div>
                    <div className="card-value">{rainProb}%</div>
                    <div className="card-subtitle">
                        {rainProbText}
                    </div>
                </div>
            </div>

            {/* Wind Card */}
            <div className="widget-card wind-card">
                <div className="card-icon">💨</div>
                <div className="card-content">
                    <div className="card-title">{t.wind}</div>
                    <div className="card-value">
                        {weather?.wind_speed_10m ? `${Math.round(weather.wind_speed_10m)} km/h` : '-- km/h'}
                    </div>
                    <div className="card-subtitle">
                        {windText}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default WeatherTimeWidget
