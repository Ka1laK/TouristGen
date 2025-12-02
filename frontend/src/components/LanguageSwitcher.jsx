import React from 'react'

const LanguageSwitcher = ({ currentLanguage, onLanguageChange }) => {
    return (
        <div className="language-switcher">
            <button
                className={`lang-btn ${currentLanguage === 'es' ? 'active' : ''}`}
                onClick={() => onLanguageChange('es')}
                title="Español"
            >
                <span className="flag-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 750 500" width="24" height="16">
                        <rect width="750" height="500" fill="#c60b1e" />
                        <rect y="125" width="750" height="250" fill="#ffc400" />
                        <g transform="translate(200, 250) scale(0.5)">
                            <path d="M100,0 L100,100 M0,100 L200,100" stroke="#c60b1e" strokeWidth="10" />
                        </g>
                    </svg>
                </span>
                <span className="lang-code">ES</span>
            </button>
            <div className="divider"></div>
            <button
                className={`lang-btn ${currentLanguage === 'en' ? 'active' : ''}`}
                onClick={() => onLanguageChange('en')}
                title="English (US)"
            >
                <span className="flag-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1235 650" width="24" height="16">
                        <rect width="1235" height="650" fill="#b22234" />
                        <path d="M0,50H1235M0,150H1235M0,250H1235M0,350H1235M0,450H1235M0,550H1235" stroke="#fff" strokeWidth="50" />
                        <rect width="494" height="350" fill="#3c3b6e" />
                    </svg>
                </span>
                <span className="lang-code">EN</span>
            </button>
        </div>
    )
}

export default LanguageSwitcher
