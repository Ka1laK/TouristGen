# 🗺️ TouristGen Pro

**Planificador Inteligente de Rutas Turísticas para Lima y Callao**

Sistema de optimización de rutas turísticas que utiliza **Algoritmos Genéticos** para resolver el problema **TOPTW (Team Orienteering Problem with Time Windows)**, generando itinerarios personalizados basados en preferencias del usuario, condiciones climáticas en tiempo real, y restricciones de tiempo y presupuesto.

---

## 🎯 Características Principales

### 🧬 Optimización Inteligente
- **Algoritmo Genético** con operadores de cruce ordenado (OX), mutación múltiple, y selección por torneo
- **TOPTW Solver** que maximiza el puntaje de POIs visitados respecto a restricciones
- **Función de Fitness** que considera:
  - Popularidad y rating de POIs
  - Condiciones climáticas en tiempo real
  - Preferencias del usuario
  - Penalizaciones por violación de restricciones

### 🌦️ Integración con APIs Externas
- **Open-Meteo**: Pronóstico del clima sin necesidad de API key
- **OpenRouteService**: Cálculo de rutas y matrices de distancia (opcional)
- **Nominatim**: Geocodificación gratuita

### 📊 Aprendizaje Continuo
- Sistema de **feedback** que ajusta pesos de popularidad
- Actualización automática de preferencias basada en comportamiento del usuario
- Mejora continua de recomendaciones

### 🎨 Interfaz Moderna
- Mapa interactivo con **Leaflet**
- Timeline visual del itinerario
- Diseño responsive y moderno
- Visualización de rutas con polylines

---

## 🏗️ Arquitectura del Sistema

```
proyecto_SI/
├── backend/                    # Backend Python (FastAPI)
│   ├── app/
│   │   ├── models/            # Modelos SQLAlchemy (POI, Feedback, User)
│   │   ├── services/          # Lógica de negocio
│   │   │   ├── toptw_solver.py      # Solver TOPTW
│   │   │   ├── ga_optimizer.py      # Algoritmo Genético
│   │   │   ├── weather_service.py   # Servicio de clima
│   │   │   ├── routes_service.py    # Servicio de rutas
│   │   │   ├── poi_service.py       # Gestión de POIs
│   │   │   └── scraper_service.py   # Web scraping
│   │   ├── api/               # Endpoints FastAPI
│   │   │   ├── pois.py
│   │   │   ├── optimizer.py
│   │   │   ├── weather.py
│   │   │   └── routes.py
│   │   ├── database.py        # Configuración de BD
│   │   ├── config.py          # Configuración
│   │   └── main.py            # Aplicación FastAPI
│   ├── init_db.py             # Script de inicialización
│   └── requirements.txt
├── frontend/                   # Frontend React
│   ├── src/
│   │   ├── components/
│   │   │   ├── Map.jsx
│   │   │   ├── Timeline.jsx
│   │   │   └── PreferenceForm.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
└── database/                   # Base de datos SQLite
    └── touristgen.db
```

---

## 🚀 Instalación y Configuración

### Prerrequisitos
- **Python 3.11+**
- **Node.js 18+**
- **npm** o **yarn**

### 1. Configurar Backend

```bash
# Navegar al directorio backend
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Inicializar base de datos con POIs de ejemplo
python init_db.py

# Ejecutar servidor
python -m app.main
```

El backend estará disponible en: `http://localhost:8000`
Documentación API: `http://localhost:8000/docs`

### 2. Configurar Frontend

```bash
# Navegar al directorio frontend
cd frontend

# Instalar dependencias
npm install

# Ejecutar servidor de desarrollo
npm run dev
```

El frontend estará disponible en: `http://localhost:5173`

---

## 🔧 Configuración Opcional

### API Keys (Opcional)

Crear archivo `.env` en `backend/`:

```env
# OpenRouteService (opcional - mejora cálculo de rutas)
OPENROUTESERVICE_API_KEY=tu_api_key_aqui

# Open-Meteo no requiere API key
# Nominatim no requiere API key
```

**Nota**: El sistema funciona completamente sin API keys, usando cálculos geodésicos como fallback.

---

## 📖 Uso del Sistema

### 1. Configurar Preferencias
- **Duración máxima**: Tiempo disponible para el tour (60-720 minutos)
- **Presupuesto**: Límite de gasto en soles (S/)
- **Hora de inicio**: Hora de comienzo del tour
- **Ritmo**: Lento, medio o rápido
- **Categorías obligatorias**: Tipos de lugares que DEBEN incluirse
- **Categorías a evitar**: Tipos de lugares a excluir
- **Distritos preferidos**: Zonas de Lima/Callao a priorizar

### 2. Generar Ruta
Click en "🚀 Generar Ruta Optimizada"

El sistema:
1. Filtra POIs según preferencias
2. Obtiene pronóstico del clima
3. Calcula matriz de distancias
4. Ejecuta algoritmo genético (100 individuos, 200 generaciones)
5. Retorna ruta optimizada

### 3. Visualizar Resultados
- **Mapa**: Muestra POIs numerados y ruta trazada
- **Timeline**: Itinerario detallado con horarios, costos, clima
- **Estadísticas**: Total de lugares, duración, costo, puntaje

---

## 🧮 Modelo Matemático

### TOPTW (Team Orienteering Problem with Time Windows)

**Objetivo**: Maximizar puntaje total visitado

**Función de Fitness**:
```
Fitness = Σ(Popularidad × PesoClima × PesoUsuario × PesoAprendido) 
          - (α × TiempoViaje) 
          - (β × Costo) 
          - Penalizaciones
```

**Restricciones**:
- Tiempo total ≤ Duración máxima
- Costo total ≤ Presupuesto máximo
- Llegada ≥ Hora de apertura
- Salida ≤ Hora de cierre
- Categorías obligatorias incluidas

**Penalizaciones**:
- Llegar antes de apertura: +50
- Llegar después de cierre: +200
- Exceder tiempo: +2 por minuto
- Exceder presupuesto: +10 por sol
- Omitir categoría obligatoria: +100

### Algoritmo Genético

**Parámetros**:
- Población: 100 individuos
- Generaciones: 200
- Tasa de mutación: 15%
- Tasa de cruce: 80%
- Elitismo: 10%

**Operadores**:
- **Selección**: Torneo (tamaño 5)
- **Cruce**: Ordered Crossover (OX)
- **Mutación**: Swap, Insert, Shuffle, Add, Remove

---

## 📊 Base de Datos

### Tabla: `pois`
Puntos de interés con:
- Coordenadas geográficas
- Horarios de apertura/cierre
- Popularidad y rating
- Categoría y distrito
- Precio y duración de visita
- Peso de aprendizaje

### Tabla: `feedback`
Retroalimentación del usuario:
- Rating del POI
- Si fue visitado o no
- Condiciones climáticas
- Comentarios

### Tabla: `user_profiles`
Perfiles de usuario (opcional):
- Preferencias guardadas
- Historial de visitas
- POIs favoritos

---

## 🌐 API Endpoints

### POIs
- `GET /api/pois/` - Listar todos los POIs
- `GET /api/pois/{id}` - Obtener POI específico
- `POST /api/pois/` - Crear nuevo POI
- `GET /api/pois/districts/list` - Listar distritos
- `GET /api/pois/categories/list` - Listar categorías
- `GET /api/pois/stats/overview` - Estadísticas generales

### Optimización
- `POST /api/optimize/generate-route` - Generar ruta optimizada
- `POST /api/optimize/feedback` - Enviar feedback

### Clima
- `GET /api/weather/current` - Clima actual
- `GET /api/weather/forecast` - Pronóstico horario
- `GET /api/weather/penalty` - Calcular penalización climática

### Rutas
- `POST /api/routes/calculate` - Calcular ruta entre dos puntos
- `POST /api/routes/matrix` - Calcular matriz de distancias
- `GET /api/routes/isochrone` - Obtener isócrona

---

## 🧪 Testing

### Backend
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend
```bash
cd frontend
npm run test
```

---

## 📈 Mejoras Futuras

- [ ] Implementar ACO (Ant Colony Optimization) como alternativa
- [ ] Soporte multi-día
- [ ] Integración con transporte público
- [ ] App móvil (React Native)
- [ ] Sistema de reservas
- [ ] Recomendaciones personalizadas con ML
- [ ] Soporte multi-idioma
- [ ] Modo offline

---

## 🤝 Contribuciones

Este es un proyecto educacional. Las contribuciones son bienvenidas:

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto es de código abierto para fines educacionales.

---

## 👥 Autores

Desarrollado como proyecto de Sistema Inteligente para planificación turística en Lima y Callao.

---

## 🙏 Agradecimientos

- **Open-Meteo** por API de clima gratuita
- **OpenStreetMap** y **Nominatim** por geocodificación
- **OpenRouteService** por cálculo de rutas
- **FastAPI** y **React** por excelentes frameworks
- **Leaflet** por mapas interactivos

---

## 📞 Soporte

Para preguntas o problemas, abrir un issue en el repositorio.

**¡Disfruta explorando Lima y Callao con TouristGen Pro! 🎉**
