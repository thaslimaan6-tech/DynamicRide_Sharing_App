from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
import math
import socket
from a_star import find_path, get_all_cities
import os

# Detect Render
IS_RENDER = os.environ.get('RENDER') == 'true'

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

def get_db():
    """Get database connection with Row factory"""
    db_path = '/tmp/rideshare.db' if IS_RENDER else 'rideshare.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with all required tables"""
    db_path = '/tmp/rideshare.db' if IS_RENDER else 'rideshare.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        current_lat REAL,
        current_lon REAL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS rides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        source TEXT NOT NULL,
        destination TEXT NOT NULL,
        path TEXT NOT NULL,
        coords TEXT NOT NULL,
        pickup_lat REAL NOT NULL,
        pickup_lon REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        rider_id INTEGER,
        rider_distance REAL,
        pickup_time INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (rider_id) REFERENCES users(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ride_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        notification_type TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (ride_id) REFERENCES rides(id)
    )''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized at:", db_path)

# Use Flask's before_first_request (runs once before first request)
_db_initialized = False

@app.before_request
def initialize_database():
    global _db_initialized
    if not _db_initialized:
        init_db()
        _db_initialized = True

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371
    dLat = (lat2 - lat1) * math.pi / 180
    dLon = (lon2 - lon1) * math.pi / 180
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(lat1 * math.pi / 180) * math.cos(lat2 * math.pi / 180) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def update_rider_location(rider_id):
    """Update rider's location to a random position"""
    base_lat, base_lon = 16.3067, 80.4365
    rider_lat = base_lat + random.uniform(-0.09, 0.09)
    rider_lon = base_lon + random.uniform(-0.09, 0.09)
    
    conn = get_db()
    conn.execute('UPDATE users SET current_lat = ?, current_lon = ? WHERE id = ?',
                (rider_lat, rider_lon, rider_id))
    conn.commit()
    conn.close()
    
    return rider_lat, rider_lon

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'rider':
            return redirect(url_for('rider_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        
        hashed_password = generate_password_hash(password)
        
        try:
            conn = get_db()
            conn.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                        (name, email, hashed_password, role))
            conn.commit()
            conn.close()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists!', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user'] = user['name']
            session['role'] = user['role']
            
            if user['role'] == 'rider':
                return redirect(url_for('rider_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/book_ride', methods=['GET', 'POST'])
def book_ride():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        source = request.form.get('source')
        destination = request.form.get('destination')
        
        if source == destination:
            flash('Source and destination cannot be the same!', 'error')
            return render_template('book_ride.html', cities=get_all_cities())
        
        path, coord_list = find_path(source, destination)
        
        if path:
            path_str = ','.join(path)
            coords_str = str(coord_list)
            pickup_lat, pickup_lon = coord_list[0]
            
            conn = get_db()
            conn.execute('''INSERT INTO rides 
                (user_id, source, destination, path, coords, pickup_lat, pickup_lon) 
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (session['user_id'], source, destination, path_str, coords_str, 
                 pickup_lat, pickup_lon))
            conn.commit()
            conn.close()
            
            flash('Ride booked successfully!', 'success')
            return render_template('route_map.html', path=path, coords=coord_list,
                                 source=source, destination=destination)
        else:
            flash('Route not found!', 'error')
    
    return render_template('book_ride.html', cities=get_all_cities())

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    
    # Get rides with rider information - NO DUPLICATES
    rides = conn.execute('''
        SELECT 
            rides.*,
            riders.name as rider_name,
            riders.email as rider_email,
            riders.current_lat as rider_lat,
            riders.current_lon as rider_lon
        FROM rides
        LEFT JOIN users as riders ON rides.rider_id = riders.id
        WHERE rides.user_id = ? 
        ORDER BY rides.created_at DESC
        LIMIT 20
    ''', (session['user_id'],)).fetchall()
    
    # Calculate distance for accepted rides
    rides_with_info = []
    seen_ride_ids = set()  # Track unique rides
    
    for ride in rides:
        # Skip duplicate rides
        if ride['id'] in seen_ride_ids:
            continue
        seen_ride_ids.add(ride['id'])
        
        ride_dict = dict(ride)
        
        # Calculate distance and ETA for accepted rides
        if ride['status'] == 'accepted' and ride['rider_lat'] and ride['rider_lon']:
            distance = calculate_distance(
                ride['rider_lat'], ride['rider_lon'],
                ride['pickup_lat'], ride['pickup_lon']
            )
            ride_dict['rider_distance'] = round(distance, 2)
            eta = int((distance / 40) * 60)  # 40 km/h average
            ride_dict['eta_minutes'] = eta
        
        rides_with_info.append(ride_dict)
    
    conn.close()
    
    return render_template('user_dashboard.html', user=session['user'], rides=rides_with_info)

@app.route('/rider_dashboard')
def rider_dashboard():
    if 'user_id' not in session or session.get('role') != 'rider':
        return redirect(url_for('login'))
    
    rider_lat, rider_lon = update_rider_location(session['user_id'])
    
    conn = get_db()
    rides = conn.execute('''
        SELECT rides.*, users.name as user_name, users.email as user_email
        FROM rides
        JOIN users ON rides.user_id = users.id
        ORDER BY rides.created_at DESC
    ''').fetchall()
    
    rides_with_distance = []
    for ride in rides:
        ride_dict = dict(ride)
        distance = calculate_distance(rider_lat, rider_lon, ride['pickup_lat'], ride['pickup_lon'])
        pickup_time = int((distance / 40) * 60)
        
        ride_dict['rider_distance'] = round(distance, 2)
        ride_dict['pickup_time'] = pickup_time
        rides_with_distance.append(ride_dict)
    
    conn.close()
    
    return render_template('rider_dashboard.html', 
                         rides=rides_with_distance, 
                         rider=session['user'],
                         rider_lat=rider_lat,
                         rider_lon=rider_lon)
@app.route('/accept_ride/<int:ride_id>')
def accept_ride(ride_id):
    if 'user_id' not in session or session.get('role') != 'rider':
        flash('Please login as a rider first', 'error')
        return redirect(url_for('login'))
    
    from a_star import CITY_GRAPH
    
    conn = get_db()
    
    try:
        ride = conn.execute('''
            SELECT rides.*, users.name as user_name 
            FROM rides 
            JOIN users ON rides.user_id = users.id 
            WHERE rides.id = ?
        ''', (ride_id,)).fetchone()
        
        if not ride:
            flash('Ride not found!', 'error')
            conn.close()
            return redirect(url_for('rider_dashboard'))
        
        if ride['status'] != 'pending':
            flash('This ride has already been accepted!', 'warning')
            conn.close()
            return redirect(url_for('rider_dashboard'))
        
        rider = conn.execute('SELECT name FROM users WHERE id = ?', 
                            (session['user_id'],)).fetchone()
        rider_name = rider['name'] if rider else 'A rider'
        
        pickup_city = ride['source']
        pickup_coords = CITY_GRAPH[pickup_city]['coords']
        pickup_lat, pickup_lon = pickup_coords
        
        rider_lat = pickup_lat + random.uniform(-0.02, 0.02)
        rider_lon = pickup_lon + random.uniform(-0.02, 0.02)
        
        conn.execute('UPDATE users SET current_lat = ?, current_lon = ? WHERE id = ?',
                    (rider_lat, rider_lon, session['user_id']))
        
        def get_nearest_city(lat, lon):
            min_dist = float('inf')
            nearest = pickup_city
            for city, data in CITY_GRAPH.items():
                city_lat, city_lon = data['coords']
                dist = math.sqrt((lat - city_lat)**2 + (lon - city_lon)**2)
                if dist < min_dist:
                    min_dist = dist
                    nearest = city
            return nearest
        
        rider_city = get_nearest_city(rider_lat, rider_lon)
        
        rider_to_pickup_distance = calculate_distance(rider_lat, rider_lon, pickup_lat, pickup_lon)
        estimated_time = int((rider_to_pickup_distance / 40) * 60)
        
        if rider_city == pickup_city:
            rider_to_pickup_path = [rider_city]
            rider_to_pickup_coords = [(rider_lat, rider_lon), pickup_coords]
        else:
            rider_to_pickup_path, rider_to_pickup_coords = find_path(rider_city, pickup_city)
            if rider_to_pickup_path and rider_to_pickup_coords:
                rider_to_pickup_coords = [(rider_lat, rider_lon)] + rider_to_pickup_coords
            else:
                rider_to_pickup_path = [rider_city, pickup_city]
                rider_to_pickup_coords = [(rider_lat, rider_lon), pickup_coords]
        
        user_path = ride['path'].split(',') if ride['path'] else []
        user_coords = eval(ride['coords']) if ride['coords'] else []
        
        # Update ride status
        conn.execute('UPDATE rides SET status = ?, rider_id = ? WHERE id = ?',
                    ('accepted', session['user_id'], ride_id))
        
        notification_message = f"🎉 {rider_name} accepted your ride! Arriving in {estimated_time} min"
        
        conn.execute('''INSERT INTO notifications 
                        (user_id, ride_id, message, notification_type) 
                        VALUES (?, ?, ?, ?)''',
                    (ride['user_id'], ride_id, notification_message, 'success'))
        
        conn.commit()
        
        flash(f'Ride accepted! Navigate to {pickup_city}. ETA: {estimated_time} min', 'success')
        return redirect(url_for('show_route', ride_id=ride_id))

    
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error accepting ride: {str(e)}', 'error')
        return redirect(url_for('rider_dashboard'))
    
    finally:
        conn.close()

@app.route('/route/<int:ride_id>')
def show_route(ride_id):
    """Show route with PURPLE OSRM routing for both users and riders"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    
    # Get ride details with rider information
    ride = conn.execute('''
        SELECT 
            rides.*,
            riders.name as rider_name,
            riders.current_lat as rider_lat,
            riders.current_lon as rider_lon
        FROM rides
        LEFT JOIN users as riders ON rides.rider_id = riders.id
        WHERE rides.id = ?
    ''', (ride_id,)).fetchone()
    
    conn.close()
    
    if not ride:
        flash('Ride not found!', 'error')
        return redirect(url_for('user_dashboard') if session.get('role') != 'rider' else url_for('rider_dashboard'))
    
    # Parse path and coordinates
    path = ride['path'].split(',') if ride['path'] else []
    coords = eval(ride['coords']) if ride['coords'] else []
    
    # Prepare rider data if ride is accepted
    rider_data = None
    if ride['status'] == 'accepted' and ride['rider_lat'] and ride['rider_lon']:
        from math import radians, sin, cos, sqrt, atan2
        
        # Calculate distance to pickup
        R = 6371  # Earth radius in km
        lat1, lon1 = radians(ride['rider_lat']), radians(ride['rider_lon'])
        lat2, lon2 = radians(ride['pickup_lat']), radians(ride['pickup_lon'])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        rider_data = {
            'name': ride['rider_name'],
            'lat': ride['rider_lat'],
            'lon': ride['rider_lon'],
            'distance_to_pickup': round(distance, 2)
        }
    
    return render_template('route_map.html',
                         ride_id=ride_id,
                         source=ride['source'],
                         destination=ride['destination'],
                         path=path,
                         coords=coords,
                         status=ride['status'],
                         rider=rider_data)

@app.route('/api/notifications')
def get_notifications():
    if 'user_id' not in session:
        return jsonify({'notifications': []})
    
    try:
        conn = get_db()
        notifications = conn.execute('''
            SELECT n.*, r.source, r.destination 
            FROM notifications n
            LEFT JOIN rides r ON n.ride_id = r.id
            WHERE n.user_id = ? AND n.is_read = 0
            ORDER BY n.created_at DESC
            LIMIT 10
        ''', (session['user_id'],)).fetchall()
        
        result = [dict(n) for n in notifications]
        conn.close()
        
        return jsonify({'notifications': result})
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'notifications': [], 'error': str(e)})

@app.route('/api/notifications/<int:notif_id>/mark_read', methods=['POST'])
def mark_notification_read(notif_id):
    if 'user_id' not in session:
        return jsonify({'success': False}), 403
    
    try:
        conn = get_db()
        conn.execute('UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?',
                    (notif_id, session['user_id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/ride_status')
def check_ride_status():
    """Check if any rides have been recently updated"""
    if 'user_id' not in session:
        return jsonify({'has_updates': False})
    
    try:
        conn = get_db()
        
        # Get timestamp of last check from session
        last_check = session.get('last_ride_check', '2000-01-01 00:00:00')
        
        # Check if any rides were updated after last check
        updated_rides = conn.execute('''
            SELECT COUNT(*) as count 
            FROM rides 
            WHERE user_id = ? 
            AND status = 'accepted' 
            AND created_at > ?
        ''', (session['user_id'], last_check)).fetchone()
        
        conn.close()
        
        # Update last check time
        from datetime import datetime
        session['last_ride_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        has_updates = updated_rides['count'] > 0
        
        return jsonify({'has_updates': has_updates})
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'has_updates': False})

@app.route('/api/my_rides')
def get_my_rides():
    """Get current user's rides with rider info"""
    if 'user_id' not in session:
        return jsonify({'rides': []})
    
    try:
        conn = get_db()
        
        rides = conn.execute('''
            SELECT 
                rides.*,
                riders.name as rider_name,
                riders.current_lat as rider_lat,
                riders.current_lon as rider_lon
            FROM rides
            LEFT JOIN users as riders ON rides.rider_id = riders.id
            WHERE rides.user_id = ? 
            ORDER BY rides.created_at DESC
        ''', (session['user_id'],)).fetchall()
        
        result = []
        for ride in rides:
            ride_dict = dict(ride)
            
            # Calculate rider distance if ride is accepted
            if ride['status'] == 'accepted' and ride['rider_lat'] and ride['rider_lon']:
                distance = calculate_distance(
                    ride['rider_lat'], ride['rider_lon'],
                    ride['pickup_lat'], ride['pickup_lon']
                )
                ride_dict['rider_distance'] = round(distance, 2)
            
            result.append(ride_dict)
        
        conn.close()
        
        return jsonify({'rides': result})
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'rides': [], 'error': str(e)})

@app.route('/accept_multiple_rides', methods=['POST'])
def accept_multiple_rides():
    """Accept multiple rides for pool/share mode"""
    if 'user_id' not in session or session.get('role') != 'rider':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        ride_ids = request.json.get('ride_ids', [])
        
        if not ride_ids:
            return jsonify({'error': 'No rides selected'}), 400
        
        conn = get_db()
        
        # Update all selected rides to accepted
        for ride_id in ride_ids:
            conn.execute('''
                UPDATE rides 
                SET status = 'accepted', rider_id = ? 
                WHERE id = ? AND status = 'pending'
            ''', (session['user_id'], ride_id))
            
            # Get ride details for notification
            ride = conn.execute('SELECT * FROM rides WHERE id = ?', (ride_id,)).fetchone()
            if ride:
                notification_message = f"🎉 Your ride has been accepted! Driver will pick up multiple passengers."
                conn.execute('''
                    INSERT INTO notifications 
                    (user_id, ride_id, message, notification_type) 
                    VALUES (?, ?, ?, ?)
                ''', (ride['user_id'], ride_id, notification_message, 'success'))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Accepted {len(ride_ids)} rides'
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/multi_route_view/<ride_ids>')
def multi_route_view(ride_ids):
    """Show optimized multi-user route with real road routing"""
    if 'user_id' not in session or session.get('role') != 'rider':
        return redirect(url_for('login'))
    
    try:
        ride_id_list = [int(rid) for rid in ride_ids.split(',')]
        
        conn = get_db()
        
        # Get all selected rides
        rides = []
        for ride_id in ride_id_list:
            ride = conn.execute('''
                SELECT rides.*, users.name as user_name 
                FROM rides 
                JOIN users ON rides.user_id = users.id 
                WHERE rides.id = ?
            ''', (ride_id,)).fetchone()
            
            if ride:
                rides.append(dict(ride))
        
        conn.close()
        
        if not rides:
            flash('No rides found!', 'error')
            return redirect(url_for('rider_dashboard'))
        
        # Optimize the pool route
        route_data = optimize_pool_route(rides)
        
        if not route_data:
            flash('Could not generate route!', 'error')
            return redirect(url_for('rider_dashboard'))
        
        # Set rider location at first pickup point
        start_coords = route_data['pickups'][0]['coords']
        rider_location = {
            'lat': start_coords[0],
            'lon': start_coords[1],
            'city': route_data['start_city']
        }
        
        print(f"🚗 Pool Route: {' → '.join(route_data['path'])}")
        print(f"📍 Pickups: {len(route_data['pickups'])}, Dropoffs: {len(route_data['dropoffs'])}")
        
        return render_template('multi_route_map.html',
                             route_data=route_data,
                             rides=rides,
                             rider_location=rider_location)
        
    except Exception as e:
        print(f"❌ Error in multi_route_view: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error loading route: {str(e)}', 'error')
        return redirect(url_for('rider_dashboard'))

def optimize_pool_route(rides):
    """
    Intelligent pool route optimizer - picks up passengers optimally and drops them efficiently
    Uses A* to find shortest combined path considering all pickups and dropoffs
    """
    from a_star import find_path, calculate_route_distance, haversine_distance
    
    if not rides:
        return None
    
    # Extract pickup and dropoff locations
    pickups = []
    dropoffs = []
    
    for ride in rides:
        pickup = {
            'ride_id': ride['id'],
            'user_name': ride.get('user_name', 'User'),
            'city': ride['source'],
            'coords': (ride['pickup_lat'], ride['pickup_lon']),
            'type': 'pickup',
            'passenger_id': ride['user_id']
        }
        pickups.append(pickup)
        
        # Get destination
        try:
            coords_list = eval(ride['coords'])
            dest_coords = coords_list[-1]
            dropoff = {
                'ride_id': ride['id'],
                'user_name': ride.get('user_name', 'User'),
                'city': ride['destination'],
                'coords': dest_coords,
                'type': 'dropoff',
                'passenger_id': ride['user_id']
            }
            dropoffs.append(dropoff)
        except:
            pass
    
    # Step 1: Find closest pickup location (rider starts here)
    start_pickup = pickups[0]
    
    # Step 2: Order pickups by proximity using greedy algorithm
    ordered_pickups = [start_pickup]
    remaining_pickups = [p for p in pickups if p != start_pickup]
    
    current_city = start_pickup['city']
    while remaining_pickups:
        # Find nearest unvisited pickup
        nearest = min(remaining_pickups, 
                     key=lambda p: calculate_route_distance([current_city, p['city']]))
        ordered_pickups.append(nearest)
        remaining_pickups.remove(nearest)
        current_city = nearest['city']
    
    # Step 3: Determine dropoff order
    # Check if dropoffs share path or diverge
    dropoff_cities = [d['city'] for d in dropoffs]
    
    # If multiple passengers going to same destination
    if len(set(dropoff_cities)) == 1:
        # All going to same place - drop all at once
        ordered_dropoffs = dropoffs
    else:
        # Different destinations - optimize order
        ordered_dropoffs = []
        current_city = ordered_pickups[-1]['city']  # Last pickup location
        remaining_dropoffs = dropoffs.copy()
        
        while remaining_dropoffs:
            # Find dropoff that's on the way or nearest
            nearest_dropoff = min(remaining_dropoffs,
                                 key=lambda d: calculate_route_distance([current_city, d['city']]))
            ordered_dropoffs.append(nearest_dropoff)
            remaining_dropoffs.remove(nearest_dropoff)
            current_city = nearest_dropoff['city']
    
    # Step 4: Build complete route using A*
    route_sequence = []
    all_waypoints = []
    
    # Add rider starting point
    route_sequence.append(ordered_pickups[0]['city'])
    all_waypoints.append(ordered_pickups[0])
    
    # Add all pickups in order
    for pickup in ordered_pickups[1:]:
        if pickup['city'] not in route_sequence:
            route_sequence.append(pickup['city'])
            all_waypoints.append(pickup)
    
    # Add all dropoffs in order
    for dropoff in ordered_dropoffs:
        if dropoff['city'] not in route_sequence:
            route_sequence.append(dropoff['city'])
            all_waypoints.append(dropoff)
    
    # Step 5: Calculate full path with A* between each segment
    full_path = []
    full_coords = []
    route_segments = []
    
    for i in range(len(route_sequence) - 1):
        from_city = route_sequence[i]
        to_city = route_sequence[i + 1]
        
        segment_path, segment_coords = find_path(from_city, to_city)
        
        if segment_path and segment_coords:
            # Record segment with action (pickup/dropoff)
            segment_info = {
                'from': from_city,
                'to': to_city,
                'path': segment_path,
                'distance': calculate_route_distance(segment_path)
            }
            
            # Check if this segment includes pickup or dropoff
            for waypoint in all_waypoints:
                if waypoint['city'] == to_city:
                    segment_info['action'] = f"{waypoint['type']} {waypoint['user_name']}"
                    break
            
            route_segments.append(segment_info)
            
            # Add to full path (avoid duplicates at junction points)
            if not full_path or segment_path[0] != full_path[-1]:
                full_path.extend(segment_path)
            else:
                full_path.extend(segment_path[1:])
            
            if not full_coords or segment_coords[0] != full_coords[-1]:
                full_coords.extend(segment_coords)
            else:
                full_coords.extend(segment_coords[1:])
    
    # Calculate total distance
    total_distance = sum(seg['distance'] for seg in route_segments)
    
    return {
        'path': full_path,
        'coords': full_coords,
        'pickups': ordered_pickups,
        'dropoffs': ordered_dropoffs,
        'start_city': ordered_pickups[0]['city'],
        'route_segments': route_segments,
        'total_distance': round(total_distance, 2),
        'waypoints': all_waypoints
    }

if __name__ == '__main__':
    init_db()
    local_ip = get_local_ip()
    print("\n" + "="*60)
    print("🚗 Flask RideShare Application Starting...")
    print("="*60)
    print(f"🖥️  Local: http://127.0.0.1:8000")
    print(f"📱 Network: http://{local_ip}:8000")
    print("="*60)
    print("\nAccess from other devices on same WiFi:")
    print(f"→ http://{local_ip}:8000")
    print("="*60 + "\n")
    

    app.run(host='0.0.0.0', port=8000, debug=True)



