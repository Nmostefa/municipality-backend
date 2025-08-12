import os # أضف هذا السطر
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, EqualTo, Email, Length, Optional, ValidationError
from email_validator import validate_email, EmailNotValidError
from flask_migrate import Migrate

# Initialize Flask app
app = Flask(__name__)
# Change this to a strong, random key in production
app.config['SECRET_KEY'] = 'your_strong_random_secret_key_here_for_production'
# Use SQLite for development
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
# For production on Render, use PostgreSQL:
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://your_user:your_password@your_host:your_port/your_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db) # Initialize Flask-Migrate

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Set the login view

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id)) # Use db.session.get for SQLAlchemy 1.4+

# --- Database Models ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        """Hashes the password and stores it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        """String representation of the User object."""
        return f"User('{self.username}', '{self.email}')"

# --- WTForms Forms ---
class RegistrationForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('password', message='كلمتا المرور غير متطابقتين')])
    submit = SubmitField('تسجيل حساب جديد')

    def validate_username(self, username):
        """Validates if the username is already taken."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('اسم المستخدم هذا مستخدم بالفعل. الرجاء اختيار اسم آخر.')

    def validate_email(self, email):
        """Validates if the email is already taken and is a valid email format."""
        try:
            validate_email(email.data)
        except EmailNotValidError:
            raise ValidationError('صيغة البريد الإلكتروني غير صحيحة.')
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('البريد الإلكتروني هذا مستخدم بالفعل. الرجاء اختيار بريد آخر.')

class LoginForm(FlaskForm):
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    remember = BooleanField('تذكرني')
    submit = SubmitField('تسجيل الدخول')

# --- Flask-Admin Custom Views ---
class MyAdminIndexView(AdminIndexView):
    """Custom Admin index view to check for admin access."""
    def is_accessible(self):
        """Checks if the current user is authenticated and is an admin."""
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        """Redirects to login page if user doesn't have admin access."""
        flash('ليس لديك إذن للوصول إلى لوحة الإدارة. الرجاء تسجيل الدخول كمسؤول.', 'danger')
        return redirect(url_for('login', next=request.url))

class UserAdminView(ModelView):
    """Custom ModelView for the User model in Flask-Admin."""
    column_list = ('id', 'username', 'email', 'is_admin')
    column_searchable_list = ('username', 'email')
    column_filters = ('is_admin',)
    # form_columns will be dynamically set by get_create_form/get_edit_form
    # Password field will be handled by on_model_change

    def on_model_change(self, form, model, is_created):
        """Hashes the password before saving the user to the database."""
        # Only hash password if it's provided in the form, and it's not empty
        # For edit, if password field is Optional and left blank, form.password.data will be None
        if form.password.data:
            model.set_password(form.password.data)
        # If it's a new user being created and no password was provided (should be caught by form validation)
        elif is_created and not form.password.data:
            raise ValidationError('كلمة المرور مطلوبة للمستخدمين الجدد.')


    def get_create_form(self):
        """Returns the form class to be used when creating a new user."""
        class CreateUserForm(FlaskForm):
            username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=2, max=20)])
            email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
            password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=6)])
            confirm_password = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('password', message='كلمتا المرور غير متطابقتين')])
            is_admin = BooleanField('مسؤول؟')

            def validate_username(self, username_field):
                """Validates uniqueness of username for new users."""
                user = User.query.filter_by(username=username_field.data).first()
                if user:
                    raise ValidationError('اسم المستخدم هذا مستخدم بالفعل. الرجاء اختيار اسم آخر.')

            def validate_email(self, email_field):
                """Validates uniqueness and format of email for new users."""
                try:
                    validate_email(email_field.data)
                except EmailNotValidError:
                    raise ValidationError('صيغة البريد الإلكتروني غير صحيحة.')
                user = User.query.filter_by(email=email_field.data).first()
                if user:
                    raise ValidationError('البريد الإلكتروني هذا مستخدم بالفعل. الرجاء اختيار بريد آخر.')
        return CreateUserForm

    def get_edit_form(self):
        """Returns the form class to be used when editing an existing user."""
        class EditUserForm(FlaskForm):
            username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=2, max=20)])
            email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
            # Password and confirm_password are optional on edit
            password = PasswordField('كلمة المرور (اترك فارغاً لعدم التغيير)', validators=[Optional(), Length(min=6)])
            confirm_password = PasswordField('تأكيد كلمة المرور (اترك فارغاً لعدم التغيير)', validators=[Optional(), EqualTo('password', message='كلمتا المرور غير متطابقتين')])
            is_admin = BooleanField('مسؤول؟')

            def __init__(self, *args, **kwargs):
                super(EditUserForm, self).__init__(*args, **kwargs)
                # Store the original model instance if available
                self.original_obj = kwargs.get('obj') # This is the key line to get the current object

            def validate_username(self, username_field):
                """Validates uniqueness of username for existing users (allows current user's username)."""
                if self.original_obj and username_field.data != self.original_obj.username:
                    user = User.query.filter_by(username=username_field.data).first()
                    if user:
                        raise ValidationError('اسم المستخدم هذا مستخدم بالفعل من قبل مستخدم آخر.')

            def validate_email(self, email_field):
                """Validates uniqueness and format of email for existing users (allows current user's email)."""
                try:
                    validate_email(email_field.data)
                except EmailNotValidError:
                    raise ValidationError('صيغة البريد الإلكتروني غير صحيحة.')
                if self.original_obj and email_field.data != self.original_obj.email:
                    user = User.query.filter_by(email=email_field.data).first()
                    if user:
                        raise ValidationError('البريد الإلكتروني هذا مستخدم بالفعل من قبل مستخدم آخر.')

        return EditUserForm


    def is_accessible(self):
        """Checks if the current user is authenticated and is an admin for this view."""
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        """Redirects to login if not accessible."""
        flash('ليس لديك إذن للوصول إلى هذه الصفحة.', 'danger')
        return redirect(url_for('login', next=request.url))

# Initialize Flask-Admin
admin = Admin(app, name='لوحة تحكم بلدية ديرة', template_mode='bootstrap3', index_view=MyAdminIndexView())

# Add Flask-Admin views
admin.add_view(UserAdminView(User, db.session))

# --- Routes ---
@app.route("/")
@app.route("/home")
def home():
    """Renders the home page."""
    return render_template('home.html', title='الرئيسية')

@app.route("/register", methods=['GET', 'POST'])
def register():
    """Handles user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('تم إنشاء حسابك بنجاح! يمكنك الآن تسجيل الدخول.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='تسجيل حساب جديد', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(next_page or url_for('home'))
        else:
            flash('فشل تسجيل الدخول. الرجاء التحقق من البريد الإلكتروني وكلمة المرور.', 'danger')
    return render_template('login.html', title='تسجيل الدخول', form=form)

@app.route("/logout")
@login_required
def logout():
    """Logs out the current user."""
    logout_user()
    return redirect(url_for('home'))

@app.route("/dashboard")
@login_required
def dashboard():
    """Renders the user dashboard (requires login)."""
    return render_template('dashboard.html', title='لوحة التحكم')

# --- Main execution ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Creates tables based on models
        # Create a default admin user if one doesn't exist for initial setup
        if not User.query.filter_by(is_admin=True).first():
            print("Creating default admin user: admin@example.com / adminpass")
            admin_user = User(username='admin', email='admin@example.com', is_admin=True)
            admin_user.set_password('adminpass')
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created.")
    port = int(os.environ.get('PORT', 5000)) # احصل على المنفذ من متغير البيئة أو استخدم 5000
    app.run(host='0.0.0.0', port=port, debug=True) # اجعل التطبيق يستمع على جميع الواجهات
