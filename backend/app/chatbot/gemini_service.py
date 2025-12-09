"""
Gemini 1.5 Flash integration service for TouristGen Chatbot
"""
import google.generativeai as genai
from typing import Optional, Dict, Any
import json
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# System prompt for parameter extraction (will be completed with current date at runtime)
SYSTEM_PROMPT_TEMPLATE = """Eres un asistente de planificación turística para Lima y Callao, Perú.
Tu trabajo es ayudar al usuario a planificar una salida turística extrayendo los parámetros necesarios de forma conversacional.

INFORMACIÓN DEL SISTEMA:
- Fecha actual: {current_date}
- Día actual: {current_day_spanish} ({current_day_english})

PARÁMETROS A EXTRAER:
1. max_duration: Duración del paseo en MINUTOS (mínimo 60, máximo 720). Ejemplos: "3 horas" = 180, "medio día" = 240, "todo el día" = 480
2. max_budget: Presupuesto en SOLES (S/). Ejemplos: "económico/poco" = 50, "moderado" = 150, "sin límite" = 500
3. start_time: Hora de inicio en formato HH:MM (24h). Ejemplos: "mañana temprano" = "09:00", "tarde" = "14:00", "2pm" = "14:00"
4. day_of_week: Día de la semana EN INGLÉS. REGLAS DE INFERENCIA:
   - "hoy", "ahora", "en unos minutos", "en un rato", "más tarde", "ahorita" → {current_day_english}
   - "mañana" → {tomorrow_day_english}
   - "pasado mañana" → {day_after_tomorrow_english}
   - "este lunes", "el lunes", etc. → el próximo día mencionado (Monday, Tuesday, etc.)
   - VALIDACIÓN: Si el usuario menciona un día que YA PASÓ esta semana, responde amablemente: "Parece que [día] ya pasó esta semana. ¿Te refieres al próximo [día]?" y NO extraigas el día hasta que confirme.
5. preferred_districts: Lista de distritos de Lima/Callao. Distritos válidos: Miraflores, Barranco, Lima, San Isidro, Callao, Surco, San Miguel, Pueblo Libre, Chorrillos, La Molina, San Borja, Jesús María, Lince, Magdalena, Breña, Los Olivos, Comas, San Juan de Lurigancho, Ate, La Victoria
6. mandatory_categories: Tipos de lugares a INCLUIR. Categorías válidas: Museum, Park, Beach, Shopping, Dining, Religious, Landmark, Zoo, Cultural
7. avoid_categories: Tipos de lugares a EVITAR (mismas categorías). IMPORTANTE: Si el usuario dice que NO quiere una categoría que antes dijo que SÍ quería, muévela a avoid_categories.
8. transport_mode: "driving-car" (auto/taxi) o "foot-walking" (caminando)
9. user_pace: "slow" (lento/tranquilo), "medium" (normal), "fast" (rápido)
10. start_location_text: Punto de PARTIDA del tour (solo para cálculo de ruta, NO implica que quieran visitar ese distrito)
11. place_references: Lista de NOMBRES de lugares específicos que el usuario QUIERE VISITAR (ej: "Larcomar", "Parque Kennedy"). NO incluyas aquí el punto de partida.

IMPORTANTE SOBRE DISTRITOS:
- El punto de partida (start_location_text) NO define los distritos de interés
- SIEMPRE pregunta explícitamente en qué distritos o zonas de Lima le gustaría pasear al usuario
- Solo infiere preferred_districts cuando el usuario mencione lugares que QUIERE VISITAR o distritos explícitamente
- NO des por sentado que el distrito del punto de partida es donde quieren turistear

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
3. Si faltan parámetros OBLIGATORIOS (duration, budget, start_time, day_of_week, districts), pregunta por ellos de forma natural
4. SIEMPRE pregunta por los distritos de interés, incluso si el usuario mencionó un punto de partida
5. NO inventes valores, solo extrae lo que el usuario menciona explícitamente
6. Distingue entre PUNTO DE PARTIDA (dónde empiezan) y LUGARES A VISITAR (dónde quieren turistear)
7. Responde SIEMPRE en formato JSON con esta estructura exacta:

{{
  "assistant_message": "Tu respuesta amable al usuario",
  "extracted_params": {{
    "max_duration": null o número en minutos,
    "max_budget": null o número en soles,
    "start_time": null o "HH:MM",
    "day_of_week": null o "Monday"/"Tuesday"/"Wednesday"/"Thursday"/"Friday"/"Saturday"/"Sunday",
    "user_pace": null o "slow"/"medium"/"fast",
    "mandatory_categories": [],
    "avoid_categories": [],
    "preferred_districts": [],
    "transport_mode": null o "driving-car"/"foot-walking",
    "start_location_text": null o texto,
    "place_references": []
  }},
  "missing_params": ["lista de parámetros que faltan"]
}}

PARÁMETROS OBLIGATORIOS: max_duration, max_budget, start_time, day_of_week, preferred_districts (al menos uno)
"""


# Day name mappings
DAY_NAMES_SPANISH = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo"
}

DAY_NAMES_ENGLISH = {
    0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
    4: "Friday", 5: "Saturday", 6: "Sunday"
}


def get_system_prompt_with_date() -> str:
    """
    Generate the system prompt with current date information injected.
    This enables Gemini to correctly infer day_of_week from temporal expressions.
    """
    now = datetime.now()
    today_idx = now.weekday()  # Monday = 0, Sunday = 6
    
    tomorrow = now + timedelta(days=1)
    tomorrow_idx = tomorrow.weekday()
    
    day_after = now + timedelta(days=2)
    day_after_idx = day_after.weekday()
    
    return SYSTEM_PROMPT_TEMPLATE.format(
        current_date=now.strftime("%d/%m/%Y"),
        current_day_spanish=DAY_NAMES_SPANISH[today_idx],
        current_day_english=DAY_NAMES_ENGLISH[today_idx],
        tomorrow_day_english=DAY_NAMES_ENGLISH[tomorrow_idx],
        day_after_tomorrow_english=DAY_NAMES_ENGLISH[day_after_idx]
    )


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
                "missing_params": ["max_duration", "max_budget", "start_time", "day_of_week", "preferred_districts"]
            }
        
        try:
            # Build conversation context
            context_messages = []
            
            if conversation_history:
                for msg in conversation_history[-6:]:  # Last 6 messages for context
                    context_messages.append(f"{msg['role'].upper()}: {msg['content']}")
            
            context_messages.append(f"USER: {user_message}")
            
            # Generate prompt with current date information
            system_prompt = get_system_prompt_with_date()
            
            # Create the prompt
            full_prompt = f"""{system_prompt}

HISTORIAL DE CONVERSACIÓN:
{chr(10).join(context_messages)}

Responde en formato JSON:"""

            # Call Gemini
            response = self.model.generate_content(full_prompt)
            
            # Check if response was blocked by safety filters
            if not response.candidates or not response.candidates[0].content.parts:
                logger.warning("Gemini response blocked or empty - likely safety filter")
                return {
                    "assistant_message": "Ocurrió un problema con la petición. ¿Podrías reformular tu mensaje? Estoy listo para ayudarte a planificar tu paseo.",
                    "extracted_params": {},
                    "missing_params": ["max_duration", "max_budget", "start_time", "day_of_week", "preferred_districts"]
                }
            
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
            return {
                "assistant_message": "Disculpa, tuve un problema procesando tu mensaje. ¿Podrías intentar de nuevo?",
                "extracted_params": {},
                "missing_params": ["max_duration", "max_budget", "start_time", "day_of_week", "preferred_districts"]
            }
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return {
                "assistant_message": "Hubo un problema técnico. Por favor intenta de nuevo con tu solicitud.",
                "extracted_params": {},
                "missing_params": ["max_duration", "max_budget", "start_time", "day_of_week", "preferred_districts"]
            }
