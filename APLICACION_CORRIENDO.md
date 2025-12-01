# ✅ TouristGen Pro - Aplicación en Ejecución

## 🎉 ¡La aplicación está corriendo!

### 🌐 URLs de Acceso

**Frontend (Interfaz de Usuario)**
```
http://localhost:5173
```
👉 Abre esta URL en tu navegador para usar la aplicación

**Backend (API)**
```
http://localhost:8000
```

**Documentación de la API**
```
http://localhost:8000/docs
```
👉 Interfaz interactiva para probar los endpoints

---

## 🎮 Cómo Usar la Aplicación

### 1. Abre tu navegador
Ve a: **http://localhost:5173**

### 2. Configura tus preferencias

En el panel izquierdo verás un formulario con:

- **⏱️ Duración Máxima**: Cuánto tiempo tienes disponible (en minutos)
  - Ejemplo: 480 minutos = 8 horas
  
- **💰 Presupuesto Máximo**: Cuánto quieres gastar (en soles)
  - Ejemplo: S/ 200
  
- **🕐 Hora de Inicio**: A qué hora empiezas
  - Ejemplo: 09:00
  
- **🚶 Ritmo de Caminata**: Qué tan rápido caminas
  - Lento / Medio / Rápido
  
- **✅ Categorías Obligatorias**: Tipos de lugares que DEBES visitar
  - Museum, Park, Beach, Shopping, etc.
  
- **❌ Categorías a Evitar**: Tipos de lugares que NO quieres
  
- **📍 Distritos Preferidos**: Zonas que prefieres visitar
  - Miraflores, Barranco, Lima, San Isidro, Callao, etc.

### 3. Genera tu ruta

Haz clic en el botón: **🚀 Generar Ruta Optimizada**

El sistema:
- Analizará los POIs disponibles
- Consultará el clima en tiempo real
- Calculará las distancias
- Ejecutará el algoritmo genético
- Te mostrará la ruta óptima

### 4. Visualiza tu itinerario

Verás dos secciones:

**🗺️ Mapa Interactivo**
- POIs numerados en orden de visita
- Ruta trazada entre los puntos
- Haz clic en los marcadores para ver detalles

**📅 Timeline del Itinerario**
- Hora de llegada y salida de cada lugar
- Tiempo de visita
- Tiempo de caminata
- Costo de entrada
- Clima esperado

---

## 📊 Ejemplo de Prueba

Prueba con estos valores para un día completo en Lima:

```
Duración: 480 minutos (8 horas)
Presupuesto: S/ 150
Hora de Inicio: 09:00
Ritmo: Medio
Categorías Obligatorias: Museum, Park
Distritos Preferidos: Miraflores, Barranco
```

Deberías obtener una ruta de 6-8 lugares optimizada.

---

## 🔍 Explorar la API

Visita: **http://localhost:8000/docs**

Aquí puedes:
- Ver todos los endpoints disponibles
- Probar las APIs directamente
- Ver los modelos de datos
- Generar rutas manualmente

### Endpoints Principales

**Listar POIs**
```
GET http://localhost:8000/api/pois/
```

**Generar Ruta**
```
POST http://localhost:8000/api/optimize/generate-route
```

**Clima Actual**
```
GET http://localhost:8000/api/weather/current?latitude=-12.0464&longitude=-77.0428
```

---

## 🛑 Detener los Servidores

Cuando termines de usar la aplicación:

1. En la terminal del **Backend**: Presiona `Ctrl + C`
2. En la terminal del **Frontend**: Presiona `Ctrl + C`

---

## 🔄 Reiniciar la Aplicación

Para volver a ejecutar la aplicación más tarde:

**Backend:**
```bash
cd backend
.\venv\Scripts\activate
python -m app.main
```

**Frontend:**
```bash
cd frontend
npm run dev
```

O simplemente ejecuta los scripts:
- `start_backend.bat`
- `start_frontend.bat`

---

## 📊 Estado Actual

✅ **Backend**: Corriendo en http://localhost:8000
✅ **Frontend**: Corriendo en http://localhost:5173
✅ **Base de Datos**: Inicializada con 30+ POIs
✅ **Servicios**: Weather, Routes, POI, Optimizer activos

---

## 🎯 Próximos Pasos

1. **Abre tu navegador** en http://localhost:5173
2. **Prueba generar una ruta** con diferentes preferencias
3. **Explora el mapa** y el timeline
4. **Revisa la API** en http://localhost:8000/docs
5. **Personaliza** agregando más POIs o modificando el código

---

## 📚 Documentación Completa

- **README.md** - Documentación completa del sistema
- **QUICKSTART.md** - Guía rápida de inicio
- **walkthrough.md** - Detalles técnicos de implementación

---

## 🎉 ¡Disfruta Explorando Lima y Callao!

El sistema está listo para generar rutas turísticas optimizadas usando algoritmos genéticos y TOPTW.

**¡Feliz exploración! 🗺️✨**
