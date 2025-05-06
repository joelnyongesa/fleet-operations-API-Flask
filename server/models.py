from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, Enum
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from flask_bcrypt import Bcrypt
from sqlalchemy_serializer import SerializerMixin

import datetime
import pytz


metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
})

db = SQLAlchemy(metadata=metadata)
bcrypt = Bcrypt()

class Admin(db.Model, SerializerMixin):
    __tablename__ = 'admins'

    serialize_rules = ('-vehicles.admin',)

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    _password_hash = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # Relationships
    vehicles = db.relationship('Vehicle', backref='admin', cascade='all, delete-orphan')


    @hybrid_property
    def password_hash(self):
        raise AttributeError('Password hash cannot be viewed!')
    
    @password_hash.setter
    def password_hash(self, password):
        password_hash = bcrypt.generate_password_hash(password)
        self._password_hash = password_hash.decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)
    
    def __repr__(self):
        return f'<Admin {self.email}>'
    
class Vehicle(db.Model, SerializerMixin):
    __tablename__ = 'vehicles'

    serialize_rules = (
        '-admin.vehicles', 
        '-driver.vehicle', 
        '-trips.vehicle', 
        '-maintenance_records.vehicle', 
        '-charging_sessions.vehicle',
        )

    STATUS_CHOICES = ('idle', 'active', 'maintenance', 'charging')

    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(200))
    capacity = db.Column(db.Integer)
    number_plate = db.Column(db.String(20))
    current_status = db.Column(Enum(*STATUS_CHOICES, name='vehicle_status'), nullable=False, default='idle')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # Relationships
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'))
    # admin = db.relationship('Admin', back_populates='vehicles')

    driver = db.relationship('Driver', backref='vehicle', cascade='all, delete-orphan')
    trips = db.relationship('Trip', backref='vehicle', cascade='all, delete-orphan', lazy=True)
    maintenance_records = db.relationship('MaintenanceRecord', backref='vehicle', cascade='all, delete-orphan', lazy=True)
    charging_sessions = db.relationship('ChargingSession', backref='vehicle', cascade='all, delete-orphan', lazy=True)


    @validates('current_status')
    def validate_status(self, key, value):
        if value not in self.STATUS_CHOICES:
            raise ValueError(f"Invalid status '{value}', must be one of {self.STATUS_CHOICES}")
        return value
    
    def __repr__(self):
        return f'<Vehicle {self.number_plate} ({self.model})>'
    
class Driver(db.Model, SerializerMixin):
    __tablename__ = 'drivers'

    serialize_rules = (
        '-vehicle.driver', 
        '-trips.driver',
        )
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    driving_license_number = db.Column(db.Integer, unique=True, nullable=False)
    national_id_number = db.Column(db.Integer, unique=True, nullable=False)
    phone = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())


    # Relationships
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), unique=True, nullable=True)
    # vehicle = db.relationship('Vehicle', back_populates='driver')

    trips = db.relationship('Trip', backref='driver', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<Driver {self.name}>'

class Trip(db.Model, SerializerMixin):
    __tablename__ = 'trips'

    serialize_rules = (
        '-vehicle.trips', 
        '-driver.trips', 
        '-route.trips',
        )

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)

    # Relationships
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    # driver = db.relationship('Driver', back_populates='trips', lazy=True)

    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    # vehicle = db.relationship('Vehicle', back_populates='trips', lazy=True)

    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    # route = db.relationship('Route', back_populates='trips', lazy=True)

    def __repr__(self):
        return f"<Trip ID: {self.id} (Driver: {self.driver_id}, Vehicle: {self.vehicle_id})>"

class Route(db.Model, SerializerMixin):
    __tablename__ = 'routes'

    serialize_rules = ('-trips.route',)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    start_latitude = db.Column(db.Float, nullable=False)
    start_longitude = db.Column(db.Float, nullable=False)
    end_latitude = db.Column(db.Float, nullable=False)
    end_longitude = db.Column(db.Float, nullable=False)

    # Relationships
    trips = db.relationship('Trip', backref='route', lazy=True)

    def __repr__(self):
        return f"<Route {self.name} (ID: {self.id})>"
    
class MaintenanceRecord(db.Model, SerializerMixin):
    __tablename__ = 'maintenance_records'

    serialize_rules = ('-vehicle.maintenance_records',)

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String, nullable=False)
    record_date = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(pytz.timezone('Africa/Nairobi')))
    resolved_date = db.Column(db.DateTime, nullable=True)
    resolved = db.Column(db.Boolean, default=False)

    # Relationships
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    # vehicle = db.relationship('Vehicle', back_populates='maintenance_records', lazy=True)

    def __repr__(self):
        return f"<MaintenanceRecord {self.id} (Vehicle: {self.vehicle_id} (Description: {self.description}))>"
    
class ChargingSession(db.Model, SerializerMixin):
    __tablename__ = 'charging_sessions'

    serialize_rules = ('-vehicle.charging_sessions',)

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    energy_kwh = db.Column(db.Float, nullable=False)

    # Relationships
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    # vehicle = db.relationship('Vehicle', back_populates='charging_sessions', lazy=True)

    def __repr__(self):
        return f"<ChargingSession {self.id} (Vehicle: {self.vehicle_id})>"