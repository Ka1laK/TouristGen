import { useState } from 'react'

/**
 * MetricsPanel - Displays ACO optimization metrics with convergence chart
 * Shows fitness improvement over iterations and key algorithm parameters
 */
const MetricsPanel = ({ metrics, fitnessScore, numPois, totalDuration, totalCost, t }) => {
    const [expanded, setExpanded] = useState(false)
    
    if (!metrics) return null
    
    const { 
        algorithm = "ACO",
        iterations = 0,
        num_ants = 0,
        alpha = 0,
        beta = 0,
        evaporation_rate = 0,
        fitness_history = [],
        pois_evaluated = 0
    } = metrics

    // Calculate chart dimensions and data points
    const chartWidth = 280
    const chartHeight = 120
    const padding = { top: 10, right: 10, bottom: 25, left: 40 }
    const innerWidth = chartWidth - padding.left - padding.right
    const innerHeight = chartHeight - padding.top - padding.bottom

    // Extract best fitness values for the chart
    const fitnessValues = fitness_history.map(h => h.best_fitness || h.avg_fitness || 0)
    const maxFitness = Math.max(...fitnessValues, 1)
    const minFitness = Math.min(...fitnessValues, 0)
    const fitnessRange = maxFitness - minFitness || 1

    // Create SVG path for the line chart
    const createPath = () => {
        if (fitnessValues.length === 0) return ""
        
        const points = fitnessValues.map((value, index) => {
            const x = padding.left + (index / (fitnessValues.length - 1 || 1)) * innerWidth
            const y = padding.top + innerHeight - ((value - minFitness) / fitnessRange) * innerHeight
            return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
        })
        
        return points.join(' ')
    }

    // Create area fill path
    const createAreaPath = () => {
        if (fitnessValues.length === 0) return ""
        
        const linePath = createPath()
        const lastX = padding.left + innerWidth
        const firstX = padding.left
        const bottomY = padding.top + innerHeight
        
        return `${linePath} L ${lastX} ${bottomY} L ${firstX} ${bottomY} Z`
    }

    // Format large numbers
    const formatNumber = (num) => {
        if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
        return num.toFixed(1)
    }

    return (
        <div className="metrics-panel">
            <div className="metrics-header" onClick={() => setExpanded(!expanded)}>
                <div className="metrics-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M3 3v18h18"/>
                        <path d="M18 17V9"/>
                        <path d="M13 17V5"/>
                        <path d="M8 17v-3"/>
                    </svg>
                    <span>{t?.optimizationMetrics || 'Métricas de Optimización'}</span>
                </div>
                <svg 
                    className={`expand-icon ${expanded ? 'expanded' : ''}`}
                    width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                >
                    <polyline points="6 9 12 15 18 9"/>
                </svg>
            </div>

            {/* Summary Cards - Always visible */}
            <div className="metrics-cards">
                <div className="metric-card fitness">
                    <div className="metric-icon">🎯</div>
                    <div className="metric-content">
                        <span className="metric-value">{fitnessScore?.toFixed(1) || '0'}</span>
                        <span className="metric-label">{t?.fitnessScore || 'Fitness'}</span>
                    </div>
                </div>
                <div className="metric-card pois">
                    <div className="metric-icon">📍</div>
                    <div className="metric-content">
                        <span className="metric-value">{numPois || 0}</span>
                        <span className="metric-label">{t?.places || 'Lugares'}</span>
                    </div>
                </div>
                <div className="metric-card duration">
                    <div className="metric-icon">⏱️</div>
                    <div className="metric-content">
                        <span className="metric-value">{totalDuration || 0}</span>
                        <span className="metric-label">min</span>
                    </div>
                </div>
                <div className="metric-card cost">
                    <div className="metric-icon">💰</div>
                    <div className="metric-content">
                        <span className="metric-value">S/{totalCost?.toFixed(0) || '0'}</span>
                        <span className="metric-label">{t?.cost || 'Costo'}</span>
                    </div>
                </div>
            </div>

            {/* Expanded Section - Chart and Parameters */}
            <div className={`metrics-details ${expanded ? 'show' : ''}`}>
                {/* Convergence Chart */}
                <div className="convergence-chart">
                    <div className="chart-title">{t?.convergenceChart || 'Convergencia del Algoritmo'}</div>
                    <svg width={chartWidth} height={chartHeight} className="fitness-chart">
                        {/* Grid lines */}
                        <line 
                            x1={padding.left} y1={padding.top} 
                            x2={padding.left} y2={padding.top + innerHeight} 
                            stroke="#444" strokeWidth="1"
                        />
                        <line 
                            x1={padding.left} y1={padding.top + innerHeight} 
                            x2={padding.left + innerWidth} y2={padding.top + innerHeight} 
                            stroke="#444" strokeWidth="1"
                        />
                        
                        {/* Y-axis labels */}
                        <text x={padding.left - 5} y={padding.top + 5} fontSize="10" fill="#888" textAnchor="end">
                            {formatNumber(maxFitness)}
                        </text>
                        <text x={padding.left - 5} y={padding.top + innerHeight} fontSize="10" fill="#888" textAnchor="end">
                            {formatNumber(minFitness)}
                        </text>
                        
                        {/* X-axis labels */}
                        <text x={padding.left} y={chartHeight - 5} fontSize="10" fill="#888" textAnchor="start">
                            0
                        </text>
                        <text x={padding.left + innerWidth} y={chartHeight - 5} fontSize="10" fill="#888" textAnchor="end">
                            {iterations}
                        </text>
                        <text x={padding.left + innerWidth / 2} y={chartHeight - 5} fontSize="10" fill="#888" textAnchor="middle">
                            {t?.iterations || 'Iteraciones'}
                        </text>

                        {/* Area fill */}
                        <path
                            d={createAreaPath()}
                            fill="url(#areaGradient)"
                            opacity="0.3"
                        />
                        
                        {/* Line */}
                        <path
                            d={createPath()}
                            fill="none"
                            stroke="#4ade80"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            className="chart-line"
                        />
                        
                        {/* Gradient definition */}
                        <defs>
                            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#4ade80" stopOpacity="0.6"/>
                                <stop offset="100%" stopColor="#4ade80" stopOpacity="0"/>
                            </linearGradient>
                        </defs>
                    </svg>
                </div>

                {/* Algorithm Parameters */}
                <div className="algorithm-params">
                    <div className="params-title">{t?.algorithmParams || 'Parámetros ACO'}</div>
                    <div className="params-grid">
                        <div className="param-item">
                            <span className="param-label">🐜 {t?.ants || 'Hormigas'}</span>
                            <span className="param-value">{num_ants}</span>
                        </div>
                        <div className="param-item">
                            <span className="param-label">🔄 {t?.iterations || 'Iteraciones'}</span>
                            <span className="param-value">{iterations}</span>
                        </div>
                        <div className="param-item">
                            <span className="param-label">α {t?.pheromone || 'Feromona'}</span>
                            <span className="param-value">{alpha}</span>
                        </div>
                        <div className="param-item">
                            <span className="param-label">β {t?.heuristic || 'Heurística'}</span>
                            <span className="param-value">{beta}</span>
                        </div>
                        <div className="param-item">
                            <span className="param-label">ρ {t?.evaporation || 'Evaporación'}</span>
                            <span className="param-value">{(evaporation_rate * 100).toFixed(0)}%</span>
                        </div>
                        <div className="param-item">
                            <span className="param-label">📊 {t?.poisEvaluated || 'POIs evaluados'}</span>
                            <span className="param-value">{pois_evaluated}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default MetricsPanel
