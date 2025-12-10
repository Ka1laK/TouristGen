import { useState } from 'react'

/**
 * FeedbackModal - Collects user ratings for generated routes
 * Can be shown as overlay modal or inline card (inline=true)
 */
const FeedbackModal = ({ routeId, routeData, onClose, onSubmit, t, inline = false }) => {
    const [rating, setRating] = useState(0)
    const [hoveredRating, setHoveredRating] = useState(0)
    const [submitted, setSubmitted] = useState(false)
    const [loading, setLoading] = useState(false)

    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

    const handleSubmit = async () => {
        if (rating === 0) return

        setLoading(true)
        try {
            const response = await fetch(`${API_URL}/api/feedback/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    route_id: routeId,
                    rating: rating,
                    total_duration: routeData?.total_duration,
                    total_cost: routeData?.total_cost,
                    num_pois: routeData?.num_pois,
                    fitness_score: routeData?.fitness_score,
                    avg_poi_rating: routeData?.avg_poi_rating,
                    avg_poi_popularity: routeData?.avg_poi_popularity,
                    total_distance_km: routeData?.total_distance_km
                }),
            })

            if (response.ok) {
                setSubmitted(true)
                if (!inline) {
                    setTimeout(() => {
                        onSubmit && onSubmit(rating)
                        onClose()
                    }, 1500)
                }
            }
        } catch (error) {
            console.error('Error submitting feedback:', error)
        } finally {
            setLoading(false)
        }
    }

    const displayRating = hoveredRating || rating

    // Inline card mode - no overlay
    if (inline) {
        return (
            <div className="feedback-inline-card">
                {!submitted ? (
                    <>
                        <div className="feedback-inline-header">
                            <span className="feedback-icon">⭐</span>
                            <h4>{t?.rateFeedback || '¿Qué te pareció esta ruta?'}</h4>
                        </div>

                        <div className="star-rating inline">
                            {[1, 2, 3, 4, 5].map((star) => (
                                <button
                                    key={star}
                                    className={`star ${star <= displayRating ? 'active' : ''}`}
                                    onClick={() => setRating(star)}
                                    onMouseEnter={() => setHoveredRating(star)}
                                    onMouseLeave={() => setHoveredRating(0)}
                                >
                                    ★
                                </button>
                            ))}
                        </div>

                        <div className="rating-label">
                            {displayRating === 1 && (t?.ratingBad || 'Mala')}
                            {displayRating === 2 && (t?.ratingPoor || 'Regular')}
                            {displayRating === 3 && (t?.ratingOk || 'Aceptable')}
                            {displayRating === 4 && (t?.ratingGood || 'Buena')}
                            {displayRating === 5 && (t?.ratingExcellent || '¡Excelente!')}
                        </div>

                        <button
                            className="btn-submit-feedback-inline"
                            onClick={handleSubmit}
                            disabled={rating === 0 || loading}
                        >
                            {loading ? (
                                <span className="loading-spinner-white"></span>
                            ) : (
                                t?.submitFeedback || 'Enviar calificación'
                            )}
                        </button>
                    </>
                ) : (
                    <div className="feedback-success-inline">
                        <span className="success-icon">✓</span>
                        <p>{t?.thanksFeedback || '¡Gracias por tu calificación!'}</p>
                    </div>
                )}
            </div>
        )
    }

    // Overlay modal mode (original)
    return (
        <div className="feedback-overlay">
            <div className="feedback-modal">
                {!submitted ? (
                    <>
                        <div className="feedback-header">
                            <span className="feedback-icon">⭐</span>
                            <h3>{t?.rateFeedback || '¿Qué te pareció esta ruta?'}</h3>
                        </div>

                        <div className="star-rating">
                            {[1, 2, 3, 4, 5].map((star) => (
                                <button
                                    key={star}
                                    className={`star ${star <= displayRating ? 'active' : ''}`}
                                    onClick={() => setRating(star)}
                                    onMouseEnter={() => setHoveredRating(star)}
                                    onMouseLeave={() => setHoveredRating(0)}
                                >
                                    ★
                                </button>
                            ))}
                        </div>

                        <div className="rating-label">
                            {displayRating === 1 && (t?.ratingBad || 'Mala')}
                            {displayRating === 2 && (t?.ratingPoor || 'Regular')}
                            {displayRating === 3 && (t?.ratingOk || 'Aceptable')}
                            {displayRating === 4 && (t?.ratingGood || 'Buena')}
                            {displayRating === 5 && (t?.ratingExcellent || '¡Excelente!')}
                        </div>

                        <div className="feedback-actions">
                            <button
                                className="btn-submit-feedback"
                                onClick={handleSubmit}
                                disabled={rating === 0 || loading}
                            >
                                {loading ? (
                                    <span className="loading-spinner-white"></span>
                                ) : (
                                    t?.submitFeedback || 'Enviar'
                                )}
                            </button>
                            <button className="btn-skip-feedback" onClick={onClose}>
                                {t?.skipFeedback || 'Omitir'}
                            </button>
                        </div>
                    </>
                ) : (
                    <div className="feedback-success">
                        <span className="success-icon">✓</span>
                        <p>{t?.thanksFeedback || '¡Gracias por tu calificación!'}</p>
                    </div>
                )}
            </div>
        </div>
    )
}

export default FeedbackModal

