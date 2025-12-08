"""
Gemini 1.5 Flash integration service for TouristGen Chatbot
"""
import google.generativeai as genai
from typing import Optional, Dict, Any
import json
import logging
import os

logger = logging.getLogger(__name__)


# System prompt for parameter extraction
SYSTEM_PROMPT = """Eres un asistente de planificación turística para Lima y Callao, Perú.
Tu trabajo es ayudar al usuario a planificar una salida turística extrayendo los parámetros necesarios de forma conversacional.

PARÁMETROS A EXTRAER:
1. max_duration: Duración del paseo en MINUTOS (mínimo 60, máximo 720). Ejemplos: "3 horas" = 180, "medio día" = 240, "todo el día" = 480
2. max_budget: Presupuesto en SOLES (S/). Ejemplos: "económico/poco" = 50, "moderado" = 150, "sin límite" = 500
3. start_time: Hora de inicio en formato HH:MM (24h). Ejemplos: "mañana" = "09:00", "tarde" = "14:00", "2pm" = "14:00"
4. preferred_districts: Lista de distritos de Lima/Callao. Distritos válidos: Miraflores, Barranco, Lima, San Isidro, Callao, Surco, San Miguel, Pueblo Libre, Chorrillos, La Molina, San Borja, Jesús María, Lince, Magdalena, Breña
5. mandatory_categories: Tipos de lugares a INCLUIR. Categorías válidas: Museum, Park, Beach, Shopping, Dining, Religious, Landmark, Zoo, Cultural
6. avoid_categories: Tipos de lugares a EVITAR (mismas categorías)
7. transport_mode: "driving-car" (auto/taxi) o "foot-walking" (caminando)
8. user_pace: "slow" (lento/tranquilo), "medium" (normal), "fast" (rápido)
9. start_location_text: Descripción textual del punto de partida

MAPEO DE INTENCIONES A CATEGORÍAS:
- "romántico/pareja/cita": Park, Dining, Cultural, Landmark
- "familiar/niños/familia": Park, Zoo, Museum, Beach
- "cultural/historia": Museum, Cultural, Religious, Landmark
- "aventura/naturaleza": Park, Beach
- "compras/shopping": Shopping, Dining
- "gastronómico/comida": Dining

INSTRUCCIONES:
1. Sé amable y conversacional en español
2. Extrae parámetros del mensaje del usuario
3. Si faltan parámetros OBLIGATORIOS (duration, budget, start_time, districts), pregunta por ellos de forma natural
4. NO inventes valores, solo extrae lo que el usuario menciona explícitamente
5. Responde SIEMPRE en formato JSON con esta estructura exacta:

{
  "assistant_message": "Tu respuesta amable al usuario",
  "extracted_params": {
    "max_duration": null o número en minutos,
    "max_budget": null o número en soles,
    "start_time": null o "HH:MM",
    "user_pace": null o "slow"/"medium"/"fast",
    "mandatory_categories": [],
    "avoid_categories": [],
    "preferred_districts": [],
    "transport_mode": null o "driving-car"/"foot-walking",
    "start_location_text": null o texto
  },
  "missing_params": ["lista de parámetros que faltan"]
}

PARÁMETROS OBLIGATORIOS: max_duration, max_budget, start_time, preferred_districts (al menos uno)
"""


class GeminiService:
    """Service for interacting with Gemini 1.5 Flash API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set. Chatbot will not work.")
            self.model = None
            return
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name="models/gemini-2.5-flash",
                generation_config={
                    "temperature": 0.3,  # Lower for more consistent extraction
                    "top_p": 0.95,
                    "max_output_tokens": 1024,
                    "response_mime_type": "application/json"
                }
            )
            logger.info("Gemini 2.5 Flash initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if Gemini service is available"""
        return self.model is not None
    
    async def process_message(
        self, 
        user_message: str, 
        conversation_history: list = None
    ) -> Dict[str, Any]:
        """
        Process a user message and extract parameters
        
        Args:
            user_message: The user's message
            conversation_history: List of previous messages for context
            
        Returns:
            Dict with assistant_message, extracted_params, missing_params
        """
        if not self.is_available():
            return {
                "assistant_message": "Lo siento, el servicio de chat no está disponible. Por favor configura GEMINI_API_KEY.",
                "extracted_params": {},
                "missing_params": ["max_duration", "max_budget", "start_time", "preferred_districts"]
            }
        
        try:
            # Build conversation context
            context_messages = []
            
            if conversation_history:
                for msg in conversation_history[-6:]:  # Last 6 messages for context
                    context_messages.append(f"{msg['role'].upper()}: {msg['content']}")
            
            context_messages.append(f"USER: {user_message}")
            
            # Create the prompt
            full_prompt = f"""{SYSTEM_PROMPT}

HISTORIAL DE CONVERSACIÓN:
{chr(10).join(context_messages)}

Responde en formato JSON:"""

            # Call Gemini
            response = self.model.generate_content(full_prompt)
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Handle potential markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            return {
                "assistant_message": result.get("assistant_message", ""),
                "extracted_params": result.get("extracted_params", {}),
                "missing_params": result.get("missing_params", [])
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Raw response: {response.text if 'response' in dir() else 'N/A'}")
            return {
                "assistant_message": "Disculpa, tuve un problema procesando tu mensaje. ¿Podrías intentar de nuevo?",
                "extracted_params": {},
                "missing_params": ["max_duration", "max_budget", "start_time", "preferred_districts"]
            }
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return {
                "assistant_message": f"Error al procesar el mensaje: {str(e)}",
                "extracted_params": {},
                "missing_params": ["max_duration", "max_budget", "start_time", "preferred_districts"]
            }
