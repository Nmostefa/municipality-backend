import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Email, Length, Optional, ValidationError
from email_validator import validate_email, EmailNotValidError
from flask_migrate import Migrate
from datetime import datetime # تأكد من استيراد datetime

# Initialize Flask app
app = Flask(__name__)
# Change this to a strong, random key in production
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_strong_random_secret_key_here_for_production')
# Use SQLite for development (consider for local development only)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
# For production on Render, use PostgreSQL:
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
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

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    budget = db.Column(db.Float, nullable=True)
    contractor = db.Column(db.String(255), nullable=True)
    start_date = db.Column(db.String(10), nullable=True) # YYYY-MM-DD
    end_date = db.Column(db.String(10), nullable=True)   # YYYY-MM-DD
    progress_percentage = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(255), nullable=True)
    
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

class Deliberation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.String(10), nullable=True) # YYYY-MM-DD
    category = db.Column(db.String(100), nullable=True)
    document_url = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    required_documents = db.Column(db.Text, nullable=True)
    steps = db.Column(db.Text, nullable=True)
    fees = db.Column(db.Float, nullable=True)
    working_hours = db.Column(db.String(255), nullable=True)
    
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

class Decision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(100), nullable=True)
    date = db.Column(db.String(10), nullable=True) # YYYY-MM-DD
    document_url = db.Column(db.String(255), nullable=True)
    
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_published = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    author = db.Column(db.String(80), nullable=True)
    announcement_type = db.Column(db.String(50), nullable=True)
    document_url = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    deadline = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        d = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        if 'date_published' in d and isinstance(d['date_published'], datetime):
            d['date_published'] = d['date_published'].isoformat()
        if 'deadline' in d and isinstance(d['deadline'], datetime):
            d['deadline'] = d['deadline'].isoformat()
        return d

class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_name = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}


# --- WTForms Forms ---
class RegistrationForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('password', message='كلمتا المرور غير متطابقتين')])
    submit = SubmitField('تسجيل حساب جديد')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('اسم المستخدم هذا مستخدم بالفعل. الرجاء اختيار اسم آخر.')

    def validate_email(self, email):
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
    def is_accessible(self):
        return current_user.is_authenticated and getattr(current_user, 'is_admin', False)

    def inaccessible_callback(self, name, **kwargs):
        flash('ليس لديك إذن للوصول إلى لوحة الإدارة. الرجاء تسجيل الدخول كمسؤول.', 'danger')
        return redirect(url_for('login', next=request.url))

class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and getattr(current_user, 'is_admin', False)

    def inaccessible_callback(self, name, **kwargs):
        flash('ليس لديك إذن للوصول إلى هذه الصفحة.', 'danger')
        return redirect(url_for('login', next=request.url))

class UserAdminView(AuthenticatedModelView):
    column_list = ('id', 'username', 'email', 'is_admin')
    column_searchable_list = ('username', 'email')
    column_filters = ('is_admin',)

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.set_password(form.password.data)
        elif is_created and not form.password.data:
            raise ValidationError('كلمة المرور مطلوبة للمستخدمين الجدد.')

    def get_create_form(self):
        class CreateUserForm(FlaskForm):
            username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=2, max=20)])
            email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
            password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=6)])
            confirm_password = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('password', message='كلمتا المرور غير متطابقتين')])
            is_admin = BooleanField('مسؤول؟')

            def validate_username(self, username_field):
                user = User.query.filter_by(username=username_field.data).first()
                if user:
                    raise ValidationError('اسم المستخدم هذا مستخدم بالفعل. الرجاء اختيار اسم آخر.')

            def validate_email(self, email_field):
                try:
                    validate_email(email_field.data)
                except EmailNotValidError:
                    raise ValidationError('صيغة البريد الإلكتروني غير صحيحة.')
                user = User.query.filter_by(email=email_field.data).first()
                if user:
                    raise ValidationError('البريد الإلكتروني هذا مستخدم بالفعل. الرجاء اختيار بريد آخر.')
        return CreateUserForm

    def get_edit_form(self):
        class EditUserForm(FlaskForm):
            username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=2, max=20)])
            email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
            password = PasswordField('كلمة المرور (اترك فارغاً لعدم التغيير)', validators=[Optional(), Length(min=6)])
            confirm_password = PasswordField('تأكيد كلمة المرور (اترك فارغاً لعدم التغيير)', validators=[Optional(), EqualTo('password', message='كلمتا المرور غير متطابقتين')])
            is_admin = BooleanField('مسؤول؟')

            def __init__(self, *args, **kwargs):
                super(EditUserForm, self).__init__(*args, **kwargs)
                self.original_obj = kwargs.get('obj') 

            def validate_username(self, username_field):
                if self.original_obj and username_field.data != self.original_obj.username:
                    user = User.query.filter_by(username=username_field.data).first()
                    if user:
                        raise ValidationError('اسم المستخدم هذا مستخدم بالفعل من قبل مستخدم آخر.')

            def validate_email(self, email_field):
                try:
                    validate_email(email_field.data)
                except EmailNotValidError:
                    raise ValidationError('صيغة البريد الإلكتروني غير صحيحة.')
                if self.original_obj and email_field.data != self.original_obj.email:
                    user = User.query.filter_by(email=email_field.data).first()
                    if user:
                        raise ValidationError('البريد الإلكتروني هذا مستخدم بالفعل من قبل مستخدم آخر.')
        return EditUserForm

# --- Flask-Admin Views for other models ---
class ProjectAdminView(AuthenticatedModelView):
    column_list = ('id', 'title', 'status', 'category', 'budget', 'start_date', 'end_date', 'progress_percentage')
    column_searchable_list = ('title', 'description', 'category', 'contractor')
    column_filters = ('status', 'category')
    form_columns = ('title', 'description', 'status', 'category', 'budget', 'contractor', 'start_date', 'end_date', 'progress_percentage', 'image_url')

class DeliberationAdminView(AuthenticatedModelView):
    column_list = ('id', 'title', 'date', 'category')
    column_searchable_list = ('title', 'description', 'category')
    column_filters = ('category',)
    form_columns = ('title', 'description', 'date', 'category', 'document_url', 'image_url')

class ServiceAdminView(AuthenticatedModelView):
    column_list = ('id', 'name', 'description', 'working_hours', 'fees')
    column_searchable_list = ('name', 'description')
    form_columns = ('name', 'description', 'required_documents', 'steps', 'fees', 'working_hours')

class DecisionAdminView(AuthenticatedModelView):
    column_list = ('id', 'title', 'type', 'date')
    column_searchable_list = ('title', 'type')
    column_filters = ('type',)
    form_columns = ('title', 'type', 'date', 'document_url')

class AnnouncementAdminView(AuthenticatedModelView):
    column_list = ('id', 'title', 'date_published', 'announcement_type', 'deadline')
    column_searchable_list = ('title', 'content', 'announcement_type', 'author')
    column_filters = ('announcement_type',)
    form_columns = ('title', 'content', 'date_published', 'author', 'announcement_type', 'document_url', 'image_url', 'deadline')

class SiteSettingAdminView(AuthenticatedModelView):
    column_list = ('id', 'setting_name', 'setting_value')
    column_searchable_list = ('setting_name',)
    form_columns = ('setting_name', 'setting_value')

class DepartmentAdminView(AuthenticatedModelView):
    column_list = ('id', 'name', 'description')
    column_searchable_list = ('name',)
    form_columns = ('name', 'description')

# Initialize Flask-Admin
admin = Admin(app, name='لوحة تحكم بلدية ديرة', template_mode='bootstrap3', index_view=MyAdminIndexView())

# Add Flask-Admin views
admin.add_view(UserAdminView(User, db.session, name='المستخدمون'))
admin.add_view(ProjectAdminView(Project, db.session, name='المشاريع'))
admin.add_view(DeliberationAdminView(Deliberation, db.session, name='المداولات'))
admin.add_view(ServiceAdminView(Service, db.session, name='الخدمات'))
admin.add_view(DecisionAdminView(Decision, db.session, name='القرارات'))
admin.add_view(AnnouncementAdminView(Announcement, db.session, name='الإعلانات'))
admin.add_view(SiteSettingAdminView(SiteSetting, db.session, name='إعدادات الموقع'))
admin.add_view(DepartmentAdminView(Department, db.session, name='الأقسام'))


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
    port = int(os.environ.get('PORT', 5000)) # Get port from environment variable or use 5000
    app.run(host='0.0.0.0', port=port, debug=True) # Make the app listen on all interfaces
