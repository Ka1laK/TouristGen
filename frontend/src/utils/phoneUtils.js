/**
 * Phone utility functions for POI contact features
 */

/**
 * Detect phone type (mobile, landline, or unknown)
 * @param {string} phone - Phone number to analyze
 * @returns {string|null} - 'mobile', 'landline', 'unknown', or null
 */
export function detectPhoneType(phone) {
    if (!phone || typeof phone !== 'string') {
        return null;
    }

    // Remove spaces, hyphens, and parentheses for analysis
    const cleanPhone = phone.replace(/[\s\-()]/g, '');

    // Peru mobile pattern: +51 9XX XXX XXX (9 digits after country code)
    // Examples: +51923374843, +51 923 374 843
    const mobilePattern = /^\+519\d{8}$/;

    // Peru landline pattern: +51 1 XXXXXXX or +51 XX XXXXXX
    // Examples: +5112085830, +51 1 2085830
    const landlinePattern = /^\+51[1-9]\d{6,8}$/;

    if (mobilePattern.test(cleanPhone)) {
        return 'mobile';
    } else if (landlinePattern.test(cleanPhone) && !mobilePattern.test(cleanPhone)) {
        return 'landline';
    }

    return 'unknown';
}

/**
 * Generate WhatsApp link with pre-filled message
 * @param {string} phone - Phone number
 * @param {string} poiName - Name of the POI
 * @param {string} arrivalTime - Arrival time
 * @returns {string} - WhatsApp URL
 */
export function generateWhatsAppLink(phone, poiName, arrivalTime) {
    if (!phone) return null;

    // Remove ALL non-numeric characters (including +)
    const cleanPhone = phone.replace(/\D/g, '');

    // Generate message with conditional time
    const timeText = arrivalTime ? ` a las ${arrivalTime}` : '';
    const message = `Hola, estoy interesado en visitar ${poiName}${timeText}. Quisiera saber si hay disponibilidad y confirmar mi visita. ¡Gracias!`;
    const encodedMessage = encodeURIComponent(message);

    return `https://wa.me/${cleanPhone}?text=${encodedMessage}`;
}

/**
 * Format phone number for display
 * @param {string} phone - Phone number
 * @returns {string} - Formatted phone number
 */
export function formatPhoneNumber(phone) {
    if (!phone) return '';

    // Just return as-is for now, can add formatting logic later
    return phone;
}

/**
 * Check if phone is valid for WhatsApp
 * @param {string} phone - Phone number
 * @returns {boolean} - True if mobile number
 */
export function isWhatsAppEnabled(phone) {
    return detectPhoneType(phone) === 'mobile';
}
