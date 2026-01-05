from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import LoginManager, login_required, current_user
from models import db, User, Place, Spot, Category, Rating, PlannedRoute, datetime
from forms import PlaceForm
from auth import auth_bp
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import os
from types import SimpleNamespace
import random


# ---------------- INIT APP ----------------
app = Flask(__name__, template_folder='templates')
app.config["SECRET_KEY"] = "super-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

app.register_blueprint(auth_bp)
db.init_app(app)
migrate = Migrate(app, db)

# ---------------- LOGIN MANAGER ----------------
login_manager = LoginManager()
login_manager.login_view = "auth_bp.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- PUBLIC ROUTES ----------------
@app.route("/")
def index():
    spots = [
        SimpleNamespace(
            title="მარტვილის კანიონი",
            description="ზურმუხტისფერი წყლები, რომლებიც უძველეს კირქვის წარმონაქმნებში მოედინება, იდეალურია ნავით გასეირნებისთვის.",
            region="სამეგრელო",
            rating=4.9,
            image="samegrelo.jpg",
            badges="წყალი, ფოტოგრაფია"
        ),
        SimpleNamespace(
            title="ოკაცეს კანიონი",
            description="გასაოცარი დაკიდული ბილიკი ღრმა ოკაცეს კანიონზე, საიდანაც შთამბეჭდავი ხედი იშლება.",
            region="იმერეთი",
            rating=4.8,
            image="imereti.jpg",
            badges="ხედი,ლაშქრობა"
        ),
        SimpleNamespace(
            title="ილიას (ყვარლის) ტბა",
            description="მშვიდი წყლები, ტყით შემოსაზღვრულ გორებსა და დასასვენებელ პარკს შორის გაშლილი, ილიას (ყვარლის) ტბას იდეალურ ადგილად აქცევს სეირნობისთვის.",
            region="კახეთი",
            rating=4.7,
            image="kaxeti.jpg",
            badges="პიკნიკი,ლაშქრობა"
        ),
        SimpleNamespace(
            title="შუქურას პალმების ბილიკი",
            description="პალმებით გაწყობილი ბილიკი, ტბასა და ზღვის სანაპიროს შორის გადაჭიმული, შუქურას სივრცეს აქცევს მშვიდ სეირნობისა და ბუნებაში დასვენების იდეალურ ადგილად.",
            region="აჭარა",
            rating=4.6,
            image="awara.jpg",
            badges="ეკოტურიზმი,დასვენება"
        ),
    ]

    categories = [
        SimpleNamespace(name="მთები", icon="mountains.svg", count=18),
        SimpleNamespace(name="ჩანჩქერები", icon="waterfall.svg", count=12),
        SimpleNamespace(name="ისტორიული", icon="historic.svg", count=15),
        SimpleNamespace(name="ტყეები", icon="forest.svg", count=10),
        SimpleNamespace(name="ხედები", icon="view.svg", count=22),
        SimpleNamespace(name="ლაშქრობა", icon="camp.svg", count=8),
        SimpleNamespace(name="ტბები", icon="lakes.svg", count=6),
        SimpleNamespace(name="მზის ამოსვლა", icon="sunset.svg", count=9),
    ]

    stats = SimpleNamespace(
        spots=len(spots),
        regions=4,
        visitors=1200
    )

    return render_template(
        "index.html",
        spots=spots,
        categories=categories,
        stats=stats
    )

# ---------------- LOGGED-IN ROUTES ----------------
@app.route("/home")
@login_required
def home():
    # All places for reference
    places = Place.query.all()

    # Random suggested places, max 10
    suggested_places = random.sample(places, min(10, len(places)))

    # Favorites — random or just limit first N
    user_favorites = current_user.favorites  # SQLAlchemy relationship
    max_favorites = 6
    if len(user_favorites) > max_favorites:
        # pick random subset of favorites
        favorites_to_show = random.sample(user_favorites, max_favorites)
    else:
        favorites_to_show = user_favorites

    # List of favorite IDs for your heart buttons
    user_favorite_ids = [p.id for p in current_user.favorites]

    planned_count = PlannedRoute.query.filter_by(user_id=current_user.id).count()

    return render_template(
        "home.html",
        places=places,
        suggested_places=suggested_places,
        favorites_to_show=favorites_to_show,  # pass limited favorites
        user_favorite_ids=user_favorite_ids,
        planned_count=planned_count
    )

@app.route("/profile")
@login_required
def profile():
    favorites = current_user.favorites
    planned_routes = PlannedRoute.query.filter_by(user_id=current_user.id).all()
    avg_rating = current_user.calculate_avg_rating()
    return render_template(
        "profile.html",
        favorites=favorites,
        planned_routes=planned_routes,
        avg_rating=avg_rating
    )

@app.route("/delete_route/<int:route_id>", methods=["POST"])
@login_required
def delete_route(route_id):
    route = PlannedRoute.query.get_or_404(route_id)

    # security check: users can delete ONLY their own routes
    if route.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    db.session.delete(route)
    db.session.commit()
    flash("მარშრუტი წაიშალა", "success")
    return redirect(url_for("profile"))


@app.route("/delete_place/<int:place_id>", methods=["POST"])
@login_required
def delete_place(place_id):
    if not current_user.is_admin:
        abort(403)

    place = Place.query.get_or_404(place_id)
    db.session.delete(place)
    db.session.commit()
    flash("Place deleted", "success")
    return redirect(url_for("categories"))


@app.route("/map")
def map_page():
    places = Place.query.filter(
        Place.latitude.isnot(None),
        Place.longitude.isnot(None)
    ).all()
    return render_template("map.html", places=places)


@app.route("/categories")
@login_required
def categories():
    search_query = request.args.get("q", "").strip()
    selected_category = request.args.get("category", "").strip()

    query = Place.query
    if selected_category and selected_category != "all":
        query = query.filter(Place.category == selected_category)
    elif search_query:
        query = query.filter(Place.name.ilike(f"%{search_query}%"))

    places = query.all()

    category_map = {
        'mountains': 'მთები',
        'waterfalls': 'ჩანჩქერები/კანიონები',
        'historic': 'ისტორიული',
        'forests': 'ტყეები',
        'views': 'ხედები',
        'hiking': 'ლაშქრობა',
        'lakes': 'ტბები',
        'sunrise': 'მზის ამოსვლა'
    }

    return render_template(
        "categories.html",
        places=places,
        category_map=category_map
    )

@app.route("/add-place", methods=["GET", "POST"])
@login_required
def add_place():
    form = PlaceForm()
    if form.validate_on_submit():
        # Handle image upload
        filename = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.image.data.save(upload_path)

        # Get coordinates from form
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        print("LAT:", latitude, "LNG:", longitude)  # debug line

        if not latitude or not longitude:
            flash("გთხოვ აირჩიე ადგილი რუკაზე", "danger")
            return redirect(request.url)

        # Create Place
        place = Place(
            name=form.name.data,
            description=form.description.data,
            category=form.category.data,
            region=form.region.data,
            image=filename,
            latitude=float(latitude),
            longitude=float(longitude)
        )

        db.session.add(place)
        db.session.commit()
        flash("Place added successfully!", "success")
        return redirect(url_for("categories"))

    return render_template("add-place.html", form=form)


@app.route('/delete_rating/<int:rating_id>', methods=['POST'])
@login_required
def delete_rating(rating_id):
    rating = Rating.query.get_or_404(rating_id)

    # Only author or admin
    if rating.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    try:
        db.session.delete(rating)
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route("/place/<int:place_id>", methods=["GET", "POST"])
@login_required
def place_detail(place_id):
    place = Place.query.get_or_404(place_id)

    if request.method == "POST":
        action = request.form.get("action")
        if action == "favorite":
            if place in current_user.favorites:
                current_user.favorites.remove(place)
            else:
                current_user.favorites.append(place)

        elif action == "route":
            existing_route = PlannedRoute.query.filter_by(user_id=current_user.id, place_id=place.id).first()
            if not existing_route:
                planned_route = PlannedRoute(user_id=current_user.id, place_id=place.id, date=datetime.utcnow())
                db.session.add(planned_route)

        elif action == "rating":
            stars = float(request.form.get("stars"))
            comment = request.form.get("comment")
            image_file = request.files.get("image")
            filename = None
            if image_file and image_file.filename != "":
                filename = secure_filename(image_file.filename)
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_rating = Rating(user_id=current_user.id, place_id=place.id, stars=stars, comment=comment, image=filename)
            db.session.add(new_rating)

        db.session.commit()
        return redirect(url_for("place_detail", place_id=place.id))

    avg_rating = round(sum(r.stars for r in place.ratings)/len(place.ratings), 1) if place.ratings else 0
    return render_template("place_detail.html", place=place, ratings=place.ratings, avg_rating=avg_rating)

@app.route("/category/<string:category_name>")
@login_required
def category_places(category_name):
    suggested_places = Place.query.filter_by(category=category_name).all()
    user_favorite_ids = [p.id for p in current_user.favorites]
    return render_template(
        "dashboard.html",
        suggested_places=suggested_places,
        user_favorite_ids=user_favorite_ids
    )

@app.route("/toggle_favorite/<int:place_id>", methods=["POST"])
@login_required
def toggle_favorite(place_id):
    place = Place.query.get_or_404(place_id)
    if place in current_user.favorites:
        current_user.favorites.remove(place)
        db.session.commit()
        return {"status": "removed"}
    else:
        current_user.favorites.append(place)
        db.session.commit()
        return {"status": "added"}


@app.route('/booking', methods=['GET', 'POST'])
@login_required  # must be logged in to book
def booking():
    spots = Place.query.all()  # fetch all spots for the select dropdown

    if request.method == 'POST':
        spot_name = request.form['spot']
        date_selected = request.form['date']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        # Find the Spot in DB
        spot = Place.query.filter_by(name=spot_name).first()
        if not spot:
            flash("აირჩიე ვალიდური ადგილი!", "danger")
            return redirect(url_for('booking'))

        # Save the booking to PlannedRoute
        new_route = PlannedRoute(
            user_id=current_user.id,
            place_id=spot.id,
            date=datetime.strptime(date_selected, "%Y-%m-%d")  # make sure the date is correct
        )
        db.session.add(new_route)
        db.session.commit()

        flash("თქვენი შეკვეთა წარმატებით გაიგზავნა!", "success")
        return redirect(url_for('profile'))  # redirect to profile so it appears in Planned Routes

    return render_template("booking.html", spots=spots)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["   name"]
        email = request.form["email"]
        subject = request.form["subject"]
        message = request.form["message"]

        # TODO: save to DB or send email

        flash("შეტყობინება გაგზავნილია!", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
