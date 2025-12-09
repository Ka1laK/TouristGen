import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet-routing-machine'
import 'leaflet-routing-machine/dist/leaflet-routing-machine.css'
import '../map-markers.css'
import '../routing.css'

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

function Map({ route, recommendations, step, startLocation, language, t, onRouteTimes }) {
    const mapRef = useRef(null)
    const mapInstanceRef = useRef(null)
    const markersRef = useRef([])
    const polylinesRef = useRef([])
    const routeTimesProcessedRef = useRef(null) // Track processed route to prevent infinite loop

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

        // Remove routing control if exists
        if (mapInstanceRef.current.routingControl) {
            mapInstanceRef.current.removeControl(mapInstanceRef.current.routingControl)
            mapInstanceRef.current.routingControl = null
        }

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
        if (step === 'routing' && route && route.route && Array.isArray(route.route)) {
            // Create waypoints including start location
            const waypoints = []
            let hasStart = false

            if (startLocation && startLocation.latitude && startLocation.longitude) {
                waypoints.push(L.latLng(startLocation.latitude, startLocation.longitude))
                hasStart = true
            }

            route.route.forEach(poi => {
                if (poi && poi.latitude && poi.longitude) {
                    waypoints.push(L.latLng(poi.latitude, poi.longitude))
                }
            })

            // Add Routing Control
            if (waypoints.length > 0) {
                const routingControl = L.Routing.control({
                    waypoints: waypoints,
                    routeWhileDragging: false,
                    fitSelectedRoutes: true,
                    language: language,
                    containerClassName: 'routing-instructions',
                    lineOptions: {
                        styles: [{ color: '#6366f1', opacity: 0.8, weight: 6 }]
                    },
                    createMarker: function (i, waypoint, n) {
                        // Handle Start Location Marker
                        if (hasStart && i === 0) {
                            return L.marker(waypoint.latLng, {
                                icon: L.divIcon({
                                    className: 'custom-marker start-marker',
                                    html: `<div class="marker-pin start-pin">
                                    <div class="marker-icon">🏠</div>
                                   </div>`,
                                    iconSize: [30, 42],
                                    iconAnchor: [15, 42]
                                })
                            }).bindPopup(`<strong>Inicio:</strong> ${startLocation.address || 'Ubicación actual'}`)
                        }

                        // Handle POI Markers
                        const poiIndex = hasStart ? i - 1 : i
                        const poi = route.route[poiIndex]

                        if (!poi) return null

                        return L.marker(waypoint.latLng, {
                            icon: L.divIcon({
                                className: 'custom-marker',
                                html: `<div class="marker-pin">
                                    <div class="marker-number">${poiIndex + 1}</div>
                                   </div>`,
                                iconSize: [30, 42],
                                iconAnchor: [15, 42]
                            })
                        }).bindPopup(`
                            <div class="marker-popup">
                                <h3>${poi.name}</h3>
                                <p><strong>Categoría:</strong> ${poi.category}</p>
                                <p><strong>Distrito:</strong> ${poi.district}</p>
                                <p><strong>Rating:</strong> ${'⭐'.repeat(Math.round(poi.rating || 4))}</p>
                                <p><strong>Duración:</strong> ${poi.visit_duration} min</p>
                            </div>
                        `)
                    }
                }).addTo(mapInstanceRef.current)

                // SYNC FIX: Capture travel times from Leaflet Routing Machine (OSRM)
                // and pass them to parent for timeline synchronization
                routingControl.on('routesfound', function (e) {
                    const routes = e.routes
                    if (routes && routes.length > 0 && onRouteTimes) {
                        const selectedRoute = routes[0]

                        // Create a unique route ID based on waypoints to detect if we already processed this route
                        const routeId = selectedRoute.waypoints.map(wp =>
                            `${wp.latLng.lat.toFixed(4)},${wp.latLng.lng.toFixed(4)}`
                        ).join('|')

                        // Guard: Don't process if we already handled this exact route
                        if (routeTimesProcessedRef.current === routeId) {
                            console.log('[MAP SYNC] Route already processed, skipping')
                            return
                        }
                        routeTimesProcessedRef.current = routeId

                        // OSRM structure: route.instructions contains step-by-step with time per step
                        // We need to calculate time per leg (waypoint to waypoint)
                        const instructions = selectedRoute.instructions || []
                        const waypointIndices = selectedRoute.waypointIndices || []

                        // Calculate segment times between waypoints
                        const segmentTimes = []
                        let currentSegmentTime = 0
                        let currentWaypointIdx = 0

                        for (let i = 0; i < instructions.length; i++) {
                            const instruction = instructions[i]
                            currentSegmentTime += (instruction.time || 0)

                            // Check if this instruction ends at a waypoint
                            if (waypointIndices.includes(instruction.index) && i > 0) {
                                segmentTimes.push(Math.round(currentSegmentTime / 60))
                                currentSegmentTime = 0
                                currentWaypointIdx++
                            }
                        }
                        // Add the last segment
                        if (currentSegmentTime > 0) {
                            segmentTimes.push(Math.round(currentSegmentTime / 60))
                        }

                        // Fallback: if segmentTimes is empty, use total time divided by legs
                        const totalTime = Math.round(selectedRoute.summary.totalTime / 60)
                        const totalDistance = (selectedRoute.summary.totalDistance / 1000).toFixed(1)

                        if (segmentTimes.length === 0 && route && route.route) {
                            // Distribute total time proportionally
                            const numSegments = route.route.length + (hasStart ? 1 : 0)
                            const avgTime = Math.round(totalTime / numSegments)
                            for (let i = 0; i < numSegments; i++) {
                                segmentTimes.push(avgTime)
                            }
                        }

                        console.log('[MAP SYNC] OSRM Route Times:', {
                            segments: segmentTimes,
                            total: totalTime,
                            distance: totalDistance,
                            routeId: routeId.substring(0, 50) + '...'
                        })

                        // Pass to parent for timeline sync
                        onRouteTimes({
                            segmentTimes: segmentTimes,
                            totalTime: totalTime,
                            totalDistance: totalDistance,
                            hasStartLocation: hasStart
                        })
                    }
                })

                // Store control for cleanup
                mapInstanceRef.current.routingControl = routingControl
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
                    <h3 style={{ marginBottom: '0.5rem' }}>🗺️ {t?.startAdventure || 'Comienza tu aventura'}</h3>
                    <p style={{ color: '#64748b' }}>{t?.enterLocation || 'Ingresa tu ubicación o selecciona filtros para ver recomendaciones'}</p>
                </div>
            )}
        </div>
    )
}

export default Map
