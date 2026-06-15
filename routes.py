from flask import render_template, request, redirect, url_for, session, flash
from app import app
from models import db, User, Trek, Booking
from datetime import datetime

# --- Helper Session Guard for Role-Based Access Control ---
def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# --- AUTHENTICATION ROUTES ---
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            if user.role == 'staff' and user.status != 'approved':
                flash('Your account has not been approved by Admin yet.', 'danger')
                return redirect(url_for('login'))
            if user.status == 'blacklisted':
                flash('Your account has been deactivated/blacklisted by the Administrator.', 'danger')
                return redirect(url_for('login'))
            
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            if user.role == 'admin': return redirect(url_for('admin_dashboard'))
            elif user.role == 'staff': return redirect(url_for('staff_dashboard'))
            else: return redirect(url_for('user_dashboard'))
        
        flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        contact = request.form.get('contact')
        role = request.form.get('role')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))
        
        status = 'pending' if role == 'staff' else 'active'
        new_user = User(username=username, password=password, name=name, contact_details=contact, role=role, status=status)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Staff accounts require admin approval before login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- ADMIN ROUTES ---
@app.route('/admin/dashboard')
def admin_dashboard():
    user = get_current_user()
    if not user or user.role != 'admin': return redirect(url_for('login'))
    
    search_query = request.args.get('search', '')
    
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()
    
    if search_query:
        treks_list = Trek.query.filter(Trek.trek_name.contains(search_query) | Trek.id.contains(search_query)).all()
        staff_list = User.query.filter(User.role == 'staff', (User.name.contains(search_query) | User.id.contains(search_query))).all()
        users_list = User.query.filter(User.role == 'user', (User.name.contains(search_query) | User.id.contains(search_query))).all()
    else:
        treks_list = Trek.query.all()  # Fetches ALL treks, including Completed/Closed
        staff_list = User.query.filter_by(role='staff').all()
        users_list = User.query.filter_by(role='user').all()
        
    bookings_list = Booking.query.all()  # Admin can view ALL global bookings
    
    return render_template('admin_dash.html', total_treks=total_treks, total_users=total_users, 
                           total_staff=total_staff, total_bookings=total_bookings, treks=treks_list, 
                           staff=staff_list, users=users_list, bookings=bookings_list)

@app.route('/admin/trek/add', methods=['POST'])
def add_trek():
    user = get_current_user()
    if not user or user.role != 'admin': return redirect(url_for('login'))
    
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
    slots = int(request.form.get('slots'))
    
    new_trek = Trek(
        trek_name=request.form.get('trek_name'),
        location=request.form.get('location'),
        difficulty=request.form.get('difficulty'),
        duration=int(request.form.get('duration')),
        total_slots=slots,
        available_slots=slots,
        start_date=start_date,
        end_date=end_date,
        status='Pending'
    )
    db.session.add(new_trek)
    db.session.commit()
    flash('New trek route entry generated successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/trek/delete/<int:trek_id>')
def delete_trek(trek_id):
    user = get_current_user()
    if not user or user.role != 'admin': return redirect(url_for('login'))
    
    trek = Trek.query.get_or_404(trek_id)
    Booking.query.filter_by(trek_id=trek_id).delete()
    db.session.delete(trek)
    db.session.commit()
    flash('Trek route entry removed from system registry.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/status/<int:uid>/<string:action>')
def change_user_status(uid, action):
    user = get_current_user()
    if not user or user.role != 'admin': return redirect(url_for('login'))
    
    target_user = User.query.get_or_404(uid)
    if action == 'approve': target_user.status = 'approved'
    elif action == 'blacklist': target_user.status = 'blacklisted'
    elif action == 'activate': target_user.status = 'active'
    
    db.session.commit()
    flash(f"User access authorization updated to: {target_user.status}.", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/assign_staff/<int:trek_id>', methods=['POST'])
def assign_staff(trek_id):
    user = get_current_user()
    if not user or user.role != 'admin': return redirect(url_for('login'))
    
    trek = Trek.query.get_or_404(trek_id)
    staff_id = request.form.get('staff_id')
    
    trek.assigned_staff_id = int(staff_id) if staff_id else None
    db.session.commit()
    flash('Personnel assignments modified successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

# --- TREK STAFF ROUTES ---
@app.route('/staff/dashboard')
def staff_dashboard():
    user = get_current_user()
    if not user or user.role != 'staff': return redirect(url_for('login'))
    
    assigned_treks = Trek.query.filter_by(assigned_staff_id=user.id).all()
    return render_template('staff_dash.html', treks=assigned_treks)

@app.route('/staff/trek/update/<int:trek_id>', methods=['POST'])
def update_trek(trek_id):
    user = get_current_user()
    if not user or user.role != 'staff': return redirect(url_for('login'))
    
    trek = Trek.query.get_or_404(trek_id)
    if trek.assigned_staff_id != user.id:
        flash("Unauthorized modification window denied.", "danger")
        return redirect(url_for('staff_dashboard'))
        
    trek.status = request.form.get('status')
    trek.available_slots = int(request.form.get('available_slots'))
    
    # Cascade status change to bookings if staff completes the trek
    if trek.status == 'Completed':
        bookings = Booking.query.filter_by(trek_id=trek.id, status='Booked').all()
        for b in bookings:
            b.status = 'Completed'
            
    db.session.commit()
    flash('Trek metrics and participant status logs adjusted.', 'success')
    return redirect(url_for('staff_dashboard'))

# --- USER/TREKKER ROUTES ---
@app.route('/user/dashboard')
def user_dashboard():
    user = get_current_user()
    if not user or user.role != 'user': return redirect(url_for('login'))
    
    difficulty_filter = request.args.get('difficulty', '')
    location_filter = request.args.get('location', '')
    search_filter = request.args.get('search_name', '')
    
    query = Trek.query.filter_by(status='Open')
    if difficulty_filter:
        query = query.filter_by(difficulty=difficulty_filter)
    if location_filter:
        query = query.filter(Trek.location.contains(location_filter))
    if search_filter:
        query = query.filter(Trek.trek_name.contains(search_filter))
        
    available_treks = query.all()
    my_bookings = Booking.query.filter_by(user_id=user.id).all()
    
    return render_template('user_dash.html', treks=available_treks, bookings=my_bookings, user_profile=user)

@app.route('/user/profile/edit', methods=['POST'])
def edit_profile():
    user = get_current_user()
    if not user or user.role != 'user': return redirect(url_for('login'))
    
    user.name = request.form.get('name')
    user.contact_details = request.form.get('contact')
    db.session.commit()
    flash('Your profile changes have been saved.', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/user/book/<int:trek_id>', methods=['POST'])
def book_trek(trek_id):
    user = get_current_user()
    if not user or user.role != 'user': return redirect(url_for('login'))
    
    trek = Trek.query.get_or_404(trek_id)
    
    already_booked = Booking.query.filter_by(user_id=user.id, trek_id=trek.id, status='Booked').first()
    if already_booked:
        flash('You have already secured a reservation for this trek route.', 'warning')
        return redirect(url_for('user_dashboard'))
        
    if trek.status != 'Open':
        flash('Booking rejected: This trek route is currently not open.', 'danger')
    elif trek.available_slots <= 0:
        flash('Booking rejected: No slots remaining! Overbooking prevented.', 'danger')
    else:
        trek.available_slots -= 1
        new_booking = Booking(user_id=user.id, trek_id=trek.id, status='Booked')
        db.session.add(new_booking)
        db.session.commit()
        flash('Trek reservation confirmed!', 'success')
        
    return redirect(url_for('user_dashboard'))