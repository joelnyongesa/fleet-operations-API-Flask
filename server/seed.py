import random
from faker import Faker
from app import app
from models import db, Admin, Vehicle, Driver, Trip, Route, MaintenanceRecord, ChargingSession
import datetime
import pytz

NUM_VEHICLES = 15
NUM_DRIVERS = 20
NUM_MAINTENANCE_RECORDS_PER_VEHICLE = 3
NUM_CHARGING_SESSIONS_PER_VEHICLE = 5
NUM_TRIPS = 50

fake = Faker()
nairobi_tz = pytz.timezone('Africa/Nairobi')

ROUTE_DATA = [
    {"name": "Nairobi CBD - Juja", "start_latitude": -1.286389, "start_longitude": 36.817223, "end_latitude": -1.1008, "end_longitude": 37.0108},
    {"name": "Nairobi CBD - Kikuyu", "start_latitude": -1.286389, "start_longitude": 36.817223, "end_latitude": -1.2500, "end_longitude": 36.6667},
    {"name": "Nairobi CBD - JKIA", "start_latitude": -1.286389, "start_longitude": 36.817223, "end_latitude": -1.319167, "end_longitude": 36.9275},
    {"name": "City Stadium - Dandora", "start_latitude": -1.2994, "start_longitude": 36.8379, "end_latitude": -1.2536, "end_longitude": 36.9084},
    {"name": "CBD - Civo (Upper Hill)", "start_latitude": -1.286389, "start_longitude": 36.817223, "end_latitude": -1.2990, "end_longitude": 36.8153}, # Assuming Civo is Upper Hill area
    {"name": "CBD - Utawala", "start_latitude": -1.286389, "start_longitude": 36.817223, "end_latitude": -1.3056, "end_longitude": 36.9768}
]


def generate_kenyan_plate(used_plates):
    while True:
        prefix = "K" + random.choice("BCDFGHJKLMNPQRSTVWXYZ") + random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        digits = str(random.randint(100, 999))
        suffix = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        plate = f"{prefix} {digits}{suffix}"
        if plate not in used_plates:
            used_plates.add(plate)
            return plate

def generate_kenyan_phone(used_phones):
     while True:
        prefix = random.choice(["+2547", "+2541"]) 
        if prefix == "+2547":
             number = f"{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"
        else: # +2541
             number = f"{random.randint(10, 19)}{random.randint(100000, 999999)}" 

        full_number = f"{prefix}{number[:7]}" 

        if full_number not in used_phones:
             used_phones.add(full_number)
             return full_number
        
if __name__ == '__main__':
    with app.app_context():
        print("Clearing existing data...")
        ChargingSession.query.delete()
        MaintenanceRecord.query.delete()
        Trip.query.delete()
        Driver.query.delete()
        Vehicle.query.delete()
        Admin.query.delete()
        Route.query.delete()
        db.session.commit()

        print("Seeding Admins...")
        admins = []
        for i in range(2):
            admin = Admin(
                email=f'admin{i+1}@basi-go-clone.com',
                _password_hash=f'password{123 + i}'
            )
            admins.append(admin)
        demo_admin = Admin(
            email="demo@email.com",
            _password_hash="Fleet!Demo2025&"
        )
        admins.append(demo_admin)
        db.session.add_all(admins)
        db.session.commit()

        print("Seeding Routes...")
        routes = []
        for data in ROUTE_DATA:
            route = Route(**data)
            routes.append(route)
        db.session.add_all(routes)
        db.session.commit()

        print("Seeding Vehicles...")
        vehicles = []
        used_plates = set()
        vehicle_models = ["BYD K9 Electric", "Yutong E12", "Scania Citywide LF BEV", "Volvo 7900 Electric", "Mercedes-Benz eCitaro"]
        for i in range(NUM_VEHICLES):
            vehicle = Vehicle(
                model=random.choice(vehicle_models),
                capacity=random.randint(40, 75),
                number_plate=generate_kenyan_plate(used_plates),
                current_status=random.choice(Vehicle.STATUS_CHOICES),
                admin_id=random.choice(admins).id
            )
            vehicles.append(vehicle)
        db.session.add_all(vehicles)
        db.session.commit()

        print("Seeding Drivers...")
        drivers = []
        available_vehicles = list(vehicles)
        used_phones = set()
        used_emails = set()

        for i in range(NUM_DRIVERS):
            while True:
                email = fake.unique.email()
                if email not in used_emails:
                    used_emails.add(email)
                    break
            phone = generate_kenyan_phone(used_phones)

            driver = Driver(
                name=fake.name(),
                driving_license_number=fake.unique.random_number(digits=8, fix_len=True),
                national_id_number=fake.unique.random_number(digits=8, fix_len=True),
                phone=phone,
                email=email,
                is_available=random.choice([True, True, False]) # Skew towards available
            )

            if driver.is_available and available_vehicles and random.random() < 0.7:
                assigned_vehicle = random.choice(available_vehicles)
                driver.vehicle = assigned_vehicle
                available_vehicles.remove(assigned_vehicle)

            drivers.append(driver)
        db.session.add_all(drivers)
        fake.unique.clear()
        db.session.commit()

        print("Seeding Maintenance Records...")
        maintenance_records = []
        maintenance_desc = [
            "Routine Inspection", "Tire Rotation & Check", "Brake System Check",
            "Oil & Fluid Change", "Battery Health Check", "Software Update",
            "Wiper Blade Replacement", "Headlight/Taillight Check", "Charging Port Clean/Check"
        ]
        for vehicle in vehicles:
            for _ in range(NUM_MAINTENANCE_RECORDS_PER_VEHICLE):
                record_date = fake.date_time_between(start_date='-1y', end_date='now', tzinfo=nairobi_tz)
                is_resolved = random.choice([True, True, False])
                resolved_date = None
                if is_resolved:
                     delta_days = random.randint(1, 10)
                     resolved_date = record_date + datetime.timedelta(days=delta_days)
                     now_aware = datetime.datetime.now(nairobi_tz)
                     if resolved_date > now_aware:
                         resolved_date = fake.date_time_between(start_date=record_date, end_date='now', tzinfo=nairobi_tz)


                record = MaintenanceRecord(
                    description=random.choice(maintenance_desc),
                    record_date=record_date,
                    resolved=is_resolved,
                    resolved_date=resolved_date,
                    vehicle_id=vehicle.id
                )
                maintenance_records.append(record)
        db.session.add_all(maintenance_records)

        print("Seeding Charging Sessions...")
        charging_sessions = []
        for vehicle in vehicles:
             if vehicle.current_status in ['idle', 'charging', 'maintenance']:
                for _ in range(NUM_CHARGING_SESSIONS_PER_VEHICLE):
                    start_time = fake.date_time_between(start_date='-6m', end_date='now', tzinfo=nairobi_tz)
                    duration_hours = random.uniform(0.5, 6.0)
                    end_time = start_time + datetime.timedelta(hours=duration_hours)
                    is_ongoing = random.random() < 0.1
                    final_end_time = None if is_ongoing else end_time

                    now_aware = datetime.datetime.now(nairobi_tz)
                    if final_end_time and final_end_time > now_aware:
                        final_end_time = fake.date_time_between(start_date=start_time, end_date='now', tzinfo=nairobi_tz)


                    session = ChargingSession(
                        start_time=start_time,
                        end_time=final_end_time,
                        energy_kwh=round(duration_hours * random.uniform(40, 60), 2),
                        vehicle_id=vehicle.id
                    )
                    charging_sessions.append(session)
        db.session.add_all(charging_sessions)

        print("Seeding Trips...")
        trips = []
        available_drivers_for_trips = [d for d in drivers if d.is_available]
        available_vehicles_for_trips = [v for v in vehicles if v.current_status in ['idle', 'active']]

        if not available_drivers_for_trips or not available_vehicles_for_trips or not routes:
             print("Warning: Not enough available drivers, vehicles, or routes to create trips.")
        else:
            for _ in range(NUM_TRIPS):
                 driver = random.choice(available_drivers_for_trips)
                 vehicle = random.choice(available_vehicles_for_trips)
                 route = random.choice(routes)

                 start_time = fake.date_time_between(start_date='-3m', end_date='now', tzinfo=nairobi_tz)
                 duration_minutes = random.randint(30, 180) 
                 end_time = start_time + datetime.timedelta(minutes=duration_minutes)
                 is_completed = random.choice([True, True, True, False]) 
                 final_end_time = end_time if is_completed else None

                 now_aware = datetime.datetime.now(nairobi_tz)
                 if final_end_time and final_end_time > now_aware:
                    final_end_time = fake.date_time_between(start_date=start_time, end_date='now', tzinfo=nairobi_tz)
                    if not is_completed:
                         is_completed = True


                 trip = Trip(
                    start_time=start_time,
                    end_time=final_end_time,
                    completed=is_completed,
                    driver_id=driver.id,
                    vehicle_id=vehicle.id,
                    route_id=route.id
                 )
                 trips.append(trip)
            db.session.add_all(trips)

        print("Committing all new data...")
        db.session.commit()
        print("Database seeded successfully!")