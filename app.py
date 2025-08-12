import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from datetime import datetime
import json
from enum import Enum

# Initialize Flask App
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_super_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Models ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='citizen') # citizen, employee, admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"

class RequestStatus(Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=True)
    status = db.Column(db.Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('requests', lazy=True))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"Request('{self.title}', '{self.status}', 'by {self.user.username}')"

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Notification for user {self.user_id}: {self.message}"

# --- Forms ---
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RequestForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('Roads', 'Roads'),
        ('Waste Management', 'Waste Management'),
        ('Public Lighting', 'Public Lighting'),
        ('Parks & Green Spaces', 'Parks & Green Spaces'),
        ('Water & Sanitation', 'Water & Sanitation'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    submit = SubmitField('Submit Request')

# This is the UserForm that needed to be defined earlier
class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[
        ('citizen', 'Citizen'),
        ('employee', 'Employee'),
        ('admin', 'Admin')
    ], validators=[DataRequired()])
    password = PasswordField('New Password (leave blank to keep current)')
    submit = SubmitField('Update User')

    def validate_username(self, username):
        if self.username.data != self.original_username and User.query.filter_by(username=username.data).first():
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if self.email.data != self.original_email and User.query.filter_by(email=email.data).first():
            raise ValidationError('That email is taken. Please choose a different one.')

# --- Admin Views ---
class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return redirect(url_for('login'))
        return self.render('admin/index.html')

class UserAdminView(AuthenticatedModelView):
    column_list = ('username', 'email', 'role')
    column_searchable_list = ('username', 'email')
    column_filters = ('role',)
    form = UserForm # This line was causing the NameError

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.set_password(form.password.data)
        else:
            # Preserve existing password if not updated
            if not is_created:
                original_user = User.query.get(model.id)
                model.password_hash = original_user.password_hash
        return super().on_model_change(form, model, is_created)

    def get_form(self):
        form = super().get_form()
        # Store original username and email for validation during updates
        if form.model: # If editing an existing user
            form.original_username = form.model.username
            form.original_email = form.model.email
        return form

class RequestAdminView(AuthenticatedModelView):
    column_list = ('title', 'description', 'category', 'status', 'user', 'created_at', 'updated_at')
    column_searchable_list = ('title', 'description', 'category')
    column_filters = ('status', 'category', 'user.username')
    column_editable_list = ('status',) # Allow direct editing of status

    # Customize form for creating/editing requests in admin panel
    form_args = {
        'status': {
            'choices': [(status.name, status.value) for status in RequestStatus]
        }
    }

class NotificationAdminView(AuthenticatedModelView):
    column_list = ('user', 'message', 'is_read', 'created_at')
    column_searchable_list = ('message',)
    column_filters = ('is_read', 'user.username')

# Initialize Flask-Admin
admin = Admin(app, name='Municipality Dashboard', template_mode='bootstrap3', index_view=MyAdminIndexView())

# Add views to Admin
admin.add_view(UserAdminView(User, db.session))
admin.add_view(RequestAdminView(Request, db.session))
admin.add_view(NotificationAdminView(Notification, db.session))

# --- Routes ---
@app.route('/')
@app.route('/home')
def home():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.index'))
        elif current_user.role == 'employee':
            return redirect(url_for('employee_dashboard'))
        else: # citizen
            return redirect(url_for('citizen_dashboard'))
    return render_template('index.html', title='Welcome')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        # Instead of flash, return a message to the frontend or handle it with JavaScript
        return jsonify(message='Account created successfully! You can now log in.')
    # For GET request or validation failure, render the form
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            # Instead of flash, return error message
            return jsonify(error='Login Unsuccessful. Please check email and password'), 401
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/citizen_dashboard')
@login_required
def citizen_dashboard():
    if current_user.role != 'citizen':
        return redirect(url_for('home'))
    requests = Request.query.filter_by(user_id=current_user.id).order_by(Request.created_at.desc()).all()
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    return render_template('citizen_dashboard.html', requests=requests, notifications=notifications)

@app.route('/employee_dashboard')
@login_required
def employee_dashboard():
    if current_user.role != 'employee':
        return redirect(url_for('home'))
    # Employees can see all requests or requests assigned to them
    all_requests = Request.query.order_by(Request.created_at.desc()).all()
    return render_template('employee_dashboard.html', requests=all_requests)

@app.route('/requests/new', methods=['GET', 'POST'])
@login_required
def new_request():
    if current_user.role != 'citizen':
        return redirect(url_for('home'))
    form = RequestForm()
    if form.validate_on_submit():
        request_obj = Request(title=form.title.data,
                              description=form.description.data,
                              category=form.category.data,
                              user_id=current_user.id)
        db.session.add(request_obj)
        db.session.commit()
        return jsonify(message='Your request has been created!')
    return render_template('create_request.html', title='New Request', form=form)

@app.route('/requests/<int:request_id>')
@login_required
def view_request(request_id):
    request_obj = Request.query.get_or_404(request_id)
    if request_obj.user_id != current_user.id and current_user.role == 'citizen':
        return jsonify(error='You are not authorized to view this request'), 403
    return render_template('view_request.html', request=request_obj)

@app.route('/notifications')
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    return jsonify([{'id': n.id, 'message': n.message, 'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S')} for n in notifications])

@app.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        return jsonify(error='Not authorized'), 403
    notification.is_read = True
    db.session.commit()
    return jsonify(message='Notification marked as read')

@app.route('/update_request_status/<int:request_id>', methods=['POST'])
@login_required
def update_request_status(request_id):
    if current_user.role not in ['employee', 'admin']:
        return jsonify(error='Unauthorized'), 403

    request_obj = Request.query.get_or_404(request_id)
    new_status_str = request.json.get('status')

    if not new_status_str:
        return jsonify(error='Status not provided'), 400

    try:
        new_status = RequestStatus[new_status_str.upper()]
        request_obj.status = new_status
        db.session.commit()

        # Create a notification for the user who made the request
        notification_message = f"Your request '{request_obj.title}' has been updated to status: {new_status.value}."
        notification = Notification(user_id=request_obj.user_id, message=notification_message)
        db.session.add(notification)
        db.session.commit()

        return jsonify(message=f"Request {request_id} status updated to {new_status.value}")
    except KeyError:
        return jsonify(error='Invalid status value'), 400
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'An error occurred: {str(e)}'), 500


# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Create database tables if they don't exist
# This should ideally be handled by migrations in a production environment
# but for simple setups, it can be useful.
@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    # Ensure database tables are created before running the app
    # In a production environment, you would run migrations separately
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
