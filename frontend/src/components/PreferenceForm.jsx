import { useState } from 'react'
import LocationSearch from './LocationSearch'

const CATEGORIAS = [
    { value: 'Museum', label: 'Museos' },
    { value: 'Park', label: 'Parques' },
    { value: 'Beach', label: 'Playas' },
    { value: 'Shopping', label: 'Centros Comerciales' },
    { value: 'Dining', label: 'Restaurantes' },
    { value: 'Religious', label: 'Sitios Religiosos' },
    { value: 'Landmark', label: 'Monumentos' },
    { value: 'Zoo', label: 'Zoológicos' },
    { value: 'Cultural', label: 'Centros Culturales' }
]

const DISTRITOS = [
    'Miraflores', 'Barranco', 'Lima', 'San Isidro', 'Callao',
    'Surco', 'San Miguel', 'Pueblo Libre', 'Chorrillos', 'La Molina',
    'San Borja', 'Jesús María', 'Lince', 'Magdalena', 'Breña'
]

// SVG Icons (same as before)
const ClockIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
    </svg>
)

const WalletIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 12V7H5a2 2 0 0 1 0-4h14v4" />
        <path d="M3 5v14a2 2 0 0 0 2 2h16v-5" />
        <path d="M18 12a2 2 0 0 0 0 4h4v-4Z" />
    </svg>
)

const MapPinIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
        <circle cx="12" cy="10" r="3" />
    </svg>
)

const WalkIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="4" r="2" />
        <path d="m16.5 17.5-1.5-5.5-3 3" />
        <path d="M10.5 12.5 8 10l-2 1" />
        <path d="m7 18 1.5-5.5" />
    </svg>
)

const FilterIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
    </svg>
)

const XIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
)

function PreferenceForm({ onSubmit, loading, error, step, onGenerateRoute, onReset, t }) {
    const [preferences, setPreferences] = useState({
        max_duration: 480,
        max_budget: 200,
        start_time: '09:00',
        user_pace: 'medium',
        mandatory_categories: [],
        avoid_categories: [],
        preferred_districts: [],
        start_location: {
            address: '',
            latitude: null,
            longitude: null
        }
    })

    const [showAdvanced, setShowAdvanced] = useState(false)

    const handleSubmit = (e) => {
        e.preventDefault()
        onSubmit(preferences)
    }

    const handleChange = (field, value) => {
        setPreferences(prev => ({
            ...prev,
            [field]: value
        }))
    }

    const handleLocationSelect = (location) => {
        setPreferences(prev => ({
            ...prev,
            start_location: location
        }))
    }

    const addItem = (field, value) => {
        if (value && !preferences[field].includes(value)) {
            setPreferences(prev => ({
                ...prev,
                [field]: [...prev[field], value]
            }))
        }
    }

    const removeItem = (field, value) => {
        setPreferences(prev => ({
            ...prev,
            [field]: prev[field].filter(item => item !== value)
        }))
    }

    if (step === 'recommendations') {
        return (
            <div className="preference-form-compact">
                <div className="form-header">
                    <h2>{t.recommendationsReady}</h2>
                    <p className="text-sm text-gray-600">{t.foundPlaces}</p>
                </div>

                <div className="summary-card">
                    <p><strong>{t.startPoint}:</strong> {preferences.start_location.address || t.myLocation}</p>
                    <p><strong>{t.duration}:</strong> {preferences.max_duration / 60} {t.hours}</p>
                    <p><strong>{t.budget}:</strong> S/ {preferences.max_budget}</p>
                </div>

                <button
                    type="button"
                    className="btn-generate"
                    onClick={onGenerateRoute}
                    disabled={loading}
                >
                    {loading ? (
                        <>
                            <span className="loading-spinner"></span>
                            <span>{t.generating}</span>
                        </>
                    ) : (
                        <>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M5 12h14" />
                                <path d="m12 5 7 7-7 7" />
                            </svg>
                            <span>{t.generateRoute}</span>
                        </>
                    )}
                </button>

                <button
                    type="button"
                    className="btn-secondary"
                    onClick={onReset}
                    style={{ marginTop: '0.5rem', width: '100%', padding: '0.75rem', border: '1px solid #cbd5e1', borderRadius: '8px', background: 'white' }}
                >
                    {t.changeFilters}
                </button>
            </div>
        )
    }

    if (step === 'routing') {
        return (
            <div className="preference-form-compact">
                <div className="form-header">
                    <h2>{t.routeGenerated}</h2>
                </div>
                <div className="summary-card">
                    <p>{t.enjoyTrip}</p>
                </div>
                <button
                    type="button"
                    className="btn-secondary"
                    onClick={onReset}
                    style={{ marginTop: '0.5rem', width: '100%', padding: '0.75rem', border: '1px solid #cbd5e1', borderRadius: '8px', background: 'white' }}
                >
                    {t.newSearch}
                </button>
            </div>
        )
    }

    return (
        <form className="preference-form-compact" onSubmit={handleSubmit}>
            <div className="form-header">
                <h2>{t.configTitle}</h2>
            </div>

            {error && (
                <div className="error-message">
                    {error}
                </div>
            )}

            {/* Location Search */}
            <div className="form-group-compact">
                <label className="form-label-icon">
                    <MapPinIcon />
                    <span>{t.startPoint}</span>
                </label>
                <LocationSearch
                    onLocationSelect={handleLocationSelect}
                    initialValue={preferences.start_location.address}
                />
            </div>

            {/* Duration */}
            <div className="form-group-compact">
                <label className="form-label-icon">
                    <ClockIcon />
                    <span>{t.duration}</span>
                </label>
                <select
                    className="form-select"
                    value={preferences.max_duration}
                    onChange={(e) => handleChange('max_duration', parseInt(e.target.value))}
                >
                    <option value="180">3 {t.hours} ({t.halfDay})</option>
                    <option value="300">5 {t.hours}</option>
                    <option value="480">8 {t.hours} ({t.fullDay})</option>
                    <option value="600">10 {t.hours}</option>
                </select>
            </div>

            {/* Budget */}
            <div className="form-group-compact">
                <label className="form-label-icon">
                    <WalletIcon />
                    <span>{t.budget}</span>
                </label>
                <select
                    className="form-select"
                    value={preferences.max_budget}
                    onChange={(e) => handleChange('max_budget', parseFloat(e.target.value))}
                >
                    <option value="50">S/ 50 ({t.economic})</option>
                    <option value="100">S/ 100</option>
                    <option value="200">S/ 200</option>
                    <option value="300">S/ 300</option>
                    <option value="500">S/ 500 ({t.premium})</option>
                </select>
            </div>

            {/* Start Time */}
            <div className="form-group-compact">
                <label className="form-label-icon">
                    <ClockIcon />
                    <span>{t.startTime}</span>
                </label>
                <input
                    type="time"
                    className="form-input"
                    value={preferences.start_time}
                    onChange={(e) => handleChange('start_time', e.target.value)}
                    required
                />
            </div>

            {/* Pace */}
            <div className="form-group-compact">
                <label className="form-label-icon">
                    <WalkIcon />
                    <span>{t.pace}</span>
                </label>
                <select
                    className="form-select"
                    value={preferences.user_pace}
                    onChange={(e) => handleChange('user_pace', e.target.value)}
                >
                    <option value="slow">{t.slow}</option>
                    <option value="medium">{t.medium}</option>
                    <option value="fast">{t.fast}</option>
                </select>
            </div>

            {/* Advanced Options Toggle */}
            <button
                type="button"
                className="btn-advanced"
                onClick={() => setShowAdvanced(!showAdvanced)}
            >
                <FilterIcon />
                <span>{showAdvanced ? t.hideFilters : t.showFilters} {t.advancedFilters}</span>
                <span className="toggle-icon">{showAdvanced ? '▲' : '▼'}</span>
            </button>

            {/* Advanced Options */}
            {showAdvanced && (
                <div className="advanced-options">
                    {/* Mandatory Categories */}
                    <div className="form-group-compact">
                        <label className="form-label-small">{t.wantToVisit}</label>
                        <select
                            className="form-select"
                            onChange={(e) => {
                                addItem('mandatory_categories', e.target.value)
                                e.target.value = ''
                            }}
                            defaultValue=""
                        >
                            <option value="" disabled>{t.selectCategory}</option>
                            {CATEGORIAS.filter(cat => !preferences.mandatory_categories.includes(cat.value)).map(cat => (
                                <option key={cat.value} value={cat.value}>
                                    {t[cat.value] || cat.label}
                                </option>
                            ))}
                        </select>
                        <div className="chips-container">
                            {preferences.mandatory_categories.map(cat => {
                                const category = CATEGORIAS.find(c => c.value === cat)
                                return (
                                    <div key={cat} className="chip chip-primary">
                                        <span>{t[cat] || category?.label || cat}</span>
                                        <button type="button" onClick={() => removeItem('mandatory_categories', cat)}>
                                            <XIcon />
                                        </button>
                                    </div>
                                )
                            })}
                        </div>
                    </div>

                    {/* Avoid Categories */}
                    <div className="form-group-compact">
                        <label className="form-label-small">{t.dontInterest}</label>
                        <select
                            className="form-select"
                            onChange={(e) => {
                                addItem('avoid_categories', e.target.value)
                                e.target.value = ''
                            }}
                            defaultValue=""
                        >
                            <option value="" disabled>{t.selectCategory}</option>
                            {CATEGORIAS.filter(cat => !preferences.avoid_categories.includes(cat.value)).map(cat => (
                                <option key={cat.value} value={cat.value}>
                                    {t[cat.value] || cat.label}
                                </option>
                            ))}
                        </select>
                        <div className="chips-container">
                            {preferences.avoid_categories.map(cat => {
                                const category = CATEGORIAS.find(c => c.value === cat)
                                return (
                                    <div key={cat} className="chip chip-danger">
                                        <span>{t[cat] || category?.label || cat}</span>
                                        <button type="button" onClick={() => removeItem('avoid_categories', cat)}>
                                            <XIcon />
                                        </button>
                                    </div>
                                )
                            })}
                        </div>
                    </div>

                    {/* Preferred Districts */}
                    <div className="form-group-compact">
                        <label className="form-label-small">{t.preferredDistricts}</label>
                        <select
                            className="form-select"
                            onChange={(e) => {
                                addItem('preferred_districts', e.target.value)
                                e.target.value = ''
                            }}
                            defaultValue=""
                        >
                            <option value="" disabled>{t.selectDistrict}</option>
                            {DISTRITOS.filter(d => !preferences.preferred_districts.includes(d)).map(district => (
                                <option key={district} value={district}>
                                    {district}
                                </option>
                            ))}
                        </select>
                        <div className="chips-container">
                            {preferences.preferred_districts.map(district => (
                                <div key={district} className="chip chip-secondary">
                                    <span>{district}</span>
                                    <button type="button" onClick={() => removeItem('preferred_districts', district)}>
                                        <XIcon />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Submit Button */}
            <button
                type="submit"
                className="btn-generate"
                disabled={loading}
            >
                {loading ? (
                    <>
                        <span className="loading-spinner"></span>
                        <span>{t.searching}</span>
                    </>
                ) : (
                    <>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="11" cy="11" r="8" />
                            <line x1="21" y1="21" x2="16.65" y2="16.65" />
                        </svg>
                        <span>{t.searchButton}</span>
                    </>
                )}
            </button>

            <small className="form-footer">
                {t.step1}
            </small>
        </form>
    )
}

export default PreferenceForm
