import os
import uuid
from datetime import datetime, timedelta

from flask import (
    Flask, render_template, redirect, url_for, request,
    flash, send_from_directory, abort, jsonify
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from werkzeug.utils import secure_filename

from models import (
    db, Building, Unit, Resident, Vendor, Ticket, TicketVendor,
    Attachment, Comment, BoardUser,
    STATUS_CHOICES, CATEGORY_CHOICES, PRIORITY_CHOICES
)

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------

def create_app(config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-in-production-please")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///ticketing.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB

    ALLOWED_PHOTO_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "heic"}
    ALLOWED_DOC_EXTENSIONS = {"pdf", "doc", "docx", "xls", "xlsx", "txt"}

    if config:
        app.config.update(config)

    db.init_app(app)

    # -----------------------------------------------------------------------
    # Flask-Login
    # -----------------------------------------------------------------------
    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access the board dashboard."

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(BoardUser, int(user_id))

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def allowed_file(filename, kind="photo"):
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if kind == "photo":
            return ext in ALLOWED_PHOTO_EXTENSIONS
        return ext in ALLOWED_DOC_EXTENSIONS

    def save_upload(file_storage, subfolder):
        filename = secure_filename(file_storage.filename)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        dest = os.path.join(app.config["UPLOAD_FOLDER"], subfolder)
        os.makedirs(dest, exist_ok=True)
        file_storage.save(os.path.join(dest, unique_name))
        return unique_name

    # -----------------------------------------------------------------------
    # Public blueprint – resident submission form
    # -----------------------------------------------------------------------
    from flask import Blueprint

    public = Blueprint("public", __name__)

    @public.route("/", methods=["GET", "POST"])
    def submit():
        residents = Resident.query.order_by(Resident.name).all()
        units = Unit.query.order_by(Unit.number).all()
        buildings = Building.query.order_by(Building.number).all()
        if request.method == "POST":
            resident_id = request.form.get("resident_id") or None
            category = request.form.get("category", "Other")
            description = request.form.get("description", "").strip()
            priority = request.form.get("priority", "Low")
            unit_id = request.form.get("unit_id") or None
            building_id = request.form.get("building_id") or None

            if not resident_id:
                flash("Please select your name.", "danger")
                return render_template("submit.html", residents=residents, units=units,
                                       buildings=buildings, categories=CATEGORY_CHOICES,
                                       priorities=PRIORITY_CHOICES)
            if not description:
                flash("Please describe the issue.", "danger")
                return render_template("submit.html", residents=residents, units=units,
                                       buildings=buildings, categories=CATEGORY_CHOICES,
                                       priorities=PRIORITY_CHOICES)

            resident = db.session.get(Resident, int(resident_id))

            # If a unit is selected, derive its building; otherwise use the building dropdown
            if unit_id:
                unit = db.session.get(Unit, int(unit_id))
                building_id = unit.building_id if unit else building_id

            ticket = Ticket(
                status="New",
                category=category,
                priority=priority,
                unit_id=int(unit_id) if unit_id else None,
                building_id=int(building_id) if building_id else None,
                submitted_by_id=resident.id if resident else None,
                submitted_by_name=resident.name if resident else None,
                submitted_by_email=resident.email if resident else None,
                description=description,
                date_submitted=datetime.utcnow(),
            )
            db.session.add(ticket)
            db.session.flush()  # get ticket.id before attaching files

            # Handle photo uploads
            for photo in request.files.getlist("photos"):
                if photo and photo.filename and allowed_file(photo.filename, "photo"):
                    fname = save_upload(photo, "photos")
                    att = Attachment(
                        ticket_id=ticket.id,
                        filename=fname,
                        original_filename=photo.filename,
                        file_type="photo",
                        content_type=photo.content_type,
                    )
                    db.session.add(att)

            db.session.commit()
            flash(f"Your request has been submitted (Ticket #{ticket.id}). Thank you!", "success")
            return redirect(url_for("public.submit"))

        return render_template("submit.html", residents=residents, units=units,
                               buildings=buildings, categories=CATEGORY_CHOICES,
                               priorities=PRIORITY_CHOICES)

    @public.route("/uploads/<path:filepath>")
    def uploaded_file(filepath):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filepath)

    # -----------------------------------------------------------------------
    # Auth blueprint
    # -----------------------------------------------------------------------
    auth = Blueprint("auth", __name__, url_prefix="/board")

    @auth.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("board.dashboard"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = BoardUser.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(request.args.get("next") or url_for("board.dashboard"))
            flash("Invalid username or password.", "danger")
        return render_template("login.html")

    @auth.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("auth.login"))

    # -----------------------------------------------------------------------
    # Board blueprint
    # -----------------------------------------------------------------------
    board = Blueprint("board", __name__, url_prefix="/board")

    @board.before_request
    @login_required
    def require_login():
        pass

    # ---------- Dashboard ---------------------------------------------------

    @board.route("/")
    @login_required
    def dashboard():
        open_tickets = Ticket.query.filter(Ticket.status.in_(["New", "Assigned", "Waiting"])).all()
        recent_completed = (
            Ticket.query
            .filter(Ticket.status == "Completed")
            .order_by(Ticket.date_completed.desc())
            .limit(10)
            .all()
        )
        # Stats
        stats = {
            "new": Ticket.query.filter_by(status="New").count(),
            "assigned": Ticket.query.filter_by(status="Assigned").count(),
            "waiting": Ticket.query.filter_by(status="Waiting").count(),
            "completed": Ticket.query.filter_by(status="Completed").count(),
        }
        by_category = {}
        for cat in CATEGORY_CHOICES:
            by_category[cat] = Ticket.query.filter(
                Ticket.category == cat,
                Ticket.status.in_(["New", "Assigned", "Waiting"])
            ).count()
        return render_template(
            "board/dashboard.html",
            open_tickets=open_tickets,
            recent_completed=recent_completed,
            stats=stats,
            by_category=by_category,
        )

    # ---------- Ticket list -------------------------------------------------

    @board.route("/tickets")
    @login_required
    def ticket_list():
        # Filters
        status = request.args.get("status", "")
        category = request.args.get("category", "")
        priority = request.args.get("priority", "")
        unit_id = request.args.get("unit_id", "")
        building_id = request.args.get("building_id", "")
        search = request.args.get("search", "").strip()
        timeframe = request.args.get("timeframe", "")

        q = Ticket.query

        if status:
            if status == "open":
                q = q.filter(Ticket.status.in_(["New", "Assigned", "Waiting"]))
            else:
                q = q.filter(Ticket.status == status)
        if category:
            q = q.filter(Ticket.category == category)
        if priority:
            q = q.filter(Ticket.priority == priority)
        if unit_id:
            q = q.filter(Ticket.unit_id == int(unit_id))
        if building_id:
            building = db.session.get(Building, int(building_id))
            if building:
                unit_ids = [u.id for u in building.units]
                q = q.filter(
                    db.or_(
                        Ticket.unit_id.in_(unit_ids),
                        Ticket.building_id == int(building_id)
                    )
                )
        if search:
            like = f"%{search}%"
            q = q.filter(
                db.or_(
                    Ticket.description.ilike(like),
                    Ticket.submitted_by_name.ilike(like),
                    Ticket.submitted_by_email.ilike(like),
                )
            )
        if timeframe == "12months":
            cutoff = datetime.utcnow() - timedelta(days=365)
            q = q.filter(Ticket.date_submitted >= cutoff)

        tickets = q.order_by(Ticket.date_submitted.desc()).all()

        units = Unit.query.order_by(Unit.number).all()
        buildings = Building.query.order_by(Building.number).all()

        return render_template(
            "board/ticket_list.html",
            tickets=tickets,
            units=units,
            buildings=buildings,
            categories=CATEGORY_CHOICES,
            priorities=PRIORITY_CHOICES,
            statuses=STATUS_CHOICES,
            filters={
                "status": status, "category": category, "priority": priority,
                "unit_id": unit_id, "building_id": building_id,
                "search": search, "timeframe": timeframe
            },
        )

    # ---------- Ticket detail / edit ----------------------------------------

    @board.route("/tickets/<int:ticket_id>", methods=["GET", "POST"])
    @login_required
    def ticket_detail(ticket_id):
        ticket = db.get_or_404(Ticket, ticket_id)
        units = Unit.query.order_by(Unit.number).all()
        buildings = Building.query.order_by(Building.number).all()
        residents = Resident.query.order_by(Resident.name).all()
        vendors = Vendor.query.order_by(Vendor.name).all()

        if request.method == "POST":
            action = request.form.get("action", "update")

            if action == "comment":
                body = request.form.get("body", "").strip()
                if body:
                    c = Comment(
                        ticket_id=ticket.id,
                        author=current_user.username,
                        body=body,
                    )
                    db.session.add(c)
                    db.session.commit()
                    flash("Comment added.", "success")
                return redirect(url_for("board.ticket_detail", ticket_id=ticket.id))

            if action == "upload":
                for photo in request.files.getlist("photos"):
                    if photo and photo.filename and allowed_file(photo.filename, "photo"):
                        fname = save_upload(photo, "photos")
                        db.session.add(Attachment(
                            ticket_id=ticket.id, filename=fname,
                            original_filename=photo.filename, file_type="photo",
                            content_type=photo.content_type,
                        ))
                for doc in request.files.getlist("documents"):
                    if doc and doc.filename and allowed_file(doc.filename, "document"):
                        fname = save_upload(doc, "documents")
                        db.session.add(Attachment(
                            ticket_id=ticket.id, filename=fname,
                            original_filename=doc.filename, file_type="document",
                            content_type=doc.content_type,
                        ))
                db.session.commit()
                flash("Attachments uploaded.", "success")
                return redirect(url_for("board.ticket_detail", ticket_id=ticket.id))

            # Default: update ticket fields
            old_status = ticket.status
            ticket.status = request.form.get("status", ticket.status)
            ticket.category = request.form.get("category", ticket.category)
            ticket.priority = request.form.get("priority", ticket.priority)
            ticket.description = request.form.get("description", ticket.description)

            unit_id = request.form.get("unit_id") or None
            ticket.unit_id = int(unit_id) if unit_id else None
            if ticket.unit_id:
                unit = db.session.get(Unit, ticket.unit_id)
                ticket.building_id = unit.building_id if unit else None
            else:
                bldg_id = request.form.get("building_id") or None
                ticket.building_id = int(bldg_id) if bldg_id else None

            assigned_id = request.form.get("assigned_to_resident_id") or None
            ticket.assigned_to_resident_id = int(assigned_id) if assigned_id else None

            est = request.form.get("estimated_cost") or None
            ticket.estimated_cost = float(est) if est else None
            fin = request.form.get("final_cost") or None
            ticket.final_cost = float(fin) if fin else None

            # Timestamps based on status transitions
            if ticket.status != "New" and not ticket.date_assigned:
                ticket.date_assigned = datetime.utcnow()
            if ticket.status == "Completed" and not ticket.date_completed:
                ticket.date_completed = datetime.utcnow()
            elif ticket.status != "Completed":
                ticket.date_completed = None

            # Vendors (multi-select)
            TicketVendor.query.filter_by(ticket_id=ticket.id).delete()
            for vid in request.form.getlist("vendor_ids"):
                db.session.add(TicketVendor(ticket_id=ticket.id, vendor_id=int(vid)))

            db.session.commit()
            flash("Ticket updated.", "success")
            return redirect(url_for("board.ticket_detail", ticket_id=ticket.id))

        photos = ticket.attachments.filter_by(file_type="photo").all()
        documents = ticket.attachments.filter_by(file_type="document").all()

        return render_template(
            "board/ticket_detail.html",
            ticket=ticket,
            units=units,
            buildings=buildings,
            residents=residents,
            vendors=vendors,
            photos=photos,
            documents=documents,
            categories=CATEGORY_CHOICES,
            priorities=PRIORITY_CHOICES,
            statuses=STATUS_CHOICES,
        )

    @board.route("/tickets/<int:ticket_id>/delete", methods=["POST"])
    @login_required
    def delete_ticket(ticket_id):
        ticket = db.get_or_404(Ticket, ticket_id)
        # Remove uploaded files
        for att in ticket.attachments:
            subfolder = "photos" if att.file_type == "photo" else "documents"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], subfolder, att.filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        db.session.delete(ticket)
        db.session.commit()
        flash(f"Ticket #{ticket_id} deleted.", "success")
        return redirect(url_for("board.ticket_list"))

    @board.route("/tickets/<int:ticket_id>/delete-attachment/<int:att_id>", methods=["POST"])
    @login_required
    def delete_attachment(ticket_id, att_id):
        att = db.get_or_404(Attachment, att_id)
        if att.ticket_id != ticket_id:
            abort(403)
        subfolder = "photos" if att.file_type == "photo" else "documents"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], subfolder, att.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        db.session.delete(att)
        db.session.commit()
        flash("Attachment removed.", "success")
        return redirect(url_for("board.ticket_detail", ticket_id=ticket_id))

    # ---------- Admin: Residents --------------------------------------------

    @board.route("/residents")
    @login_required
    def residents():
        residents = Resident.query.order_by(Resident.name).all()
        units = Unit.query.order_by(Unit.number).all()
        return render_template("board/residents.html", residents=residents, units=units)

    @board.route("/residents/add", methods=["POST"])
    @login_required
    def add_resident():
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        unit_id = request.form.get("unit_id") or None
        if not name:
            flash("Name is required.", "danger")
            return redirect(url_for("board.residents"))
        r = Resident(name=name, email=email, phone=phone,
                     unit_id=int(unit_id) if unit_id else None)
        db.session.add(r)
        db.session.commit()
        flash("Resident added.", "success")
        return redirect(url_for("board.residents"))

    @board.route("/residents/<int:resident_id>/delete", methods=["POST"])
    @login_required
    def delete_resident(resident_id):
        r = db.get_or_404(Resident, resident_id)
        db.session.delete(r)
        db.session.commit()
        flash("Resident removed.", "success")
        return redirect(url_for("board.residents"))

    # ---------- Admin: Vendors ----------------------------------------------

    @board.route("/vendors")
    @login_required
    def vendors():
        vendors = Vendor.query.order_by(Vendor.name).all()
        return render_template("board/vendors.html", vendors=vendors)

    @board.route("/vendors/add", methods=["POST"])
    @login_required
    def add_vendor():
        v = Vendor(
            name=request.form.get("name", "").strip(),
            contact_person=request.form.get("contact_person", "").strip(),
            phone=request.form.get("phone", "").strip(),
            email=request.form.get("email", "").strip(),
            specialty=request.form.get("specialty", "").strip(),
            notes=request.form.get("notes", "").strip(),
        )
        if not v.name:
            flash("Vendor name is required.", "danger")
            return redirect(url_for("board.vendors"))
        db.session.add(v)
        db.session.commit()
        flash("Vendor added.", "success")
        return redirect(url_for("board.vendors"))

    @board.route("/vendors/<int:vendor_id>/edit", methods=["POST"])
    @login_required
    def edit_vendor(vendor_id):
        v = db.get_or_404(Vendor, vendor_id)
        v.name = request.form.get("name", v.name).strip()
        v.contact_person = request.form.get("contact_person", v.contact_person).strip()
        v.phone = request.form.get("phone", v.phone).strip()
        v.email = request.form.get("email", v.email).strip()
        v.specialty = request.form.get("specialty", v.specialty).strip()
        v.notes = request.form.get("notes", v.notes).strip()
        db.session.commit()
        flash("Vendor updated.", "success")
        return redirect(url_for("board.vendors"))

    @board.route("/vendors/<int:vendor_id>/delete", methods=["POST"])
    @login_required
    def delete_vendor(vendor_id):
        v = db.get_or_404(Vendor, vendor_id)
        db.session.delete(v)
        db.session.commit()
        flash("Vendor removed.", "success")
        return redirect(url_for("board.vendors"))

    # ---------- Admin: Units ------------------------------------------------

    @board.route("/units")
    @login_required
    def units():
        units = Unit.query.order_by(Unit.number).all()
        buildings = Building.query.order_by(Building.number).all()
        return render_template("board/units.html", units=units, buildings=buildings)

    @board.route("/units/<int:unit_id>")
    @login_required
    def unit_detail(unit_id):
        unit = db.get_or_404(Unit, unit_id)
        tickets = unit.tickets.order_by(Ticket.date_submitted.desc()).all()
        return render_template("board/unit_detail.html", unit=unit, tickets=tickets,
                               statuses=STATUS_CHOICES)

    # ---------- Register blueprints -----------------------------------------
    app.register_blueprint(public)
    app.register_blueprint(auth)
    app.register_blueprint(board)

    # -----------------------------------------------------------------------
    # DB init command
    # -----------------------------------------------------------------------
    @app.cli.command("init-db")
    def init_db():
        """Create tables and seed initial data."""
        db.create_all()
        from seed import seed_data
        seed_data(db)
        print("Database initialised.")

    @app.cli.command("create-user")
    def create_user():
        """Interactively create a board user."""
        import getpass
        username = input("Username: ").strip()
        email = input("Email (optional): ").strip()
        password = getpass.getpass("Password: ")
        is_admin = input("Admin? (y/N): ").strip().lower() == "y"
        u = BoardUser(username=username, email=email, is_admin=is_admin)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        print(f"User '{username}' created.")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
