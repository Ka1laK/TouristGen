import re
from typing import Optional, Tuple
from datetime import datetime
import logging
logger = logging.getLogger(__name__)
def parse_opening_hours(hours_dict: dict, day: str)-> Tuple[Optional[int], Optional[int]]:
    if not hours_dict or not isinstance(hours_dict, dict):
        # Sin información -> tratar como 24 horas
        return (0, 1440)
    day_hours = hours_dict.get(day)
    # Caso 1: null -> tratar como 24 horas (internamente)
    if day_hours is None:
        return (0, 1440)
    # Caso 2: "Abierto 24 horas" o similares
    if "24 horas" in day_hours.lower() or "24 hours" in day_hours.lower():
        return (0, 1440)
    # Caso 3: "Cerrado" o similar
    if "cerrado" in day_hours.lower() or "closed" in day_hours.lower():
        return (None, None) # Cerrado este día
    # Caso 4: Formato horario "HH:MM–HH:MM" o "HH:MM-HH:MM"
    # Nota: El guión puede ser – (Unicode) o - (ASCII)
    time_pattern = r'(\d{1,2}):(\d{2})\s*[–\-]\s*(\d{1,2}):(\d{2})'
    match = re.search(time_pattern, day_hours)
    if match:
        open_hour, open_min, close_hour, close_min = map(int, match.groups())
        opening_minutes = open_hour * 60 + open_min
        closing_minutes = close_hour * 60 + close_min
        # Manejar horarios que cruzan medianoche (ej: 22:00-02:00)
        if closing_minutes < opening_minutes:
            closing_minutes += 1440 # Agregar 24 horas
        return (opening_minutes, closing_minutes)
    # Si no se puede parsear, asumir 24 horas
    logger.warning(f"Could not parse opening hours: {day_hours}")
    return (0, 1440)
def is_poi_available(hours_dict: dict, day: str, start_time_minutes: int, visit_duration: int = 60)-> bool:
    """
    Verifica si un POI está disponible para visitar.
    Args:
    hours_dict: Dict de opening_hours
    day: Día de la semana
    start_time_minutes: Hora de inicio del tour (minutos desde
    medianoche)
    visit_duration: Duración estimada de visita en minutos
    Returns:
    True si el POI está abierto durante el tiempo de visita
    """
    opening, closing = parse_opening_hours(hours_dict, day)
    # Cerrado este día
    if opening is None:
        return False
    # Verificar que hay tiempo suficiente para visitar
    # El usuario debe llegar antes del cierre menos duración de visita
    latest_arrival = closing - visit_duration
    return start_time_minutes <= latest_arrival
def calculate_urgency_weight(hours_dict: dict, day: str, current_time_minutes: int, visit_duration: int = 60)-> float:
    """
    Calcula peso de urgencia para POIs que cierran pronto.
    Un POI que cierra en 30 minutos debería tener mayor prioridad
    que uno que cierra en 3 horas.
    Args:
    hours_dict: Dict de opening_hours
    day: Día de la semana
    current_time_minutes: Hora actual/inicio (minutos desde medianoche)
    visit_duration: Duración de visita
    Returns:
    Float de 1.0 (sin urgencia) a 2.0 (máxima urgencia)
    """
    opening, closing = parse_opening_hours(hours_dict, day)
    # Sin horario definido o 24 horas -> sin urgencia
    if opening is None or closing >= 1440: # 1440 = 24 horas
        return 1.0
    # Tiempo restante hasta el cierre
    time_until_close = closing - current_time_minutes
    # Si ya cerró o no hay tiempo para visitar
    if time_until_close <= visit_duration:
        return 0.0 # No visitable
    # Ventana de tiempo disponible después de visita mínima
    available_window = time_until_close - visit_duration
    # Calcular urgencia inversamente proporcional al tiempo disponible
    # < 30 min disponible -> urgencia máxima (2.0)
    # > 180 min disponible -> sin urgencia (1.0)
    if available_window <= 30:
        return 2.0
    elif available_window >= 180:
        return 1.0
    else:
        # Interpolación lineal entre 30 y 180 minutos
        urgency = 2.0- ((available_window - 30) / 150)
        return max(1.0, min(2.0, urgency))