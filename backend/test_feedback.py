import requests, json, time

API_URL = 'http://localhost:8000/api/feedback'

def submit_feedback(i):
    payload = {
        "route_id": f"test{i}",
        "rating": (i % 5) + 1,
        "total_duration": 60 + i,
        "total_cost": 20.0 + i*0.5,
        "num_pois": 5 + (i % 3),
        "fitness_score": 100.0 + i,
        "avg_poi_rating": 4.0 + (i % 2)*0.5,
        "avg_poi_popularity": 70 + (i % 10),
        "total_distance_km": 10.0 + (i % 4)
    }
    r = requests.post(f"{API_URL}/submit", json=payload)
    print('POST', r.status_code, r.json())

def get_weights():
    r = requests.get('http://localhost:8000/api/feedback/weights')
    print('GET weights', r.status_code, r.json())

if __name__ == '__main__':
    # submit a few feedbacks
    for i in range(1, 5):
        submit_feedback(i)
        time.sleep(0.2)
    get_weights()
