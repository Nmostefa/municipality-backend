from flask import Flask, jsonify, request, redirect, url_for, flash, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import date, datetime

# استيرادات Flask-Admin
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

# استيرادات Flask-Login و Werkzeug.security
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# استيرادات WTForms و Flask-WTF (مطلوبة لنموذج المستخدم والإعدادات)
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Optional

app = Flask(__name__)

# --- تهيئة CORS للسماح للواجهة الأمامية بالوصول ---
# تأكد من أن هذا يطابق نطاق Netlify الخاص بك
CORS(app, resources={r"/api/*": {"origins": ["https://apcdirah-dz.netlify.app", "http://localhost:5173"]}})
# --------------------------------------------------

# إعداد قاعدة البيانات PostgreSQL من متغير البيئة
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# إعداد المفتاح السري لـ Flask-Admin و Flask-Login من متغير البيئة
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_super_secret_key_that_you_must_change_now_12345') # غير هذا!

db = SQLAlchemy(app)

# --- تهيئة Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # اسم الـ view لصفحة تسجيل الدخول
login_manager.login_message = "الرجاء تسجيل الدخول للوصول إلى لوحة التحكم."
login_manager.login_message_category = "info"

# --- تعريف نماذج قاعدة البيانات (كما هي لديك) ---
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    budget = db.Column(db.Float, nullable=True)
    contractor = db.Column(db.String(255), nullable=True)
    start_date = db.Column(db.String(10), nullable=True)
    end_date = db.Column(db.String(10), nullable=True)
    progress_percentage = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(255), nullable=True)
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

class Deliberation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.String(10), nullable=True)
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
    date = db.Column(db.String(10), nullable=True)
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

# --- تعريف نموذج المستخدم (User Model) لـ Flask-Login ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# ------------------------------------------------------

# --- فئة مخصصة لـ ModelView تتطلب تسجيل الدخول ---
class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        flash('الرجاء تسجيل الدخول للوصول إلى لوحة التحكم.', 'warning')
        return redirect(url_for('login', next=request.url))

# --- فئة مخصصة لـ User ModelView لمعالجة كلمة المرور ---
class UserAdminView(AuthenticatedModelView):
    # 📌 التعديل هنا: تحديد النموذج المخصص كـ 'form' attribute للكلاس
    form = UserForm 
    
    column_exclude_list = ['password_hash']
    # 'password' و 'confirm_password' يتم التعامل معهما عبر UserForm
    form_columns = ['username', 'password', 'confirm_password'] 

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.set_password(form.password.data)
        return super().on_model_change(form, model, is_created)

# --- تعريف نموذج WTForms مخصص للمستخدمين ---
class UserForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired()])
    password = PasswordField('كلمة المرور الجديدة', validators=[Optional()])
    confirm_password = PasswordField('تأكيد كلمة المرور الجديدة', validators=[
        Optional(),
        EqualTo('password', message='كلمتا المرور غير متطابقتين')
    ])

# --- تعريف نموذج WTForms مخصص لإعدادات الموقع ---
class SiteSettingForm(FlaskForm):
    setting_name = StringField('اسم الإعداد', validators=[DataRequired()])
    setting_value = TextAreaField('قيمة الإعداد', validators=[Optional()])

# --- فئة مخصصة لـ SiteSetting ModelView ---
class SiteSettingAdminView(AuthenticatedModelView):
    form = SiteSettingForm

# --- تهيئة Flask-Admin وإضافة النماذج ---
admin = Admin(app, name='لوحة تحكم بلدية ديرة', template_mode='bootstrap3', url='/admin')

admin.add_view(AuthenticatedModelView(Department, db.session, name='الأقسام'))
admin.add_view(AuthenticatedModelView(Project, db.session, name='المشاريع'))
admin.add_view(AuthenticatedModelView(Announcement, db.session, name='الإعلانات'))
admin.add_view(AuthenticatedModelView(Deliberation, db.session, name='المداولات'))
admin.add_view(AuthenticatedModelView(Decision, db.session, name='القرارات'))
admin.add_view(SiteSettingAdminView(SiteSetting, db.session, name='إعدادات الموقع'))
admin.add_view(AuthenticatedModelView(Service, db.session, name='الخدمات'))
# 📌 التعديل هنا: تم حذف الوسيط 'form=UserForm'
admin.add_view(UserAdminView(User, db.session, name='المستخدمون')) 

# --- تعريف الـ APIs ---
@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify([project.to_dict() for project in projects])

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict())

@app.route('/api/departments', methods=['GET'])
def get_departments():
    departments = Department.query.all()
    return jsonify([department.to_dict() for department in departments])

@app.route('/api/announcements', methods=['GET'])
def get_announcements():
    announcements = Announcement.query.order_by(Announcement.date_published.desc()).all()
    return jsonify([announcement.to_dict() for announcement in announcements])

@app.route('/api/deliberations', methods=['GET'])
def get_deliberations():
    deliberations = Deliberation.query.order_by(Deliberation.date.desc()).all()
    return jsonify([deliberation.to_dict() for deliberation in deliberations])

@app.route('/api/decisions', methods=['GET'])
def get_decisions():
    decisions = Decision.query.order_by(Decision.date.desc()).all()
    return jsonify([decision.to_dict() for decision in decisions])

@app.route('/api/services', methods=['GET'])
def get_services():
    services = Service.query.all()
    return jsonify([service.to_dict() for service in services])

@app.route('/api/settings', methods=['GET'])
def get_settings():
    settings = SiteSetting.query.all()
    return jsonify([setting.to_dict() for setting in settings])

@app.route('/')
def home():
    # هذا المسار يستخدم فقط لاختبار عمل الواجهة الخلفية
    return "مرحباً بكم في الواجهة الخلفية لبلدية ديرة!"

@app.route('/api/status')
def status():
    return jsonify({"status": "Backend is running", "message": "Ready to serve data!"})

# --- مسارات تسجيل الدخول والخروج (تأكد أن login.html موجود في مجلد templates) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))

    # استخدام UserForm لنموذج تسجيل الدخول (اختياري، لكن يمكن استخدامه)
    # لا نستخدم form.validate_on_submit() هنا، بل نتحقق يدوياً
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('تم تسجيل الدخول بنجاح!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.index'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح.', 'success')
    return redirect(url_for('login'))
# ---------------------------------------------------------------------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("تم التأكد من إنشاء جداول قاعدة البيانات.")

        # --- كود إضافة البيانات التجريبية والمستخدم الإداري (يجب أن يكون معلقاً في الإنتاج!) ---
        # إذا كنت تضيف بيانات جديدة يدوياً عبر Admin Panel، يجب أن يكون هذا الجزء معلقاً بالكامل.
        # هذا الجزء فقط للتطوير الأولي أو عند الحاجة لإعادة تهيئة قاعدة البيانات.
        # if not User.query.filter_by(username='admin').first():
        #     print("إضافة مستخدم إداري افتراضي...")
        #     admin_user = User(username='admin')
        #     admin_user.set_password('admin123') # <--- **غيّر 'admin123' بكلمة مرور قوية جداً!**
        #     db.session.add(admin_user)
        #     db.session.commit()
        #     print("تم إضافة المستخدم الإداري: admin بكلمة مرور 'admin123'.")
        #     print("يرجى تغيير كلمة المرور هذه بعد تسجيل الدخول لأول مرة.")
        #
        # if not Department.query.first():
        #     print("إضافة بيانات تجريبية للأقسام...")
        #     dept1 = Department(name="قسم الشؤون الإدارية", description="يتعامل مع السجلات، المراسلات، وإدارة الموظفين.")
        #     dept2 = Department(name="قسم المالية والاقتصاد", description="مسؤول عن الميزانية، الإيرادات، والنفقات البلدية.")
        #     db.session.add_all([dept1, dept2])
        #     db.session.commit()
        #     print("تم إضافة بيانات تجريبية للأقسام بنجاح.")
        #
        # if not Service.query.first():
        #     print("إضافة بيانات تجريبية للخدمات...")
        #     svc1 = Service(name="خدمة تسجيل المواليد", description="إجراءات تسجيل المواليد الجدد.", required_documents="شهادة ميلاد، هوية الأبوين", steps="1. تقديم الطلب 2. التحقق من الوثائق 3. إصدار الشهادة", fees=0.0, working_hours="9:00 - 14:00")
        #     svc2 = Service(name="خدمة الزواج", description="إجراءات عقود الزواج.", required_documents="شهادة ميلاد، هوية، شهادة طبية", steps="1. تقديم الطلب 2. التحقق من الوثائق 3. إبرام العقد", fees=1000.0, working_hours="9:00 - 14:00")
        #     db.session.add_all([svc1, svc2])
        #     db.session.commit()
        #     print("تم إضافة بيانات تجريبية للخدمات بنجاح.")
        #
        # if not SiteSetting.query.first():
        #     print("إضافة بيانات تجريبية لإعدادات الموقع (معلومات الاتصال)...")
        #     setting1 = SiteSetting(setting_name="phone_number", setting_value="+213-26-75-9994")
        #     setting2 = SiteSetting(setting_name="email", setting_value="dirah@hotmail.com")
        #     setting3 = SiteSetting(setting_name="address", setting_value="شارع البلدية، ديرة، الجزائر")
        #     setting4 = SiteSetting(setting_name="working_hours", setting_value="الأحد - الخميس: 8:00 صباحاً - 4:00 مساءً")
        #     db.session.add_all([setting1, setting2, setting3, setting4])
        #     db.session.commit()
        #     print("تم إضافة بيانات تجريبية لإعدادات الموقع بنجاح.")
        # ---------------------------------------------------------------------------------

    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000)) # استخدام متغير PORT لـ Render
