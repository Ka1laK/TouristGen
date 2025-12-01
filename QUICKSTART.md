# 🚀 Quick Start Guide - TouristGen Pro

## ⚡ Fastest Way to Get Started

### Option 1: Using Setup Scripts (Recommended)

#### Step 1: Setup Backend
```bash
# Double-click or run:
setup_backend.bat
```

This will:
- Create Python virtual environment
- Install all dependencies
- Initialize database with sample POIs

#### Step 2: Setup Frontend
```bash
# Double-click or run:
setup_frontend.bat
```

This will:
- Install Node.js dependencies

#### Step 3: Start the System

**Terminal 1 - Backend:**
```bash
# Double-click or run:
start_backend.bat
```

Backend runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

**Terminal 2 - Frontend:**
```bash
# Double-click or run:
start_frontend.bat
```

Frontend runs at: `http://localhost:5173`

### Option 2: Manual Setup

#### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
python -m app.main
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 🎮 Using the Application

1. **Open browser** to `http://localhost:5173`

2. **Configure your preferences:**
   - **Duration**: How many hours you have (e.g., 480 min = 8 hours)
   - **Budget**: Maximum spending (e.g., S/ 200)
   - **Start Time**: When you want to begin (e.g., 09:00)
   - **Pace**: Walking speed (slow/medium/fast)
   - **Categories**: Select must-visit types (Museums, Parks, etc.)
   - **Districts**: Choose preferred areas (Miraflores, Barranco, etc.)

3. **Click "Generar Ruta Optimizada"**

4. **View your optimized route:**
   - **Map**: See numbered POIs and route path
   - **Timeline**: Detailed schedule with times and costs
   - **Stats**: Total duration, cost, and optimization score

---

## 📊 Sample Test Case

Try these settings for a great day in Lima:

```
Duration: 480 minutes (8 hours)
Budget: S/ 150
Start Time: 09:00
Pace: Medium
Mandatory Categories: Museum, Park
Preferred Districts: Miraflores, Barranco, Lima
```

Expected result: 6-8 POIs optimized route visiting cultural sites and parks.

---

## 🔍 Exploring the API

Visit `http://localhost:8000/docs` for interactive API documentation.

Try these endpoints:

### Get all POIs
```bash
GET http://localhost:8000/api/pois/
```

### Get districts
```bash
GET http://localhost:8000/api/pois/districts/list
```

### Get current weather
```bash
GET http://localhost:8000/api/weather/current?latitude=-12.0464&longitude=-77.0428
```

### Generate route (POST request)
```bash
POST http://localhost:8000/api/optimize/generate-route
Content-Type: application/json

{
  "max_duration": 480,
  "max_budget": 200,
  "start_time": "09:00",
  "user_pace": "medium",
  "mandatory_categories": ["Museum"],
  "avoid_categories": [],
  "preferred_districts": ["Miraflores"]
}
```

---

## 🐛 Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.11+)
- Reinstall dependencies: `pip install -r requirements.txt`
- Check port 8000 is free

### Frontend won't start
- Check Node version: `node --version` (need 18+)
- Delete `node_modules` and run `npm install` again
- Check port 5173 is free

### No POIs showing
- Run `python init_db.py` to populate database
- Check backend is running
- Check browser console for errors

### Map not displaying
- Check internet connection (Leaflet needs to load tiles)
- Check browser console for errors
- Try refreshing the page

---

## 📚 Next Steps

1. **Explore the code:**
   - Backend: `backend/app/`
   - Frontend: `frontend/src/`

2. **Add more POIs:**
   - Edit `backend/init_db.py`
   - Add your favorite places

3. **Customize the algorithm:**
   - Adjust GA parameters in `backend/app/config.py`
   - Modify fitness function in `backend/app/services/toptw_solver.py`

4. **Enhance the UI:**
   - Modify styles in `frontend/src/index.css`
   - Add new components in `frontend/src/components/`

---

## 📖 Documentation

- **[README.md](file:///c:/Users/risse/Downloads/proyecto_SI/README.md)** - Complete documentation
- **[Walkthrough](file:///C:/Users/risse/.gemini/antigravity/brain/73f5519f-989d-4836-946b-1da912a7f0a1/walkthrough.md)** - Implementation details
- **[API Docs](http://localhost:8000/docs)** - Interactive API documentation (when backend is running)

---

## 🎉 Enjoy!

You now have a fully functional intelligent tourist route planner!

**Happy exploring Lima and Callao! 🗺️✨**
