"""
Verify travel time between Larcomar and Buenavista Cafe
"""
import requests
import os
from dotenv import load_dotenv
from geopy.distance import geodesic

load_dotenv()
API_KEY = os.getenv('OPENROUTESERVICE_API_KEY')

# Larcomar y Buenavista Cafe coordinates
larcomar = (-12.1319578, -77.0304916)
buenavista = (-12.1190075, -77.0452845)

# Calculate geodesic distance
dist_km = geodesic(larcomar, buenavista).kilometers
print(f'Distancia en linea recta: {dist_km:.2f} km')
print()

# Call OpenRouteService for driving-car
url = 'https://api.openrouteservice.org/v2/matrix/driving-car'
headers = {'Authorization': API_KEY, 'Content-Type': 'application/json'}

# ORS expects [lon, lat]
locations = [
    [larcomar[1], larcomar[0]],
    [buenavista[1], buenavista[0]]
]

body = {'locations': locations, 'metrics': ['duration', 'distance'], 'units': 'm'}
response = requests.post(url, json=body, headers=headers, timeout=30)
data = response.json()

print('OpenRouteService API Response:')
dist_road = data["distances"][0][1]/1000
time_seconds = data["durations"][0][1]
time_minutes = time_seconds / 60

print(f'  Distancia por carretera: {dist_road:.2f} km')
print(f'  Tiempo en SEGUNDOS: {time_seconds:.0f}')
print(f'  Tiempo en MINUTOS: {time_minutes:.1f}')
print(f'  Velocidad promedio: {(dist_road / (time_minutes/60)):.1f} km/h')
print()
print('Conclusion:')
if time_minutes < 5:
    print(f'  -> El API dice {time_minutes:.1f} minutos, lo cual parece bajo')
    print(f'  -> Para {dist_road:.2f} km, 3 min implica velocidad de {dist_road/(3/60):.0f} km/h')
else:
    print(f'  -> El API dice {time_minutes:.1f} minutos - parece razonable')
