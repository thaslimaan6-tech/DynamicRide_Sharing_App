import heapq
import math
from typing import List, Tuple, Dict, Optional

# Enhanced city graph with major cities in Andhra Pradesh
CITY_GRAPH = {
    # Major Cities
    'Vijayawada': {
        'coords': (16.5062, 80.6480),
        'neighbors': {
            'Guntur': 32,
            'Eluru': 60,
            'Machilipatnam': 65,
            'Amaravati': 30,
            'Rajahmundry': 120,
            'Mangalgiri': 15
        }
    },
    'Visakhapatnam': {
        'coords': (17.6869, 83.2185),
        'neighbors': {
            'Rajahmundry': 190,
            'Vizianagaram': 60,
            'Anakapalli': 35
        }
    },
    'Guntur': {
        'coords': (16.3067, 80.4365),
        'neighbors': {
            'Vijayawada': 32,
            'Amaravati': 25,
            'Tenali': 28,
            'Narsaraopet': 48,
            'Mangalgiri': 20 
        }
    },
    'Mangalgiri': {
        'coords': (16.4300, 80.5500),  # near town center
        'neighbors': {
            'Vijayawada': 15,
            'Guntur': 20,
            'Amaravati': 18
        }
    },
    'Rajahmundry': {
        'coords': (17.0005, 81.8040),
        'neighbors': {
            'Vijayawada': 120,
            'Visakhapatnam': 190,
            'Kakinada': 60,
            'Amalapuram': 55
        }
    },
    'Amaravati': {
        'coords': (16.5734, 80.3580),
        'neighbors': {
            'Vijayawada': 30,
            'Guntur': 25,
            'Tenali': 20,
            'Mangalgiri': 18 
        }
    },
    'Tirupati': {
        'coords': (13.6288, 79.4192),
        'neighbors': {
            'Nellore': 140,
            'Chittoor': 70,
            'Srikalahasti': 35
        }
    },
    'Nellore': {
        'coords': (14.4426, 79.9865),
        'neighbors': {
            'Tirupati': 140,
            'Ongole': 135,
            'Kavali': 40
        }
    },
    'Kakinada': {
        'coords': (16.9891, 82.2475),
        'neighbors': {
            'Rajahmundry': 60,
            'Amalapuram': 50,
            'Visakhapatnam': 150
        }
    },
    'Eluru': {
        'coords': (16.7107, 81.0953),
        'neighbors': {
            'Vijayawada': 60,
            'Tanuku': 45,
            'Tadepalligudem': 40
        }
    },
    'Ongole': {
        'coords': (15.5057, 80.0499),
        'neighbors': {
            'Nellore': 135,
            'Guntur': 130,
            'Chirala': 35
        }
    },
    'Anantapur': {
        'coords': (14.6819, 77.6006),
        'neighbors': {
            'Kurnool': 110,
            'Kadiri': 55,
            'Hindupur': 90
        }
    },
    'Kurnool': {
        'coords': (15.8281, 78.0373),
        'neighbors': {
            'Anantapur': 110,
            'Nandyal': 75,
            'Adoni': 60
        }
    },
    'Vizianagaram': {
        'coords': (18.1067, 83.4152),
        'neighbors': {
            'Visakhapatnam': 60,
            'Srikakulam': 65,
            'Anakapalli': 45
        }
    },
    'Machilipatnam': {
        'coords': (16.1875, 81.1389),
        'neighbors': {
            'Vijayawada': 65,
            'Avanigadda': 35
        }
    },
    'Tenali': {
        'coords': (16.2428, 80.6425),
        'neighbors': {
            'Guntur': 28,
            'Amaravati': 20,
            'Vijayawada': 35
        }
    },
    'Chittoor': {
        'coords': (13.2172, 79.1003),
        'neighbors': {
            'Tirupati': 70,
            'Madanapalle': 60
        }
    },
    'Kadapa': {
        'coords': (14.4673, 78.8242),
        'neighbors': {
            'Kurnool': 150,
            'Tirupati': 180,
            'Proddatur': 35
        }
    },
    'Srikakulam': {
        'coords': (18.2949, 83.8938),
        'neighbors': {
            'Vizianagaram': 65,
            'Visakhapatnam': 105
        }
    },
    'Narsaraopet': {
        'coords': (16.2346, 80.0470),
        'neighbors': {
            'Guntur': 48,
            'Ongole': 85
        }
    },
    'Tadepalligudem': {
        'coords': (16.8150, 81.5267),
        'neighbors': {
            'Eluru': 40,
            'Rajahmundry': 75
        }
    },
    'Amalapuram': {
        'coords': (16.5778, 82.0083),
        'neighbors': {
            'Rajahmundry': 55,
            'Kakinada': 50
        }
    },
    'Kavali': {
        'coords': (14.9142, 79.9944),
        'neighbors': {
            'Nellore': 40,
            'Ongole': 95
        }
    },
    'Chirala': {
        'coords': (15.8238, 80.3520),
        'neighbors': {
            'Ongole': 35,
            'Bapatla': 40
        }
    },
    'Bapatla': {
        'coords': (15.9044, 80.4679),
        'neighbors': {
            'Chirala': 40,
            'Tenali': 55
        }
    },
    'Hindupur': {
        'coords': (13.8283, 77.4911),
        'neighbors': {
            'Anantapur': 90,
            'Madanapalle': 95
        }
    },
    'Adoni': {
        'coords': (15.6277, 77.2747),
        'neighbors': {
            'Kurnool': 60,
            'Anantapur': 140
        }
    },
    'Nandyal': {
        'coords': (15.4777, 78.4839),
        'neighbors': {
            'Kurnool': 75,
            'Kadapa': 120
        }
    },
    'Proddatur': {
        'coords': (14.7502, 78.5482),
        'neighbors': {
            'Kadapa': 35,
            'Nandyal': 85
        }
    },
    'Madanapalle': {
        'coords': (13.5503, 78.5029),
        'neighbors': {
            'Chittoor': 60,
            'Hindupur': 95
        }
    },
    'Srikalahasti': {
        'coords': (13.7500, 79.7000),
        'neighbors': {
            'Tirupati': 35,
            'Nellore': 120
        }
    },
    'Anakapalli': {
        'coords': (17.6911, 82.9986),
        'neighbors': {
            'Visakhapatnam': 35,
            'Vizianagaram': 45
        }
    },
    'Tanuku': {
        'coords': (16.7547, 81.6817),
        'neighbors': {
            'Eluru': 45,
            'Tadepalligudem': 55
        }
    },
    'Avanigadda': {
        'coords': (16.0218, 80.9182),
        'neighbors': {
            'Machilipatnam': 35,
            'Vijayawada': 90
        }
    },
    'Kadiri': {
        'coords': (14.1122, 78.1599),
        'neighbors': {
            'Anantapur': 55,
            'Kadapa': 110
        }
    }
}

# Cache for frequently used routes
_route_cache: Dict[Tuple[str, str], Tuple[List[str], List[Tuple[float, float]]]] = {}

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r

def heuristic(city1: str, city2: str) -> float:
    """
    Improved heuristic using actual great-circle distance
    """
    coords1 = CITY_GRAPH[city1]['coords']
    coords2 = CITY_GRAPH[city2]['coords']
    return haversine_distance(coords1[0], coords1[1], coords2[0], coords2[1])

def find_path(start: str, goal: str) -> Tuple[Optional[List[str]], Optional[List[Tuple[float, float]]]]:
    """
    Optimized A* pathfinding algorithm with caching
    Returns: (path, coordinates) or (None, None) if no path found
    """
    # Check cache first
    cache_key = (start, goal)
    if cache_key in _route_cache:
        return _route_cache[cache_key]
    
    # Validate inputs
    if start not in CITY_GRAPH or goal not in CITY_GRAPH:
        return None, None
    
    if start == goal:
        coords = [CITY_GRAPH[start]['coords']]
        result = ([start], coords)
        _route_cache[cache_key] = result
        return result
    
    # A* algorithm with priority queue
    frontier = []
    heapq.heappush(frontier, (0, start))
    
    came_from: Dict[str, Optional[str]] = {start: None}
    cost_so_far: Dict[str, float] = {start: 0}
    
    while frontier:
        _, current = heapq.heappop(frontier)
        
        if current == goal:
            break
        
        for neighbor, distance in CITY_GRAPH[current]['neighbors'].items():
            new_cost = cost_so_far[current] + distance
            
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + heuristic(neighbor, goal)
                heapq.heappush(frontier, (priority, neighbor))
                came_from[neighbor] = current
    
    # Reconstruct path
    if goal not in came_from:
        return None, None
    
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = came_from[current]
    path.reverse()
    
    # Get coordinates
    coordinates = [CITY_GRAPH[city]['coords'] for city in path]
    
    # Cache the result
    result = (path, coordinates)
    _route_cache[cache_key] = result
    
    return result

def get_all_cities() -> List[str]:
    """Return sorted list of all available cities"""
    return sorted(CITY_GRAPH.keys())

def get_city_info(city: str) -> Optional[Dict]:
    """Get information about a specific city"""
    return CITY_GRAPH.get(city)

def calculate_route_distance(path: List[str]) -> float:
    """Calculate total distance of a route"""
    if not path or len(path) < 2:
        return 0.0
    
    total_distance = 0.0
    for i in range(len(path) - 1):
        current = path[i]
        next_city = path[i + 1]
        
        if next_city in CITY_GRAPH[current]['neighbors']:
            total_distance += CITY_GRAPH[current]['neighbors'][next_city]
    
    return total_distance

def get_nearest_city(lat: float, lon: float) -> str:
    """Find the nearest city to given coordinates"""
    min_distance = float('inf')
    nearest = list(CITY_GRAPH.keys())[0]
    
    for city, data in CITY_GRAPH.items():
        city_lat, city_lon = data['coords']
        distance = haversine_distance(lat, lon, city_lat, city_lon)
        
        if distance < min_distance:
            min_distance = distance
            nearest = city
    
    return nearest

def clear_cache():
    """Clear the route cache"""
    global _route_cache
    _route_cache.clear()
