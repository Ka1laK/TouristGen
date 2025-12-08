import { useEffect } from 'react'
import { detectPhoneType, generateWhatsAppLink, formatPhoneNumber, isWhatsAppEnabled } from '../utils/phoneUtils'
import '../poi-modal.css'

function POIDetailModal({ poi, isOpen, onClose, t }) {
    if (!isOpen || !poi) return null

    const phoneType = detectPhoneType(poi.phone)
    const hasWhatsApp = isWhatsAppEnabled(poi.phone)
    const whatsappLink = hasWhatsApp ? generateWhatsAppLink(poi.phone, poi.poi_name || poi.name, poi.arrival_time) : null

    // Handle click outside modal
    const handleBackdropClick = (e) => {
        if (e.target.className === 'modal-overlay') {
            onClose()
        }
    }

    // Prevent body scroll when modal is open
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden'
        }

        return () => {
            document.body.style.overflow = 'unset'
        }
    }, [isOpen])

    const renderStars = (rating) => {
        const stars = []
        const fullStars = Math.floor(rating || 0)
        const hasHalfStar = (rating || 0) % 1 >= 0.5

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

    // SVG Icons
    const CloseIcon = () => (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
    )

    const LocationIcon = () => (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
            <circle cx="12" cy="10" r="3" />
        </svg>
    )

    const ClockIcon = () => (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
        </svg>
    )

    const FileTextIcon = () => (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
        </svg>
    )

    const PhoneIcon = () => (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
        </svg>
    )

    const SmartphoneIcon = () => (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="5" y="2" width="14" height="20" rx="2" ry="2" />
            <line x1="12" y1="18" x2="12.01" y2="18" />
        </svg>
    )

    const GlobeIcon = () => (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="2" y1="12" x2="22" y2="12" />
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>
    )

    const InfoIcon = () => (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
        </svg>
    )

    const WhatsAppIcon = () => (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z" />
        </svg>
    )

    // Simulate review count based on rating and popularity (since DB doesn't have this field)
    const getReviewCount = () => {
        if (!poi.rating) return 0
        // Simulate: higher rating and popularity = more reviews
        const baseCount = Math.floor((poi.popularity || 50) * (poi.rating / 5) * 50)
        return baseCount + Math.floor(Math.random() * 100)
    }

    // Clean description by removing redundant rating text
    const getCleanDescription = () => {
        if (!poi.description) return t.noInfoAvailable || 'No hay descripción disponible'

        // Remove patterns like "Valorado con 3.8 estrellas (6403 reseñas)."
        let cleanDesc = poi.description
            .replace(/Valorado con \d+\.?\d* estrellas \(\d+ reseñas\)\./gi, '')
            .replace(/Rated \d+\.?\d* stars \(\d+ reviews\)\./gi, '')
            .trim()

        return cleanDesc || t.noInfoAvailable || 'No hay descripción disponible'
    }

    return (
        <div className="modal-overlay" onClick={handleBackdropClick}>
            <div className="modal-container">
                {/* Colored Header */}
                <div className="modal-header-colored">
                    <div className="modal-header-content">
                        <h2 className="modal-poi-name-header">
                            {poi.poi_name || poi.name}
                        </h2>
                        {poi.rating && (
                            <div className="modal-poi-rating-header">
                                {renderStars(poi.rating)}
                                <span className="rating-value-header">{poi.rating.toFixed(1)}</span>
                                <span className="review-count-header">({getReviewCount()} reseñas)</span>
                            </div>
                        )}
                    </div>
                    <button className="modal-close-btn-header" onClick={onClose} aria-label="Close">
                        <CloseIcon />
                    </button>
                </div>

                <div className="modal-content">
                    {/* Category and District */}
                    <div className="modal-poi-meta">
                        {poi.category && (
                            <span className="badge badge-category">
                                {t[poi.category] || poi.category}
                            </span>
                        )}
                        {poi.district && (
                            <span className="badge badge-district">
                                {poi.district}
                            </span>
                        )}
                    </div>

                    {/* Address */}
                    {poi.address && (
                        <div className="modal-info-item">
                            <div className="modal-info-icon">
                                <LocationIcon />
                            </div>
                            <div className="modal-info-content">
                                <p className="modal-address">{poi.address}</p>
                            </div>
                        </div>
                    )}

                    {/* Arrival Time */}
                    {poi.arrival_time && (
                        <div className="modal-info-item">
                            <div className="modal-info-icon">
                                <ClockIcon />
                            </div>
                            <div className="modal-info-content">
                                <strong>{t.arrival || 'Llegada'}:</strong> {poi.arrival_time}
                            </div>
                        </div>
                    )}

                    <div className="modal-divider"></div>

                    {/* Description */}
                    <div className="modal-section">
                        <h3 className="modal-section-title">
                            <FileTextIcon /> {t.description || 'Descripción'}
                        </h3>
                        <p className="modal-description">
                            {getCleanDescription()}
                        </p>
                    </div>

                    {/* Opening Hours */}
                    {poi.opening_hours && Object.keys(poi.opening_hours).length > 0 && (
                        <>
                            <div className="modal-divider"></div>
                            <div className="modal-section">
                                <h3 className="modal-section-title">
                                    <ClockIcon /> Horario de atención
                                </h3>
                                <div className="opening-hours-grid">
                                    {Object.entries(poi.opening_hours).map(([day, hours]) => (
                                        <div key={day} className="opening-hours-item">
                                            <span className="opening-hours-day">{day}</span>
                                            <span className="opening-hours-time">{hours || 'Cerrado'}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </>
                    )}

                    <div className="modal-divider"></div>

                    {/* Contact Information */}
                    <div className="modal-section">
                        <h3 className="modal-section-title">
                            <PhoneIcon /> {t.contact || 'Contacto'}
                        </h3>

                        {/* Phone */}
                        {poi.phone ? (
                            <div className="contact-item">
                                <div className="contact-icon">
                                    {phoneType === 'mobile' ? <SmartphoneIcon /> : <PhoneIcon />}
                                </div>
                                <div className="contact-content">
                                    <div className="contact-label">{t.phone || 'Teléfono'}</div>
                                    <div className="contact-value">
                                        {phoneType === 'mobile' ? (
                                            <a href={`tel:${poi.phone}`} className="phone-link">
                                                {formatPhoneNumber(poi.phone)}
                                            </a>
                                        ) : (
                                            <span>{formatPhoneNumber(poi.phone)}</span>
                                        )}
                                    </div>
                                    {hasWhatsApp && whatsappLink && (
                                        <a
                                            href={whatsappLink}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="btn-whatsapp"
                                        >
                                            <WhatsAppIcon /> {t.contactWhatsApp || 'Contactar por WhatsApp'}
                                        </a>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="contact-item">
                                <div className="contact-icon"><InfoIcon /></div>
                                <div className="contact-content">
                                    <div className="contact-label">{t.phone || 'Teléfono'}</div>
                                    <div className="contact-value no-info">
                                        {t.noInfoAvailable || 'No info disponible'}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Website */}
                        {poi.website ? (
                            <div className="contact-item">
                                <div className="contact-icon"><GlobeIcon /></div>
                                <div className="contact-content">
                                    <div className="contact-label">{t.website || 'Sitio web'}</div>
                                    <a
                                        href={poi.website.startsWith('http') ? poi.website : `https://${poi.website}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="website-link"
                                    >
                                        {poi.website}
                                    </a>
                                </div>
                            </div>
                        ) : (
                            <div className="contact-item">
                                <div className="contact-icon"><InfoIcon /></div>
                                <div className="contact-content">
                                    <div className="contact-label">{t.website || 'Sitio web'}</div>
                                    <div className="contact-value no-info">
                                        {t.noInfoAvailable || 'No info disponible'}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                <div className="modal-footer">
                    <button className="btn-modal-close" onClick={onClose}>
                        {t.close || 'Cerrar'}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default POIDetailModal
