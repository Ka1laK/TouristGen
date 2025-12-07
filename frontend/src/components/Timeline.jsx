import { useState } from 'react'
import POIDetailModal from './POIDetailModal'

function Timeline({ timeline: initialTimeline, totalDuration, totalCost, fitnessScore, t, onTimelineUpdate }) {
    const [timeline, setTimeline] = useState(initialTimeline || [])
    const [selectedPOI, setSelectedPOI] = useState(null)
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [deleteConfirmIndex, setDeleteConfirmIndex] = useState(null)

    if (!timeline || timeline.length === 0) {
        return null
    }

    const formatTime = (minutes) => {
        const hours = Math.floor(minutes / 60)
        const mins = Math.round(minutes % 60)
        return `${hours.toString().padStart(2, '0')}h ${mins.toString().padStart(2, '0')}m`
    }

    const formatCurrency = (amount) => {
        return `S/ ${amount.toFixed(2)}`
    }

    const renderStars = (rating) => {
        const stars = []
        const fullStars = Math.floor(rating)
        const hasHalfStar = rating % 1 >= 0.5

        for (let i = 0; i < 5; i++) {
            if (i < fullStars) {
                stars.push(<span key={i} style={{ color: '#fbbf24' }}>★</span>)
            } else if (i === fullStars && hasHalfStar) {
                stars.push(<span key={i} style={{ color: '#fbbf24' }}>⯨</span>)
            } else {
                stars.push(<span key={i} style={{ color: '#d1d5db' }}>★</span>)
            }
        }
        return stars
    }

    const firstPOITravelTime = timeline[0]?.travel_time || 0
    const displayTravelTime = firstPOITravelTime > 0 ? formatTime(firstPOITravelTime) : "Calculando..."

    const handleDeletePOI = (index) => {
        const newTimeline = timeline.filter((_, i) => i !== index)
        setTimeline(newTimeline)
        setDeleteConfirmIndex(null)

        if (onTimelineUpdate) {
            onTimelineUpdate(newTimeline)
        }
    }

    const handleReorder = (fromIndex, toIndex) => {
        const newTimeline = [...timeline]
        const [movedItem] = newTimeline.splice(fromIndex, 1)
        newTimeline.splice(toIndex, 0, movedItem)
        setTimeline(newTimeline)

        if (onTimelineUpdate) {
            onTimelineUpdate(newTimeline)
        }
    }

    // SVG Icons
    const CalendarIcon = () => (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
        </svg>
    )

    const DragHandleIcon = () => (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="9" cy="5" r="1.5" />
            <circle cx="9" cy="12" r="1.5" />
            <circle cx="9" cy="19" r="1.5" />
            <circle cx="15" cy="5" r="1.5" />
            <circle cx="15" cy="12" r="1.5" />
            <circle cx="15" cy="19" r="1.5" />
        </svg>
    )

    const TrashIcon = () => (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            <line x1="10" y1="11" x2="10" y2="17" />
            <line x1="14" y1="11" x2="14" y2="17" />
        </svg>
    )

    const ClockIcon = () => (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
        </svg>
    )

    const CarIcon = () => (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M5 17h14v-2a3 3 0 0 0-3-3H8a3 3 0 0 0-3 3v2z" />
            <path d="M8 12V6a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v6" />
            <circle cx="8.5" cy="17.5" r="1.5" />
            <circle cx="15.5" cy="17.5" r="1.5" />
        </svg>
    )

    const WalkIcon = () => (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="4" r="2" />
            <path d="m16.5 17.5-1.5-5.5-3 3" />
            <path d="M10.5 12.5 8 10l-2 1" />
            <path d="m7 18 1.5-5.5" />
        </svg>
    )

    const MoneyIcon = () => (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8" />
            <path d="M12 18V6" />
        </svg>
    )

    const HourglassIcon = () => (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M5 22h14" />
            <path d="M5 2h14" />
            <path d="M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22" />
            <path d="M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2" />
        </svg>
    )

    return (
        <div className="timeline">
            <div className="timeline-header">
                <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <CalendarIcon /> {t.optimizedItinerary}
                </h2>
                <div className="timeline-stats">
                    <div className="stat-item">
                        <div className="stat-value">{timeline.length}</div>
                        <div className="stat-label">{t.places}</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">{displayTravelTime}</div>
                        <div className="stat-label">{t.travelToFirst || "Viaje al 1er lugar"}</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">{formatCurrency(totalCost)}</div>
                        <div className="stat-label">{t.cost}</div>
                    </div>
                </div>
            </div>

            {timeline.map((item, index) => (
                <div
                    key={index}
                    className="timeline-item-wrapper"
                    draggable
                    onDragStart={(e) => e.dataTransfer.setData('index', index)}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                        e.preventDefault()
                        const fromIndex = parseInt(e.dataTransfer.getData('index'))
                        handleReorder(fromIndex, index)
                    }}
                >
                    {/* Drag Handle */}
                    <div className="timeline-drag-handle">
                        <DragHandleIcon />
                    </div>

                    {/* Timeline Number */}
                    <div className="timeline-number">
                        {index + 1}
                    </div>

                    {/* Clickable Card Content */}
                    <div
                        className="timeline-item-card"
                        onClick={() => {
                            setSelectedPOI(item)
                            setIsModalOpen(true)
                        }}
                    >
                        <div className="timeline-content">
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                                <div className="timeline-poi-name">{item.poi_name}</div>
                                <div style={{ fontSize: '0.9rem' }}>
                                    {renderStars(item.rating || 0)}
                                </div>
                            </div>

                            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                                <span className="badge badge-category">{t[item.category] || item.category}</span>
                                <span className="badge badge-district">{item.district}</span>
                            </div>

                            <div className="timeline-details">
                                <div className="timeline-detail">
                                    <ClockIcon />
                                    <span>
                                        <strong>{t.arrival}:</strong> {item.arrival_time}
                                    </span>
                                </div>

                                <div className="timeline-detail">
                                    <ClockIcon />
                                    <span>
                                        <strong>{t.departure}:</strong> {item.departure_time}
                                    </span>
                                </div>

                                <div className="timeline-detail" title="Tiempo que pasarás dentro de este lugar">
                                    <HourglassIcon />
                                    <span>
                                        <strong>{t.visitTime || "Tiempo en el lugar"}:</strong> {item.visit_duration} min
                                    </span>
                                </div>

                                {item.travel_time > 0 && (
                                    <div className="timeline-detail" title="Tiempo de viaje desde el lugar anterior">
                                        {item.transport_mode === 'driving-car' ? <CarIcon /> : <WalkIcon />}
                                        <span>
                                            <strong>{t.travelTime || "Viaje"}:</strong> {item.travel_time} min
                                        </span>
                                    </div>
                                )}

                                {item.wait_time > 0 && (
                                    <div className="timeline-detail" title="Tiempo de espera porque el lugar aún no abre">
                                        <HourglassIcon />
                                        <span>
                                            <strong>{t.waitingTime || "Espera (lugar cerrado)"}:</strong> {item.wait_time} min
                                        </span>
                                    </div>
                                )}

                                {!item.is_free && (
                                    <div className="timeline-detail">
                                        <MoneyIcon />
                                        <span>
                                            <strong>{t.price}:</strong> {formatCurrency(item.price)}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Delete Button */}
                    <button
                        className="timeline-delete-btn"
                        onClick={(e) => {
                            e.stopPropagation()
                            setDeleteConfirmIndex(index)
                        }}
                        title="Eliminar del itinerario"
                    >
                        <TrashIcon />
                    </button>
                </div>
            ))}

            {/* Delete Confirmation Modal */}
            {deleteConfirmIndex !== null && (
                <div className="delete-confirm-overlay" onClick={() => setDeleteConfirmIndex(null)}>
                    <div className="delete-confirm-modal" onClick={(e) => e.stopPropagation()}>
                        <h3>¿Eliminar este lugar del itinerario?</h3>
                        <p className="delete-confirm-poi-name">{timeline[deleteConfirmIndex]?.poi_name}</p>
                        <p className="delete-confirm-message">
                            Esta acción eliminará este lugar de tu itinerario optimizado.
                        </p>
                        <div className="delete-confirm-actions">
                            <button
                                className="btn-cancel"
                                onClick={() => setDeleteConfirmIndex(null)}
                            >
                                Cancelar
                            </button>
                            <button
                                className="btn-confirm-delete"
                                onClick={() => handleDeletePOI(deleteConfirmIndex)}
                            >
                                Sí, eliminar
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* POI Detail Modal */}
            <POIDetailModal
                poi={selectedPOI}
                isOpen={isModalOpen}
                onClose={() => {
                    setIsModalOpen(false)
                    setSelectedPOI(null)
                }}
                t={t}
            />
        </div>
    )
}

export default Timeline
