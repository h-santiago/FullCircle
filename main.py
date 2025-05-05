from flask import Flask, jsonify, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Consumer, Retailer, Organization, FoodItem
from geopy.geocoders import Nominatim

app = Flask("__name__")

# adding configuration for using a sqlite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'secret_key_here'  # Make sure this is kept secret in production


db.init_app(app)
with app.app_context():
    db.create_all()

# Create route for index.html
@app.route("/")
def index():
    return render_template('index.html')

# function to show login page
@app.route("/login_page")
def login():
    return render_template('login.html')

#function to log user in
@app.route("/login_user", methods=["GET", "POST"])
def login_user():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        login = User.query.filter_by(email=email, password=password).first()
        

        

        # check user exists
        if login is not None:
            # set session variable
            session['user_id'] = login.id
            #check role of user to redirect to correct dashboard
            if login.role.lower() == "consumer":
                return redirect(url_for("consumer_dashboard"))
            elif login.role.lower() == "retailer":
                return redirect(url_for("retail_dashboard"))
            elif login.role.lower() == "ngo":
                return(redirect("ngo_dashboard"))
    return render_template("login.html")

# function and route for register page
@app.route("/register")
def register():
    return render_template('registration.html')

# return lat and long from address
def get_coordinates(address):
    geolocator = Nominatim(user_agent="geo_app")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None, None

#function to create a new user account
@app.route("/create_user", methods=["POST"])
def create_user():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')

    street = request.form.get('street')
    city = request.form.get('city')
    province = request.form.get('province')
    postal_code = request.form.get('postal_code')

    country = "Canada"

    full_address = f"{street}, {city}, {province}, {postal_code}, {country}"
    lat, long = get_coordinates(full_address)


    # create new user from values entered
    new_user = User(
        name=name,
        email=email, 
        password=password, 
        role=role,
        street=street,
        city=city,
        province=province,
        postal_code=postal_code,
        latitude=lat, 
        longitude=long
    )

    if new_user is not None:
        db.session.add(new_user)
        db.session.commit()

        # Depending on the role, create the corresponding entry in the related table
        if role == "Consumer":
            new_consumer = Consumer(user_id=new_user.id)
            db.session.add(new_consumer)
        
        elif role == "Retailer":
            new_retailer = Retailer(user_id=new_user.id)
            db.session.add(new_retailer)
        
        elif role == "NGO":
            org_type = request.form.get('org_type')
            # lat = lat   
            # long = long
            new_organization = Organization(user_id=new_user.id, org_type=org_type)
            print(lat, long)
            db.session.add(new_organization)

        # Commit all changes to the database
        db.session.commit()

        return redirect("/login_page")
    else:
        print("User is none")
        return redirect("/register")

# create endpoint for organization lat and long
@app.route("/api/organizations")
def get_organizations():
    organizations = Organization.query.all()
    org_list = [
        {
            "name": org.user.name,  # Fetch organization name from the User table
            "type": org.org_type,   # Fetch organization type (food bank, shelter, etc.)
            "latitude": org.user.latitude,  # Fetch latitude from User model
            "longitude": org.user.longitude  # Fetch longitude from User model
        }
        for org in organizations
    ]
    
    return jsonify(org_list)

@app.route('/api/retailer', methods=['GET'])
def get_retailers():
    retailers = Retailer.query.join(User, Retailer.user_id == User.id).all()
    retailer_list = []

    for retailer in retailers:
        retailer_data = {
            "name": retailer.user.name,  # Assuming User has a name field
            "location": retailer.user.address,  # Assuming User has an address field
            "foodItems": [{"name": item.name, "quantity": item.quantity} for item in retailer.food_items],
            # "postedAt": "2025-03-15"  # Static date; you may replace it with an actual timestamp if available
        }
        retailer_list.append(retailer_data)

    return jsonify(retailer_list)

@app.route("/api/user/location")
def get_user_location():
    user_id = session.get('user_id')
    if user_id is None:
        return jsonify({"error": "User not logged in"}), 401

    user = User.query.get(user_id)
    if user:
        return jsonify({
            "latitude": user.latitude,  # ✅ Include latitude
            "longitude": user.longitude,  # ✅ Include longitude
            "street": user.street,
            "city": user.city,
            "province": user.province,
            "postal_code": user.postal_code
        })
    return jsonify({"error": "User not found"}), 404


@app.route("/consumer_dashboard")
def consumer_dashboard():
    # Get user_id from session
    user_id = session.get('user_id')

    if user_id is None:
        # If no user is logged in, redirect to login page
        return redirect(url_for('login'))

    # If user is logged in, fetch their information (you can also perform database queries here)
    user = User.query.get(user_id)
    
    return render_template('consumer_dashboard.html', user=user)

@app.route("/consumer_ngo_map")
def consumer_ngo_map():
    return render_template('consumer_ngo_map.html')

@app.route("/consumer_retailer_list")
def consumer_retailer_list():
    # Get all retailers with their food items
    retailers = Retailer.query.all()
    formatted_retailers = []

    for retailer in retailers:
        # Get associated user data
        user = User.query.get(retailer.user_id)
        # Get food items for this retailer
        food_items = FoodItem.query.filter_by(retailer_id=retailer.id).all()
        
        retailer_dict = {
            'name': user.name if user else 'Unknown',
            'address': f"{user.street}, {user.city}, {user.province}" if user else 'No address',
            'items': []
        }
        
        # Add each food item to the retailer's items list
        for item in food_items:
            retailer_dict['items'].append({
                'name': item.name,
                'quantity': item.quantity
            })
        
        formatted_retailers.append(retailer_dict)

    return render_template('consumer_retailer_list.html', retailers=formatted_retailers)

@app.route("/ngo_dashboard")
def ngo_dashboard():
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for("login"))  # Redirect if user is not logged in

    user = User.query.get(user_id)
    organization = Organization.query.filter_by(user_id=user_id).first()

    return render_template("ngo_dashboard.html", user=user, organization=organization)


# show the retail dashboard
@app.route("/retail_dashboard")
def retail_dashboard():
    return render_template('retail_dashboard.html')

# show the add item page
@app.route("/add_item", methods=['GET', 'POST'])
def add_item():
    return render_template('add_item.html')

# insert an item as a retailer
@app.route("/insert_item", methods=["POST"])
def insert_item():
    # Ensure the user is logged in and has a retailer role
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('login'))

    retailer = Retailer.query.filter_by(user_id=user_id).first()
    
    if request.method == 'POST':
        item_name = request.form.get('item_name')
        quantity = request.form.get('quantity')

        if retailer:
            # Create a new food item and add it to the retailer's food items
            new_food_item = FoodItem(name=item_name, quantity=quantity, retailer_id=retailer.id)
            db.session.add(new_food_item)
            db.session.commit()

        return redirect(url_for('retail_dashboard'))

# @app.route("/remove_items", methods=['GET', 'POST'])
# def remove_items():
#     return render_template('remove_item.html')

@app.route("/delete_item", methods=["POST"])
def delete_item():
    if request.method == 'POST':
        item_id = request.form.get('item_id')  # Get the selected item's ID
        
        # Ensure the user is logged in and has a retailer role
        user_id = session.get('user_id')
        if user_id is None:
            return redirect(url_for('login'))

        retailer = Retailer.query.filter_by(user_id=user_id).first()
        
        if retailer:
            # Find the food item by id and retailer id
            food_item = FoodItem.query.filter_by(id=item_id, retailer_id=retailer.id).first()
            
            if food_item:
                # Delete the item from the database
                db.session.delete(food_item)
                db.session.commit()
                return redirect(url_for('view_items'))  # Redirect to the items page after successful deletion
            else:
                # Handle case if item doesn't exist
                return "Item not found!", 404

        return "Retailer not found!", 404
    
@app.route("/remove_item", methods=['GET', 'POST'])
def remove_item():
    # Ensure the user is logged in and has a retailer role
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('login'))

    retailer = Retailer.query.filter_by(user_id=user_id).first()
    
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        
        if retailer:
            # Find the food item by id and retailer id
            food_item = FoodItem.query.filter_by(id=item_id, retailer_id=retailer.id).first()
            
            if food_item:
                # Delete the item from the database
                db.session.delete(food_item)
                db.session.commit()
                return redirect(url_for('remove_item'))  # Redirect to the items page after successful deletion
            else:
                return "Item not found!", 404
        return "Retailer not found!", 404
    
    # GET request - display the remove item page with current items
    if retailer:
        items = FoodItem.query.filter_by(retailer_id=retailer.id).all()
    else:
        items = []
    
    return render_template('remove_item.html', items=items)


@app.route("/view_items")
def view_items():
    # Ensure the user is logged in and has a retailer role
    user_id = session.get('user_id')
    print("USER ID IS",  user_id)
    if user_id is None:
        return redirect(url_for('login'))

    retailer = Retailer.query.filter_by(user_id=user_id).first()
    print(retailer)

    if retailer:
        # Fetch all food items for the retailer
        items = FoodItem.query.filter_by(retailer_id=retailer.id).all()
    else:
        items = []

    return render_template('view_items.html', items=items)


if __name__ == '__main__':
    app.run(debug=True)