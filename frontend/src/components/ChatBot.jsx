import { useState, useRef, useEffect } from 'react'
import '../chatbot.css'

/**
 * Floating Chatbot Widget Component
 * 
 * A collapsible chat interface that integrates with the TouristGen chatbot API.
 * Features:
 * - Floating toggle button in bottom-right corner
 * - Expandable chat panel
 * - Session-based conversation persistence
 * - Route generation trigger when parameters are complete
 */
function ChatBot({ t, language, onRouteGenerated }) {
    const [isOpen, setIsOpen] = useState(false)
    const [messages, setMessages] = useState([])
    const [inputValue, setInputValue] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [isGenerating, setIsGenerating] = useState(false)  // Separate flag for route generation
    const [sessionId, setSessionId] = useState(null)
    const [isReadyToGenerate, setIsReadyToGenerate] = useState(false)
    const [extractedParams, setExtractedParams] = useState(null)
    const abortControllerRef = useRef(null)

    const messagesEndRef = useRef(null)
    const inputRef = useRef(null)

    // Scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    // Focus input when chat opens
    useEffect(() => {
        if (isOpen && inputRef.current) {
            inputRef.current.focus()
        }
    }, [isOpen])

    // Load session from sessionStorage
    useEffect(() => {
        const savedSession = sessionStorage.getItem('chatbot_session')
        if (savedSession) {
            try {
                const { sessionId, messages } = JSON.parse(savedSession)
                setSessionId(sessionId)
                setMessages(messages)
            } catch (e) {
                console.error('Error loading chat session:', e)
            }
        }
    }, [])

    // Save session to sessionStorage
    useEffect(() => {
        if (sessionId && messages.length > 0) {
            sessionStorage.setItem('chatbot_session', JSON.stringify({ sessionId, messages }))
        }
    }, [sessionId, messages])

    const handleSend = async () => {
        if (!inputValue.trim() || isLoading) return

        const userMessage = inputValue.trim()
        setInputValue('')

        // Add user message to chat
        setMessages(prev => [...prev, { role: 'user', content: userMessage }])
        setIsLoading(true)

        try {
            const response = await fetch('http://localhost:8000/api/chat/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMessage,
                    session_id: sessionId
                })
            })

            if (!response.ok) {
                throw new Error('Error al enviar mensaje')
            }

            const data = await response.json()

            // Update session ID
            if (data.session_id) {
                setSessionId(data.session_id)
            }

            // Add assistant response
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.assistant_message
            }])

            // Check if ready to generate route
            setIsReadyToGenerate(data.is_ready_to_generate)
            setExtractedParams(data.extracted_params)

        } catch (error) {
            console.error('Chatbot error:', error)
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Lo siento, hubo un error. Por favor intenta de nuevo.'
            }])
        } finally {
            setIsLoading(false)
        }
    }

    const handleGenerateRoute = async () => {
        if (!sessionId || !isReadyToGenerate) return

        // Create AbortController for this request
        abortControllerRef.current = new AbortController()

        setIsLoading(true)
        setIsGenerating(true)
        console.log('[ChatBot] Generating route with session_id:', sessionId)

        try {
            const response = await fetch('http://localhost:8000/api/chat/generate-route', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId }),
                signal: abortControllerRef.current.signal
            })

            console.log('[ChatBot] Generate route response status:', response.status)

            if (!response.ok) {
                const errorData = await response.json()
                console.error('[ChatBot] Generate route error:', errorData)
                throw new Error(errorData.detail || 'Error al generar ruta')
            }

            const data = await response.json()
            console.log('[ChatBot] Generate route data:', data)

            // The response has { success: true, session_id, route: {...} }
            // We need to pass route to the parent (the actual route data)
            if (onRouteGenerated && data.route) {
                console.log('[ChatBot] Calling onRouteGenerated with route data')
                onRouteGenerated(data.route)

                // Add success message
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: '¡Ruta generada! Puedes verla en el mapa.'
                }])

                // Reset for new conversation
                setIsReadyToGenerate(false)
            } else {
                console.error('[ChatBot] No route data in response or onRouteGenerated not provided')
                throw new Error('No se recibió la ruta del servidor')
            }

        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('[ChatBot] Route generation cancelled by user')
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: 'Generación de ruta cancelada. Puedes intentar de nuevo cuando quieras.'
                }])
            } else {
                console.error('[ChatBot] Route generation error:', error)
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: `Error: ${error.message}. Por favor intenta de nuevo.`
                }])
            }
        } finally {
            setIsLoading(false)
            setIsGenerating(false)
            abortControllerRef.current = null
        }
    }

    const handleCancelGeneration = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort()
        }
    }

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    const handleClearChat = () => {
        setMessages([])
        setSessionId(null)
        setIsReadyToGenerate(false)
        setExtractedParams(null)
        sessionStorage.removeItem('chatbot_session')
    }

    const chatbotText = {
        es: {
            title: 'Asistente Virtual',
            placeholder: 'Escribe tu mensaje...',
            send: 'Enviar',
            generateRoute: '¡Generar Ruta!',
            thinking: 'Pensando...',
            clear: 'Nueva conversación',
            welcome: '¡Hola! Soy tu asistente de turismo. Cuéntame qué tipo de paseo te gustaría hacer en Lima.'
        },
        en: {
            title: 'Virtual Assistant',
            placeholder: 'Type your message...',
            send: 'Send',
            generateRoute: 'Generate Route!',
            thinking: 'Thinking...',
            clear: 'New conversation',
            welcome: 'Hello! I\'m your tourism assistant. Tell me what kind of tour you\'d like in Lima.'
        }
    }

    const texts = chatbotText[language] || chatbotText.es

    return (
        <>
            {/* Toggle Button */}
            <button
                className={`chatbot-toggle ${isOpen ? 'chatbot-toggle--open' : ''}`}
                onClick={() => setIsOpen(!isOpen)}
                title={texts.title}
            >
                {isOpen ? (
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                ) : (
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                )}
            </button>

            {/* Chat Panel */}
            {isOpen && (
                <div className="chatbot-panel">
                    {/* Header */}
                    <div className="chatbot-header">
                        <div className="chatbot-header-title">
                            <span className="chatbot-icon">🤖</span>
                            <h3>{texts.title}</h3>
                        </div>
                        <button
                            className="chatbot-clear-btn"
                            onClick={handleClearChat}
                            title={texts.clear}
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
                                <path d="M3 3v5h5"></path>
                            </svg>
                        </button>
                    </div>

                    {/* Messages */}
                    <div className="chatbot-messages">
                        {messages.length === 0 && (
                            <div className="chatbot-welcome">
                                <span className="chatbot-welcome-icon">👋</span>
                                <p>{texts.welcome}</p>
                            </div>
                        )}
                        {messages.map((msg, index) => {
                            // Simple markdown parser for bold text
                            const formatMessage = (text) => {
                                return text
                                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                    .replace(/\n/g, '<br/>')
                            }

                            return (
                                <div
                                    key={index}
                                    className={`chatbot-message chatbot-message--${msg.role}`}
                                    dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }}
                                />
                            )
                        })}
                        {isLoading && (
                            <div className="chatbot-message chatbot-message--assistant chatbot-message--loading">
                                <span className="chatbot-typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </span>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Generate Route Button */}
                    {isReadyToGenerate && !isLoading && (
                        <div className="chatbot-generate-banner">
                            <button
                                className="chatbot-generate-btn"
                                onClick={handleGenerateRoute}
                            >
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
                                </svg>
                                {texts.generateRoute}
                            </button>
                        </div>
                    )}

                    {/* Cancel Button - shown during route generation */}
                    {isGenerating && (
                        <div className="chatbot-generate-banner">
                            <button
                                className="chatbot-cancel-btn"
                                onClick={handleCancelGeneration}
                            >
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="12" cy="12" r="10"></circle>
                                    <line x1="15" y1="9" x2="9" y2="15"></line>
                                    <line x1="9" y1="9" x2="15" y2="15"></line>
                                </svg>
                                Cancelar Generación
                            </button>
                        </div>
                    )}

                    {/* Input Area */}
                    <div className="chatbot-input-area">
                        <input
                            ref={inputRef}
                            type="text"
                            className="chatbot-input"
                            placeholder={texts.placeholder}
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyPress={handleKeyPress}
                            disabled={isLoading}
                        />
                        <button
                            className="chatbot-send-btn"
                            onClick={handleSend}
                            disabled={!inputValue.trim() || isLoading}
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <line x1="22" y1="2" x2="11" y2="13"></line>
                                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                            </svg>
                        </button>
                    </div>
                </div>
            )}
        </>
    )
}

export default ChatBot
