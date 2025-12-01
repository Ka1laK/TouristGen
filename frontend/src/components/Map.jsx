import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import '../map-markers.css'

// Fix for default marker icons in React
import icon from 'leaflet/dist/images/marker-icon.png'
import iconShadow from 'leaflet/dist/images/marker-shadow.png'

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
})

L.Marker.prototype.options.icon = DefaultIcon

function Map({ route, recommendations, step, startLocation }) {
    const mapRef = useRef(null)
    const mapInstanceRef = useRef(null)
    const markersRef = useRef([])
    const polylinesRef = useRef([])

    useEffect(() => {
        // Initialize map
        if (!mapInstanceRef.current) {
            mapInstanceRef.current = L.map(mapRef.current).setView([-12.0464, -77.0428], 13)

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(mapInstanceRef.current)
        }

        return () => {
            // Cleanup on unmount
            if (mapInstanceRef.current) {
                mapInstanceRef.current.remove()
                mapInstanceRef.current = null
            }
        }
    }, [])

    useEffect(() => {
        if (!mapInstanceRef.current) return

        // Clear existing markers and polylines
        markersRef.current.forEach(marker => marker.remove())
        polylinesRef.current.forEach(polyline => polyline.remove())
        markersRef.current = []
        polylinesRef.current = []

        const bounds = []

        // 1. Draw Start Location
        if (startLocation && startLocation.latitude && startLocation.longitude) {
            const startMarker = L.marker([startLocation.latitude, startLocation.longitude], {
                icon: L.divIcon({
                    className: 'custom-marker start-marker',
                    html: `<div class="marker-pin start-pin">
                    <div class="marker-icon">🏠</div>
                   </div>`,
                    iconSize: [30, 42],
                    iconAnchor: [15, 42]
                })
            })

            startMarker.bindPopup(`<strong>Inicio:</strong> ${startLocation.address}`)
            startMarker.addTo(mapInstanceRef.current)
            markersRef.current.push(startMarker)
            bounds.push([startLocation.latitude, startLocation.longitude])
        }

        // 2. Draw Recommendations (Step 1)
        if (step === 'recommendations' && recommendations) {
            recommendations.forEach((poi, index) => {
                const marker = L.marker([poi.latitude, poi.longitude], {
                    icon: L.divIcon({
                        className: 'custom-marker recommendation-marker',
                        html: `<div class="marker-pin recommendation-pin">
                        <div class="marker-number">${index + 1}</div>
                       </div>`,
                        iconSize: [30, 42],
                        iconAnchor: [15, 42]
                    })
                })

                marker.bindPopup(`
                    <div class="marker-popup">
                        <h3>${poi.name}</h3>
                        <p><strong>Categoría:</strong> ${poi.category}</p>
                        <p><strong>Distrito:</strong> ${poi.district}</p>
                        <p><strong>Rating:</strong> ${'⭐'.repeat(Math.round(poi.rating || 4))}</p>
                    </div>
                `)

                marker.addTo(mapInstanceRef.current)
                markersRef.current.push(marker)
                bounds.push([poi.latitude, poi.longitude])
            })
        }

        // 3. Draw Full Route (Step 2)
        if (step === 'routing' && route && route.route) {
            // Add numbered markers for each POI
            route.route.forEach((poi, index) => {
                const marker = L.marker([poi.latitude, poi.longitude], {
                    icon: L.divIcon({
                        className: 'custom-marker',
                        html: `<div class="marker-pin">
                    <div class="marker-number">${index + 1}</div>
                   </div>`,
                        iconSize: [30, 42],
                        iconAnchor: [15, 42]
                    })
                })

                marker.bindPopup(`
          <div class="marker-popup">
            <h3>${poi.name}</h3>
            <p><strong>Categoría:</strong> ${poi.category}</p>
            <p><strong>Distrito:</strong> ${poi.district}</p>
            <p><strong>Rating:</strong> ${'⭐'.repeat(Math.round(poi.rating || 4))}</p>
            <p><strong>Duración:</strong> ${poi.visit_duration} min</p>
          </div>
        `)

                marker.addTo(mapInstanceRef.current)
                markersRef.current.push(marker)
                bounds.push([poi.latitude, poi.longitude])
            })

            // Draw route lines with geometry if available
            if (route.route_geometry && route.route_geometry.length > 0) {
                route.route_geometry.forEach((segment, index) => {
                    if (segment && segment.coordinates && segment.coordinates.length > 0) {
                        const latlngs = segment.coordinates.map(coord => [coord[1], coord[0]])

                        const polyline = L.polyline(latlngs, {
                            color: '#10b981', // Green color
                            weight: 5,
                            opacity: 0.7,
                            smoothFactor: 1
                        })

                        polyline.addTo(mapInstanceRef.current)
                        polylinesRef.current.push(polyline)
                        latlngs.forEach(latlng => bounds.push(latlng))
                    }
                })
            } else {
                // Fallback lines
                for (let i = 0; i < route.route.length - 1; i++) {
                    const start = route.route[i]
                    const end = route.route[i + 1]
                    const polyline = L.polyline(
                        [[start.latitude, start.longitude], [end.latitude, end.longitude]],
                        { color: '#3b82f6', weight: 3, opacity: 0.5, dashArray: '10, 10' }
                    )
                    polyline.addTo(mapInstanceRef.current)
                    polylinesRef.current.push(polyline)
                }
            }
        }

        // Fit map to show all markers
        if (bounds.length > 0) {
            mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50] })
        } else if (!startLocation) {
            // Default view if nothing to show
            mapInstanceRef.current.setView([-12.0464, -77.0428], 13)
        }
    }, [route, recommendations, step, startLocation])

    return (
        <div style={{ position: 'relative', width: '100%', height: '100%' }}>
            <div ref={mapRef} style={{ width: '100%', height: '100%' }} />
            {step === 'search' && !startLocation && (
                <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    background: 'white',
                    padding: '2rem',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                    textAlign: 'center',
                    zIndex: 1000
                }}>
                    <h3 style={{ marginBottom: '0.5rem' }}>🗺️ Comienza tu aventura</h3>
                    <p style={{ color: '#64748b' }}>Ingresa tu ubicación o selecciona filtros para ver recomendaciones</p>
                </div>
            )}
        </div>
    )
}

export default Map
