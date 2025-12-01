import { useState, useEffect } from 'react'

function WeatherTimeWidget() {
    const [currentTime, setCurrentTime] = useState(new Date())
    const [weather, setWeather] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        // Update time every second
        const timer = setInterval(() => {
            setCurrentTime(new Date())
        }, 1000)

        // Fetch weather for Lima
        fetchWeather()

        return () => clearInterval(timer)
    }, [])

    const fetchWeather = async () => {
        try {
            // Lima coordinates
            const response = await fetch(
                'https://api.open-meteo.com/v1/forecast?latitude=-12.0464&longitude=-77.0428&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m&timezone=America/Lima'
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
        return date.toLocaleTimeString('es-PE', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        })
    }

    const formatDate = (date) => {
        return date.toLocaleDateString('es-PE', {
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

    return (
        <div className="weather-time-widget">
            {/* Time Card */}
            <div className="widget-card time-card">
                <div className="card-icon">🕐</div>
                <div className="card-content">
                    <div className="card-title">Hora Actual</div>
                    <div className="card-value">{formatTime(currentTime)}</div>
                    <div className="card-subtitle">{formatDate(currentTime)}</div>
                </div>
            </div>

            {/* Weather Card */}
            <div className="widget-card weather-card">
                <div className="card-icon">{weatherInfo?.icon || '🌡️'}</div>
                <div className="card-content">
                    <div className="card-title">Clima en Lima</div>
                    <div className="card-value">
                        {weather?.temperature_2m ? `${Math.round(weather.temperature_2m)}°C` : '--°C'}
                    </div>
                    <div className="card-subtitle">{weatherInfo?.desc || 'Cargando...'}</div>
                </div>
            </div>

            {/* Rain Probability Card */}
            <div className="widget-card rain-card">
                <div className="card-icon">
                    {rainProb > 70 ? '🌧️' : rainProb > 30 ? '🌦️' : '☀️'}
                </div>
                <div className="card-content">
                    <div className="card-title">Probabilidad de Lluvia</div>
                    <div className="card-value">{rainProb}%</div>
                    <div className="card-subtitle">
                        {rainProb > 70 ? 'Alta probabilidad' : rainProb > 30 ? 'Probabilidad media' : 'Baja probabilidad'}
                    </div>
                </div>
            </div>

            {/* Wind Card */}
            <div className="widget-card wind-card">
                <div className="card-icon">💨</div>
                <div className="card-content">
                    <div className="card-title">Viento</div>
                    <div className="card-value">
                        {weather?.wind_speed_10m ? `${Math.round(weather.wind_speed_10m)} km/h` : '-- km/h'}
                    </div>
                    <div className="card-subtitle">
                        {weather?.wind_speed_10m > 20 ? 'Ventoso' : 'Moderado'}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default WeatherTimeWidget
