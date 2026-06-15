import os
from flask import Flask
from models import db, User

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'trek_management_secret_pass_123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()
        admin_exists = User.query.filter_by(role='admin').first()
        if not admin_exists:
            admin_user = User(
                username='admin',
                password='adminpassword',
                role='admin',
                name='System Administrator',
                status='active'
            )
            db.session.add(admin_user)
            db.session.commit()
            print(">>> Database initialized and Admin seeded.")
    return app

app = create_app()

# ---- DO NOT MOVE THIS ----
# This MUST be placed out here after 'app = create_app()' 
# so that routes.py can bind its @app.route decorators to the app instance!
from routes import *

if __name__ == '__main__':
    app.run(debug=True)