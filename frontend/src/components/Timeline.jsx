function Timeline({ timeline, totalDuration, totalCost, fitnessScore }) {
    if (!timeline || timeline.length === 0) {
        return null
    }

    const formatTime = (minutes) => {
        const hours = Math.floor(minutes / 60)
        const mins = minutes % 60
        return `${hours}h ${mins}m`
    }

    const formatCurrency = (amount) => {
        return `S/ ${amount.toFixed(2)}`
    }

    return (
        <div className="timeline">
            <div className="timeline-header">
                <h2>📅 Itinerario Optimizado</h2>
                <div className="timeline-stats">
                    <div className="stat-item">
                        <div className="stat-value">{timeline.length}</div>
                        <div className="stat-label">Lugares</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">{formatTime(totalDuration)}</div>
                        <div className="stat-label">Duración</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">{formatCurrency(totalCost)}</div>
                        <div className="stat-label">Costo</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">{fitnessScore.toFixed(0)}</div>
                        <div className="stat-label">Puntaje</div>
                    </div>
                </div>
            </div>

            {timeline.map((item, index) => (
                <div key={index} className="timeline-item">
                    <div className="timeline-number">{index + 1}</div>

                    <div className="timeline-content">
                        <div className="timeline-poi-name">{item.poi_name}</div>

                        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                            <span className="badge badge-category">{item.category}</span>
                            <span className="badge badge-district">{item.district}</span>
                        </div>

                        <div className="timeline-details">
                            <div className="timeline-detail">
                                <span>🕐</span>
                                <span>
                                    <strong>Llegada:</strong> {item.arrival_time}
                                </span>
                            </div>

                            <div className="timeline-detail">
                                <span>🕑</span>
                                <span>
                                    <strong>Salida:</strong> {item.departure_time}
                                </span>
                            </div>

                            <div className="timeline-detail">
                                <span>⏱️</span>
                                <span>
                                    <strong>Visita:</strong> {item.visit_duration} min
                                </span>
                            </div>

                            {item.travel_time > 0 && (
                                <div className="timeline-detail">
                                    <span>🚶</span>
                                    <span>
                                        <strong>Caminata:</strong> {item.travel_time} min
                                    </span>
                                </div>
                            )}

                            {item.wait_time > 0 && (
                                <div className="timeline-detail">
                                    <span>⏳</span>
                                    <span>
                                        <strong>Espera:</strong> {item.wait_time} min
                                    </span>
                                </div>
                            )}

                            <div className="timeline-detail">
                                <span>💰</span>
                                <span>
                                    <strong>Precio:</strong> {formatCurrency(item.price)}
                                </span>
                            </div>

                            {item.weather && (
                                <div className="timeline-detail">
                                    <span>🌡️</span>
                                    <span>
                                        <strong>Clima:</strong> {item.weather.temperature?.toFixed(1)}°C
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    )
}

export default Timeline
