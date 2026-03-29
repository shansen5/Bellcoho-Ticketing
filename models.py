from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Building(db.Model):
    __tablename__ = "buildings"
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False, unique=True)  # 1-12
    name = db.Column(db.String(100))

    units = db.relationship("Unit", back_populates="building", lazy="dynamic")
    tickets = db.relationship("Ticket", back_populates="building", lazy="dynamic")

    def __repr__(self):
        return f"Building {self.number}" + (f" ({self.name})" if self.name else "")

    @property
    def display_name(self):
        if self.name:
            return f"Bldg {self.number} – {self.name}"
        return f"Building {self.number}"


class Unit(db.Model):
    __tablename__ = "units"
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False, unique=True)  # 1-33
    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"), nullable=False)
    notes = db.Column(db.Text)

    building = db.relationship("Building", back_populates="units")
    residents = db.relationship("Resident", back_populates="unit", lazy="dynamic")
    tickets = db.relationship("Ticket", back_populates="unit", lazy="dynamic")

    def __repr__(self):
        return f"Unit {self.number}"


class Resident(db.Model):
    __tablename__ = "residents"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(200))
    phone = db.Column(db.String(30))
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=True)

    unit = db.relationship("Unit", back_populates="residents")
    submitted_tickets = db.relationship(
        "Ticket", foreign_keys="Ticket.submitted_by_id", back_populates="submitted_by", lazy="dynamic"
    )
    assigned_tickets = db.relationship(
        "Ticket", foreign_keys="Ticket.assigned_to_resident_id", back_populates="assigned_to_resident", lazy="dynamic"
    )

    def __repr__(self):
        return self.name


class Vendor(db.Model):
    __tablename__ = "vendors"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    contact_person = db.Column(db.String(150))
    phone = db.Column(db.String(30))
    email = db.Column(db.String(200))
    specialty = db.Column(db.String(100))  # Plumbing, Electrical, HVAC, etc.
    notes = db.Column(db.Text)

    ticket_vendors = db.relationship("TicketVendor", back_populates="vendor", lazy="dynamic")

    def __repr__(self):
        return self.name


# Association table for Ticket <-> Vendor (many-to-many)
class TicketVendor(db.Model):
    __tablename__ = "ticket_vendors"
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id"), nullable=False)

    ticket = db.relationship("Ticket", back_populates="ticket_vendors")
    vendor = db.relationship("Vendor", back_populates="ticket_vendors")


STATUS_CHOICES = ["New", "Assigned", "Waiting", "Completed"]
CATEGORY_CHOICES = ["Heating", "Plumbing", "Electrical", "Exterior", "Appliances", "Structural", "Other"]
PRIORITY_CHOICES = ["Low", "Normal", "Urgent"]


class Ticket(db.Model):
    __tablename__ = "tickets"
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False, default="New")
    category = db.Column(db.String(30), nullable=False)
    priority = db.Column(db.String(10), nullable=False, default="Low")

    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=True)
    # Building can be derived from unit, or set directly if unit is null
    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"), nullable=True)

    submitted_by_id = db.Column(db.Integer, db.ForeignKey("residents.id"), nullable=True)
    submitted_by_name = db.Column(db.String(150))   # fallback if not in residents table
    submitted_by_email = db.Column(db.String(200))  # fallback email

    assigned_to_resident_id = db.Column(db.Integer, db.ForeignKey("residents.id"), nullable=True)

    description = db.Column(db.Text, nullable=False)
    estimated_cost = db.Column(db.Float, nullable=True)
    final_cost = db.Column(db.Float, nullable=True)

    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)
    date_assigned = db.Column(db.DateTime, nullable=True)
    date_completed = db.Column(db.DateTime, nullable=True)

    # Relationships
    unit = db.relationship("Unit", back_populates="tickets")
    building = db.relationship("Building", back_populates="tickets")
    submitted_by = db.relationship(
        "Resident", foreign_keys=[submitted_by_id], back_populates="submitted_tickets"
    )
    assigned_to_resident = db.relationship(
        "Resident", foreign_keys=[assigned_to_resident_id], back_populates="assigned_tickets"
    )
    ticket_vendors = db.relationship("TicketVendor", back_populates="ticket", lazy="dynamic")
    attachments = db.relationship("Attachment", back_populates="ticket", lazy="dynamic")
    comments = db.relationship("Comment", back_populates="ticket", order_by="Comment.created_at", lazy="dynamic")

    @property
    def effective_building(self):
        """Return building from unit if set, else from direct building field."""
        if self.unit:
            return self.unit.building
        return self.building

    @property
    def is_open(self):
        return self.status in ("New", "Assigned", "Waiting")

    @property
    def vendors(self):
        return [tv.vendor for tv in self.ticket_vendors]

    def __repr__(self):
        return f"Ticket #{self.id}: {self.category}"


class Attachment(db.Model):
    __tablename__ = "attachments"
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_type = db.Column(db.String(10))  # 'photo' or 'document'
    content_type = db.Column(db.String(100))
    # Optional Google Drive link
    drive_url = db.Column(db.String(500))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket = db.relationship("Ticket", back_populates="attachments")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    author = db.Column(db.String(150))   # Board member name or "System"
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket = db.relationship("Ticket", back_populates="comments")


class BoardUser(UserMixin, db.Model):
    """Board members / maintenance coordinators who log in to manage tickets."""
    __tablename__ = "board_users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(200))
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return self.username
