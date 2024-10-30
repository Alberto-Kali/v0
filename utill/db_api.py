import sqlite3
import time
from tqdm import tqdm
import openrouteservice
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

# Константы
DATABASE_PATH = '../main.db'
ORS_API_KEY = '5b3ce3597851110001cf6248b406c2a4df264cdfac696101870c473c'
SLEEP_TIME = 1.5  # Увеличенное время задержки для избежания ошибок API

class LocationDatabase:
    def __init__(self):
        self.client = openrouteservice.Client(key=ORS_API_KEY)
        self.geolocator = Nominatim(user_agent="my_agent")
        
    def connect_db(self):
        return sqlite3.connect(DATABASE_PATH)

    def calculate_route(self, point1, point2, profile="foot-walking"):
        try:
            cords = [point1, point2]
            routes = self.client.directions(cords, profile=profile)
            distance = routes['routes'][0]['summary']['distance'] / 1000
            duration = routes['routes'][0]['summary']['duration'] / 60
            return (distance, duration)
        except Exception as e:
            print(f"Route calculation error: {e}")
            return None

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
                
            # Удаление мест без координат
            for place_name in places_to_delete:
                cursor.execute("DELETE FROM places WHERE name = ?", (place_name,))
                conn.commit()
                print(f"Deleted place: {place_name}")
            
            print(f"\nTotal places deleted: {len(places_to_delete)}")
            
        finally:
            conn.close()

    def create_routes_matrix(self):
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            # Создание таблицы
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS routes_matrix (
                    from_point TEXT,
                    to_point TEXT,
                    distance REAL,
                    duration REAL,
                    PRIMARY KEY (from_point, to_point)
                )
            """)
            
            cursor.execute("SELECT name, longitude, latitude FROM places")
            points = cursor.fetchall()
            total_routes = len(points) * (len(points) - 1)
            
            print("Creating routes matrix...")
            with tqdm(total=total_routes) as pbar:
                for point1 in points:
                    for point2 in points:
                        if point1 != point2:
                            try:
                                # Проверка существующего маршрута
                                cursor.execute("""
                                    SELECT 1 FROM routes_matrix 
                                    WHERE from_point = ? AND to_point = ?
                                """, (point1[0], point2[0]))
                                
                                if not cursor.fetchone():
                                    route = self.calculate_route(
                                        (point1[1], point1[2]), 
                                        (point2[1], point2[2])
                                    )
                                    
                                    if route:
                                        cursor.execute("""
                                            INSERT INTO routes_matrix 
                                            (from_point, to_point, distance, duration)
                                            VALUES (?, ?, ?, ?)
                                        """, (point1[0], point2[0], route[0], route[1]))
                                        conn.commit()
                                        time.sleep(SLEEP_TIME)
                                
                                pbar.update(1)
                                
                            except sqlite3.Error as e:
                                print(f"Database error: {e}")
                                continue
                                
        finally:
            conn.close()

def main():
    db = LocationDatabase()
    # db.update_coordinates()  # Раскомментируйте если нужно обновить координаты
    db.create_routes_matrix()

if __name__ == "__main__":
    main()