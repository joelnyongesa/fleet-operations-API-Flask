import os

from flask import Flask, session, request
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_restful import Api, Resource

from models import db, Admin, Vehicle, Driver, Trip, Route, MaintenanceRecord, ChargingSession
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)

# Application configurations
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
app.config['SALQLCHEMY_TRACK_MODIFICATIONS'] = os.environ['SQLALCHEMY_TRACK_MODIFICATIONS']
app.json.compact = os.environ['APP_JSON_COMPACT']
app.config['SESSION_COOKIE_SAMESITE'] = os.environ['SESSION_COOKIE_SAMESITE']
app.config['SESSION_COOKIE_SECURE'] = os.environ['SESSION_COOKIE_SECURE']
app.config['REMEMBER_COOKIE_SECURE'] = os.environ['REMEMBER_COOKIE_SECURE']


bcrypt = Bcrypt(app)

migrate = Migrate(app=app, db=db)

db.init_app(app)

api = Api(app=app)

CORS(app=app, supports_credentials=True)

# Handlng serialization errors.
def handle_serialization_error(e, model_name, record_id):
    print(f"Error serializing {model_name} ID: {record_id}. Error: {e}")
    
    if isinstance(e, RecursionError):
        error_message = "Serialization failed due to recursion"
    else:
        error_message = f"Serialization failed: {e}"

    return {"error": error_message, "record_id": record_id}

# AUTHENTICATION AND AUTHORIZATION
class ClearSession(Resource):
    def delete(self):
        session['admin_id'] = None
        return {}, 204

class Login(Resource):
    def post(self):
        email = request.get_json()['email']
        password = request.get_json()['password']

        if not email or not password:
            return {'error': 'Username and password are required'}, 400
        
        admin = Admin.query.filter_by(email=email).first()

        if admin and admin.authenticate(password):
            session['admin_id'] = admin.id
            return admin.to_dict(), 200
        
        return {'error': 'Invalid credentials'}, 401
    
class SignUp(Resource):
    def post(self):
        email = request.get_json()['email']
        password = request.get_json()['password']

        if not email or not password:
            return {'error': 'Email and password are required'}, 400
        
        if Admin.query.filter_by(email=email).first():
            return {'error': 'Email already exists'}, 400
        
        try:
            admin = Admin(email=email)
            admin.password_hash = password
            db.session.add(admin)
            db.session.commit()
            
            session['admin_id'] = admin.id
            return admin.to_dict(), 201
        except Exception as e:
            return {'error': str(e)}, 400

class Logout(Resource):
    def delete(self):
        session['admin_id'] = None
        return {'message': 'Successfully logged out'}, 204
    
class CheckSession(Resource):
    def get(self):
        admin = Admin.query.filter_by(id=session.get('admin_id')).first()

        if admin:
            return admin.to_dict(), 200
        
        return {'error': 'Unauthorized'}, 401
    

class Vehicles(Resource):
    def get(self):
        admin_id = session.get('admin_id')
        if not admin_id:
            return {'error': 'Unauthorized'}, 401

        vehicles_list = []
        all_vehicles = Vehicle.query.all()

        for vehicle in all_vehicles:
            try:
                vehicle_dict = vehicle.to_dict(rules=(
                    '-admin.vehicles', 
                    '-driver.vehicle', 
                    '-trips.vehicle', 
                    '-maintenance_records.vehicle', 
                    '-charging_sessions.vehicle', 

                    '-trips.driver.trips', 
                    '-trips.driver.vehicle',
                    '-trips.route.trips', 
                ))
                vehicles_list.append(vehicle_dict)

            except RecursionError:
                print(f"Warning: RecursionError encountered for Vehicle ID: {vehicle.id}. Skipping.")
                vehicles_list.append({"error": "Serialization failed due to recursion", "vehicle_id": vehicle.id})
            except Exception as e:
                print(f"Error serializing Vehicle ID: {vehicle.id}. Error: {e}")
                vehicles_list.append({"error": f"Serialization failed: {e}", "vehicle_id": vehicle.id})

        return vehicles_list, 200
    
class VehicleByID(Resource):
    def get(self, id):
        admin_id = session.get('admin_id')
        if not admin_id:
            return {'error': 'Unauthorized'}, 401

        vehicle = Vehicle.query.filter_by(id=id).first()

        if not vehicle:
            return {"error": "Vehicle not found"}, 404
        
        try:
            vehicle_dict = vehicle.to_dict(rules=(
                '-admin.vehicles', 
                '-driver.vehicle', 
                '-trips.vehicle',
                '-trips.driver.vehicle',
                '-trips.route.trips', 
                '-maintenance_records.vehicle', 
                '-charging_sessions.vehicle',
            ))
            return vehicle_dict, 200
        except Exception as e:
            return handle_serialization_error(e, "Vehicle", id), 500
        
class Drivers(Resource):
    def get(self):
        admin_id = session.get('admin_id')
        if not admin_id:
            return {'error': 'Unauthorized'}, 401

        drivers_list = []
        all_drivers = Driver.query.all()

        for driver in all_drivers:
            try:
                driver_dict = driver.to_dict(rules=(
                    '-vehicle.driver', 
                    '-trips.driver',
                ))
                drivers_list.append(driver_dict)
            except Exception as e:
                drivers_list.append(handle_serialization_error(e, "Driver", driver.id))

        return drivers_list, 200
    
class DriverByID(Resource):
    def get(self, id):
        admin_id = session.get('admin_id')
        if not admin_id:
            return {'error': 'Unauthorized'}, 401

        driver = Driver.query.filter_by(id=id).first()

        if not driver:
            return {"error": "Driver not found"}, 404
        
        try:
            driver_dict = driver.to_dict(rules=(
                '-vehicle.driver', 
                '-trips.driver',
                '-trips.driver',
                '-trips.vehicle.driver',
            ))
            return driver_dict, 200
        except Exception as e:
            return handle_serialization_error(e, "Driver", id), 500
        
class ChargingSessions(Resource):
    def get(self):
        admin_id = session.get('admin_id')
        if not admin_id:
            return {'error': 'Unauthorized'}, 401

        charging_sessions_list = []
        all_charging_sessions = ChargingSession.query.all()

        for charging_session in all_charging_sessions:
            try:
                charging_session_dict = charging_session.to_dict(rules=(
                    '-vehicle.charging_sessions',
                ))
                charging_sessions_list.append(charging_session_dict)
            except Exception as e:
                charging_sessions_list.append(handle_serialization_error(e, "ChargingSession", charging_session.id))

        return charging_sessions_list, 200
    
class ChargingSessionByID(Resource):
    def get(self, id):
        admin_id = session.get('admin_id')
        if not admin_id:
            return {'error': 'Unauthorized'}, 401

        charging_session = ChargingSession.query.filter_by(id=id).first()

        if not charging_session:
            return {"error": "ChargingSession not found"}, 404

        try:
            session_dict = charging_session.to_dict(rules=(
                '-vehicle.charging_sessions',
            ))
            return session_dict, 200
        except Exception as e:
            return handle_serialization_error(e, "ChargingSession", id), 500

class MaintenanceRecords(Resource):
    def get(self):
        admin_id = session.get('admin_id')
        if not admin_id:
            return {'error': 'Unauthorized'}, 401

        records_list = []
        all_records = MaintenanceRecord.query.all()

        for record in all_records:
            try:
                record_dict = record.to_dict(rules=(
                    '-vehicle.maintenance_records',
                ))
                records_list.append(record_dict)
            except Exception as e:
                records_list.append(handle_serialization_error(e, "MaintenanceRecord", record.id))

        return records_list, 200
    
class MaintenanceRecordsByID(Resource):
    def get(self, id):
        admin_id = session.get('admin_id')
        if not admin_id:
            return {'error': 'Unauthorized'}, 401

        record = MaintenanceRecord.query.filter_by(id=id).first()

        if not record:
            return {"error": "MaintenanceRecord not found"}, 404

        try:
            record_dict = record.to_dict(rules=(
                '-vehicle.maintenance_records',
            ))
            return record_dict, 200
        except Exception as e:
            return handle_serialization_error(e, "MaintenanceRecord", id), 500

class Trips(Resource):
    def get(self):
        if not session.get('admin_id'):
            return {'error': 'Unauthorized'}, 401
        
        trips_list = []

        all_trips = Trip.query.order_by(Trip.start_time.desc()).all()

        for trip in all_trips:
            try:
                trip_dict = trip.to_dict(rules = (
                    "-vehicle.trips",
                    "-driver.trips",
                    "-route.trips",
                    "-vehicle.driver.vehicle",
                    "-driver.vehicle.driver"
                ))
                trips_list.append(trip_dict)
            except Exception as e:
                trips_list.append(handle_serialization_error(e, "Trip", trip.id))

        return trips_list, 200
    
class TripByID(Resource):
    def get(self, id):
        if not session.get('admin_id'):
            return {'error': 'Unauthorized'}, 401

        trip = Trip.query.filter_by(id=id).first()

        if not trip:
            return {"error": "Trip not found"}, 404

        try:
            trip_dict = trip.to_dict(rules = (
                "-vehicle.trips",
                "-driver.trips",
                "-route.trips",
            ))
            return trip_dict, 200
        except Exception as e:
            return handle_serialization_error(e, "Trip", id), 500
        
class Routes(Resource):
    def get(self):
        if not session.get('admin_id'):
            return {'error': 'Unauthorized'}, 401
        
        routes_list = []
        all_routes = Route.query.order_by(Route.name).all()

        for route_obj in all_routes:
            try:
                route_dict = route_obj.to_dict(rules=('-trips',))
                routes_list.append(route_dict)
            except Exception as e:
                routes_list.append(handle_serialization_error(e, "Route", route_obj.id))

        return routes_list, 200

class RouteByID(Resource):
    def get(self, id):
        if not session.get('admin_id'):
            return {'error': 'Unauthorized'}, 401

        route = Route.query.filter_by(id=id)

        if not route:
            return {"error": "Route not found"}, 404
        
        try:
            route_dict = route.to_dict(rules=(
                "-trips.route",
                "-trips.vehicle.trips",
                "-trips.driver.trips",
            ))
            return route_dict, 200
        except Exception as e:
            return handle_serialization_error(e, "Route", id), 500
    


api.add_resource(Vehicles, '/vehicles')
api.add_resource(VehicleByID, '/vehicles/<int:id>')
api.add_resource(Drivers, '/drivers')
api.add_resource(DriverByID, '/drivers/<int:id>')
api.add_resource(ChargingSessions, '/charging-sessions')
api.add_resource(ChargingSessionByID, '/charging-sessions/<int:id>')
api.add_resource(MaintenanceRecords, '/maintenance-records')
api.add_resource(MaintenanceRecordsByID, '/maintenance-records/<int:id>')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check-session')
api.add_resource(ClearSession, '/clear-session')
api.add_resource(SignUp, '/signup')
api.add_resource(Trips, '/trips')
api.add_resource(TripByID, '/trips/<int:id>')
api.add_resource(Routes, '/routes')
api.add_resource(RouteByID, '/routes/<int:id>')

if __name__ == '__main__':
    app.run(port=5555, debug=True)