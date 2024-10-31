import sqlite3
import time
import requests
from tqdm import tqdm
import openrouteservice
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

# Константы
DATABASE_PATH = 'main.db'
ORS_API_KEY = '5b3ce3597851110001cf6248b406c2a4df264cdfac696101870c473c'
SLEEP_TIME = 1.5

TRANSPORT_MODES = {
    'foot-walking': 'пешком',
    'cycling-regular': 'велосипед',
    'driving-car': 'автомобиль',
    'driving-hgv': 'автобус'
}

class LocationDatabase:
    def __init__(self):
        self.client = openrouteservice.Client(key=ORS_API_KEY)
        self.geolocator = Nominatim(user_agent="my_agent")
        
    def connect_db(self):
        return sqlite3.connect(DATABASE_PATH)

    def update_coordinates(self):
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT name FROM places")
            places = cursor.fetchall()
            places_to_delete = []
            
            print("Updating coordinates...")
            for place in tqdm(places):
                place_name = place[0]
                try:
                    search_query = f"{place_name}, Калининградская область, Россия"
                    location = self.geolocator.geocode(search_query, timeout=10)
                    
                    if location:
                        cursor.execute("""
                            UPDATE places 
                            SET longitude = ?, latitude = ?
                            WHERE name = ?
                        """, (location.longitude, location.latitude, place_name))
                        conn.commit()
                    else:
                        places_to_delete.append(place_name)
                        print(f"\nCouldn't find coordinates for: {place_name}")
                    
                    time.sleep(SLEEP_TIME)
                    
                except (GeocoderTimedOut, GeocoderUnavailable) as e:
                    print(f"\nGeocoding error for {place_name}: {e}")
                    places_to_delete.append(place_name)
                    continue
                
            for place_name in places_to_delete:
                cursor.execute("DELETE FROM places WHERE name = ?", (place_name,))
                conn.commit()
                print(f"Deleted place: {place_name}")
        
            print(f"\nTotal places deleted: {len(places_to_delete)}")
            
        finally:
            conn.close()

    def create_routes_matrices(self):
        conn = self.connect_db()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT name, longitude, latitude FROM places")
            points = cursor.fetchall()

            locations = [[float(point[1]), float(point[2])] for point in points]
            names = [point[0] for point in points]

            for profile, mode_name in TRANSPORT_MODES.items():
                body = {
                    "locations": locations,
                    "metrics": ["distance", "duration"]
                }
                headers = {
                    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
                    'Authorization': ORS_API_KEY,
                    'Content-Type': 'application/json; charset=utf-8'
                }

                print(f"Requesting matrix data for {mode_name} from OpenRouteService...")
                response = requests.post(
                    f'https://api.openrouteservice.org/v2/matrix/{profile}', 
                    json=body, 
                    headers=headers
                )

                if response.status_code == 200:
                    matrix_data = response.json()

                    print(f"Updating routes matrix for {mode_name} in database...")
                    total_routes = len(points) * (len(points) - 1)
                    with tqdm(total=total_routes) as pbar:
                        for i, from_point in enumerate(names):
                            for j, to_point in enumerate(names):
                                if i != j:
                                    distance = matrix_data['distances'][i][j] / 1000
                                    duration = matrix_data['durations'][i][j] / 60

                                    cursor.execute(f"""
                                        INSERT OR REPLACE INTO routes_matrix_{profile.replace('-', '_')}
                                        (from_point, to_point, distance, duration)
                                        VALUES (?, ?, ?, ?)
                                    """, (from_point, to_point, distance, duration))

                                    pbar.update(1)

                    conn.commit()
                    print(f"Routes matrix for {mode_name} updated successfully.")
                else:
                    print(f"Error in API request for {mode_name}: {response.status_code} - {response.reason}")
                    print(response.text)

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            conn.close()

    def get_distance_matrices(self):
        conn = self.connect_db()
        cursor = conn.cursor()
        matrices = {}

        try:
            for profile in TRANSPORT_MODES.keys():
                table_name = f"routes_matrix_{profile.replace('-', '_')}"
                cursor.execute(f"""
                    SELECT from_point, to_point, distance, duration 
                    FROM {table_name}
                """)
                results = cursor.fetchall()
                
                matrix = {}
                for row in results:
                    from_point, to_point, distance, duration = row
                    if from_point not in matrix:
                        matrix[from_point] = {}
                    matrix[from_point][to_point] = {"distance": distance, "duration": duration}
                
                matrices[profile] = matrix

        except Exception as e:
            print(f"An error occurred while fetching matrices: {e}")

        finally:
            conn.close()

        return matrices
    
    def get_filtered_places(self, tags):
        conn = self.connect_db()
        cursor = conn.cursor()
        
        if not isinstance(tags, list):
            raise TypeError("tags должен быть списком")

        if not tags:
            return []

        query = """
        SELECT DISTINCT name, description, photo_link
        FROM places
        WHERE tags LIKE ?
        """
        
        results = set()
        for tag in tags:
            cursor.execute(query, (f"%{tag}%",))
            results.update(cursor.fetchall())
        
        conn.close()
        
        return [{"name": p[0], "description": p[1], "photo_url": p[2]} for p in results]

    def get_filtered_matrices(self, place_names):
        conn = self.connect_db()
        cursor = conn.cursor()
        matrices = {}

        try:
            # Создаем множество из place_names для быстрой проверки
            valid_places = set(place_names)

            for profile in TRANSPORT_MODES.keys():
                table_name = f"routes_matrix_{profile.replace('-', '_')}"
                placeholders = ','.join(['?' for _ in place_names])
                cursor.execute(f"""
                    SELECT from_point, to_point, distance, duration 
                    FROM {table_name}
                    WHERE from_point IN ({placeholders})
                    AND to_point IN ({placeholders})
                """, place_names + place_names)
                results = cursor.fetchall()
                
                matrix = {}
                for row in results:
                    from_point, to_point, distance, duration = row
                    # Проверяем, что оба места находятся в списке запрошенных мест
                    if from_point in valid_places and to_point in valid_places:
                        if from_point not in matrix:
                            matrix[from_point] = {}
                        matrix[from_point][to_point] = {"distance": distance, "duration": duration}
                
                matrices[profile] = matrix

        except Exception as e:
            print(f"An error occurred while fetching matrices: {e}")

        finally:
            conn.close()

        return matrices
    
    def find_places_from_names(self, days):
        conn = self.connect_db()
        cursor = conn.cursor()

        updated_days = []

        try:
            for day in days:
                updated_route = []
                for place in day['route']:
                    place_name = place['place_name']
                    cursor.execute("""
                        SELECT id, name, description, photo_link, longitude, latitude, tags
                        FROM places
                        WHERE name = ?
                    """, (place_name,))
                    result = cursor.fetchone()

                    if result:
                        updated_place = {
                            "place_id": result[0],  # используем id из базы данных
                            "place_name": result[1],
                            "description": result[2],
                            "photo_link": result[3],
                            "coordinates": {
                                "longitude": result[4],
                                "latitude": result[5]
                            },
                            "tags": result[6].split(',') if result[6] else []
                        }
                        updated_route.append(updated_place)
                    else:
                        print(f"Warning: Place '{place_name}' not found in the database.")
                        updated_route.append(place)  # сохраняем оригинальное место, если не найдено

                updated_day = day.copy()
                updated_day['route'] = updated_route
                updated_days.append(updated_day)

        except Exception as e:
            print(f"An error occurred while finding places: {e}")

        finally:
            conn.close()

        return updated_days


# Функция для получения матриц расстояний и времени
def get_all_matrices():
    db = LocationDatabase()
    db.create_routes_matrices()
    return db.get_distance_matrices()