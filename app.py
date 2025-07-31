from flask import Flask, jsonify, request, redirect, url_for, flash, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import date, datetime

# --- 1. استيرادات Flask-Admin الجديدة (موجودة لديك) ---
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
# ----------------------------------------------------

# --- استيرادات جديدة لـ Flask-Login و Werkzeug.security ---
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
# --------------------------------------------------------

# --- استيرادات جديدة لـ WTForms و Flask-WTF (مطلوبة لنموذج المستخدم) ---
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Optional
# ----------------------------------------------------------

app = Flask(__name__)

# --- تعديل تهيئة CORS هنا ---
# بدلاً من CORS(app)، سنحدد المصادر المسموح بها بشكل صريح
# هذا يسمح لـ Netlify بالوصول إلى الـ API
CORS(app, resources={r"/api/*": {"origins": ["https://apcdirah-dz.netlify.app", "http://localhost:5173"]}})
# ----------------------------------------------------------

# إعداد قاعدة البيانات PostgreSQL
# استخدم متغير بيئة (Environment Variable) لقاعدة البيانات
# هذا يعني أننا سنحصل على رابط قاعدة البيانات من إعدادات Render.com
# تأكد من أن هذا هو السطر الجديد الذي يشير إلى متغير البيئة
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
# ----------------------------------------------------------
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# --- 2. إعداد مفتاح سري لـ Flask-Admin و Flask-Login (مهم جداً للأمان) ---
# يجب تغيير هذا المفتاح السري إلى قيمة عشوائية قوية جداً في بيئة الإنتاج
# استخدم متغير بيئة للمفتاح السري أيضاً لجعلها أكثر أماناً
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_super_secret_key_that_you_must_change_now_12345')
# ----------------------------------------------------

db = SQLAlchemy(app)

# --- تهيئة Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # تحديد اسم view لوظيفة تسجيل الدخول
login_manager.login_message = "الرجاء تسجيل الدخول للوصول إلى هذه الصفحة."
login_manager.login_message_category = "info"
# -------------------------

# --- تعريف نماذج قاعدة البيانات (Database Models) ---
# (كل تعريفات النماذج الخاصة بك هنا كما هي في ملفك الأصلي)
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
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'category': self.category,
            'budget': self.budget,
            'contractor': self.contractor,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'progress_percentage': self.progress_percentage,
            'image_url': self.image_url
        }

class Deliberation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.String(10), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    document_url = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'date': self.date,
            'category': self.category,
            'document_url': self.document_url,
            'image_url': self.image_url
        }

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    required_documents = db.Column(db.Text, nullable=True)
    steps = db.Column(db.Text, nullable=True)
    fees = db.Column(db.Float, nullable=True)
    working_hours = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'required_documents': self.required_documents,
            'steps': self.steps,
            'fees': self.fees,
            'working_hours': self.working_hours
        }

class Decision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(100), nullable=True)
    date = db.Column(db.String(10), nullable=True) # يمكن أن يكون تاريخ القرار
    document_url = db.Column(db.String(255), nullable=True) # رابط لوثيقة القرار

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'type': self.type,
            'date': self.date,
            'document_url': self.document_url
        }

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
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'date_published': self.date_published.isoformat() if self.date_published else None,
            'author': self.author,
            'announcement_type': self.announcement_type,
            'document_url': self.document_url,
            'image_url': self.image_url,
            'deadline': self.deadline.isoformat() if self.deadline else None
        }

class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_name = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'setting_name': self.setting_name,
            'setting_value': self.setting_value
        }

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

# --- تعريف نموذج المستخدم (User Model) لـ Flask-Login ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False) # هذا هو الطول الصحيح الآن

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# دالة تحميل المستخدم لـ Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# ------------------------------------------------------

# --- فئة مخصصة لـ ModelView تتطلب تسجيل الدخول ---
class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        # إعادة توجيه المستخدم إلى صفحة تسجيل الدخول إذا لم يكن مسجلاً
        flash('الرجاء تسجيل الدخول للوصول إلى لوحة التحكم.', 'warning')
        return redirect(url_for('login', next=request.url))

# --- تعريف نموذج WTForms مخصص للمستخدمين ---
class UserForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired()])
    password = PasswordField('كلمة المرور الجديدة', validators=[Optional()])
    confirm_password = PasswordField('تأكيد كلمة المرور الجديدة', validators=[
        Optional(),
        EqualTo('password', message='كلمتا المرور غير متطابقتين')
    ])

# --- فئة مخصصة لـ User ModelView لمعالجة كلمة المرور ---
class UserAdminView(AuthenticatedModelView):
    form = UserForm
    column_exclude_list = ['password_hash']

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.set_password(form.password.data)
        return super().on_model_change(form, model, is_created)

    def on_form_prefill(self, form, id):
        form.password.data = ''
        form.confirm_password.data = ''
        super().on_form_prefill(form, id)
# -----------------------------------------------

# --- تعريف نموذج WTForms مخصص لإعدادات الموقع ---
class SiteSettingForm(FlaskForm):
    # حقول النموذج تتطابق مع أعمدة SiteSetting
    setting_name = StringField('اسم الإعداد', validators=[DataRequired()])
    setting_value = TextAreaField('قيمة الإعداد', validators=[Optional()])

# --- فئة مخصصة لـ SiteSetting ModelView ---
class SiteSettingAdminView(AuthenticatedModelView):
    # ربط النموذج المخصص بـ Flask-Admin
    form = SiteSettingForm
    # يمكنك إضافة column_labels هنا إذا أردت تسميات عرض مختلفة
    # column_labels = dict(setting_name='اسم الإعداد', setting_value='القيمة')
# -----------------------------------------------

# --- 3. تهيئة Flask-Admin وإضافة النماذج ---
# يجب أن تأتي تهيئة Admin بعد تعريف جميع النماذج التي سيتم إدارتها.
admin = Admin(app, name='لوحة تحكم بلدية ديرة', template_mode='bootstrap3', url='/admin')

# --- إضافة النماذج إلى Admin باستخدام AuthenticatedModelView ---
admin.add_view(AuthenticatedModelView(Department, db.session, name='الأقسام'))
admin.add_view(AuthenticatedModelView(Project, db.session, name='المشاريع'))
admin.add_view(AuthenticatedModelView(Announcement, db.session, name='الإعلانات'))
admin.add_view(AuthenticatedModelView(Deliberation, db.session, name='المداولات'))
admin.add_view(AuthenticatedModelView(Decision, db.session, name='القرارات'))
# --- استخدام SiteSettingAdminView المخصصة لإعدادات الموقع ---
admin.add_view(SiteSettingAdminView(SiteSetting, db.session, name='إعدادات الموقع'))
admin.add_view(AuthenticatedModelView(Service, db.session, name='الخدمات'))
# --- استخدام UserAdminView المخصصة للمستخدمين ---
admin.add_view(UserAdminView(User, db.session, name='المستخدمون'))
# ------------------------------------------------------------

# --- تعريف الـ APIs (كما هي في ملفك الأصلي) ---

@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify([project.to_dict() for project in projects])

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict())

@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.get_json()
    new_project = Project(
        title=data['title'],
        description=data.get('description'),
        status=data.get('status'),
        category=data.get('category'),
        budget=data.get('budget'),
        contractor=data.get('contractor'),
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        progress_percentage=data.get('progress_percentage', 0),
        image_url=data.get('image_url')
    )
    db.session.add(new_project)
    db.session.commit()
    return jsonify(new_project.to_dict()), 201

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    project.title = data.get('title', project.title)
    project.description = data.get('description', project.description)
    project.status = data.get('status', project.status)
    project.category = data.get('category', project.category)
    project.budget = data.get('budget', project.budget)
    project.contractor = data.get('contractor', project.contractor)
    project.start_date = data.get('start_date', project.start_date)
    project.end_date = data.get('end_date', project.end_date)
    project.progress_percentage = data.get('progress_percentage', project.progress_percentage)
    project.image_url = data.get('image_url', project.image_url)
    db.session.commit()
    return jsonify(project.to_dict())

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted successfully'}), 204

@app.route('/api/departments', methods=['GET'])
def get_departments():
    departments = Department.query.all()
    return jsonify([department.to_dict() for department in departments])

@app.route('/api/departments/<int:department_id>', methods=['GET'])
def get_department(department_id):
    department = Department.query.get_or_404(department_id)
    return jsonify(department.to_dict())

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

# --- إضافة مسار API للخدمات هنا ---
@app.route('/api/services', methods=['GET'])
def get_services():
    services = Service.query.all()
    return jsonify([service.to_dict() for service in services])
# -----------------------------------

@app.route('/api/settings', methods=['GET']) # <--- هذا هو API الجديد لإعدادات الموقع
def get_settings():
    settings = SiteSetting.query.all()
    return jsonify([setting.to_dict() for setting in settings])

@app.route('/')
def home():
    return "مرحباً بكم في الواجهة الخلفية لبلدية ديرة!"

@app.route('/api/status')
def status():
    return jsonify({"status": "Backend is running", "message": "Ready to serve data!"})

# --- مسارات تسجيل الدخول والخروج ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.index')) # إذا كان المستخدم مسجلاً، اذهب مباشرة إلى لوحة التحكم

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('تم تسجيل الدخول بنجاح!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.index')) # بعد تسجيل الدخول، اذهب إلى لوحة التحكم
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة.', 'danger')
    
    return render_template('login.html') # سيتم تحميل هذا الملف من مجلد templates

@app.route('/logout')
@login_required # يتطلب أن يكون المستخدم مسجلاً للدخول للخروج
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح.', 'success')
    return redirect(url_for('login'))
# -----------------------------------

if __name__ == '__main__':
    with app.app_context():
        # هذا السطر ينشئ جداول قاعدة البيانات إذا لم تكن موجودة.
        # يجب أن يبقى، وسيعمل على PostgreSQL الجديدة.
        db.create_all()
        print("تم التأكد من إنشاء جداول قاعدة البيانات.")

        # هذا الجزء من الكود يقوم بإضافة بيانات تجريبية (بما في ذلك المستخدم الإداري).
        # يجب **التعليق عليه بالكامل** أو **حذفه** عند النشر إلى بيئة الإنتاج مثل Render.com.
        # سنقوم بإضافة المستخدم الإداري والبيانات يدوياً عبر لوحة تحكم Flask-Admin بعد النشر.
        # --> لقد أعدت التعليق على الأسطر التالية الآن! <--

        # if not User.query.filter_by(username='admin').first():
        #     print("إضافة مستخدم إداري افتراضي...")
        #     admin_user = User(username='admin')
        #     admin_user.set_password('admin123') # <--- **غيّر 'admin123' بكلمة مرور قوية جداً!**
        #     db.session.add(admin_user)
        #     db.session.commit()
        #     print("تم إضافة المستخدم الإداري: admin بكلمة مرور 'admin123'.")
        #     print("يرجى تغيير كلمة المرور هذه بعد تسجيل الدخول لأول مرة.")

        # if not Department.query.first():
        #     print("إضافة بيانات تجريبية للأقسام...")
        #     dept1 = Department(name="قسم الشؤون الإدارية", description="يتعامل مع السجلات، المراسلات، وإدارة الموظفين.")
        #     dept2 = Department(name="قسم المالية والاقتصاد", description="مسؤول عن الميزانية، الإيرادات، والنفقات البلدية.")
        #     dept3 = Department(name="قسم التعمير والبناء", description="يشرف على رخص البناء والتخطيط العمراني.")
        #     dept4 = Department(name="قسم النظافة والبيئة", description="يعمل على جمع النفايات وصيانة المساحات الخضراء.")
        #     db.session.add_all([dept1, dept2, dept3, dept4])
        #     db.session.commit()
        #     print("تم إضافة بيانات تجريبية للأقسام بنجاح.")

        # if not Project.query.first():
        #     print("إضافة بيانات تجريبية للمشاريع...")
        #     proj1 = Project(
        #         title="مشروع تهيئة وسط المدينة",
        #         description="مشروع لتطوير البنية التحتية والمساحات الخضراء في وسط المدينة.",
        #         status="قيد التنفيذ",
        #         category="تنمية حضرية",
        #         budget=5000000.00,
        #         contractor="شركة البناء الحديث",
        #         start_date="2024-03-01",
        #         end_date="2025-03-01",
        #         progress_percentage=60,
        #         image_url="https://via.placeholder.com/400x250/2563eb/FFFFFF?text=Project+1"
        #     )
        #     proj2 = Project(
        #         title="مشروع إنجاز مدرسة ابتدائية جديدة",
        #         description="بناء مدرسة ابتدائية بطاقة استيعاب 500 تلميذ في حي الأمل.",
        #         status="مخطط له",
        #         category="تعليم",
        #         budget=3000000.00,
        #         contractor="شركة الأفق الجديد",
        #         start_date="2025-09-01",
        #         end_date="2026-09-01",
        #         progress_percentage=0,
        #         image_url="https://via.placeholder.com/400x250/ef4444/FFFFFF?text=Project+2"
        #     )
        #     proj3 = Project(
        #         title="ترميم شبكة الطرق الفرعية",
        #         description="إعادة تزفيت وصيانة الطرق داخل الأحياء السكنية.",
        #         status="منجز",
        #         category="بنية تحتية",
        #         budget=2000000.00,
        #         contractor="مؤسسة الطرقات",
        #         start_date="2023-01-15",
        #         end_date="2023-07-30",
        #         progress_percentage=100,
        #         image_url="https://via.placeholder.com/400x250/10b981/FFFFFF?text=Project+3"
        #     )
        #     db.session.add_all([proj1, proj2, proj3])
        #     db.session.commit()
        #     print("تم إضافة بيانات تجريبية للمشاريع بنجاح.")

        # if not Announcement.query.first():
        #     print("إضافة بيانات تجريبية للإعلانات...")
        #     announcement1 = Announcement(
        #         title='تمديد ساعات عمل البلدية خلال شهر رمضان',
        #         content='تعلن بلدية ديرة عن تمديد ساعات العمل الرسمية خلال شهر رمضان المبارك لتلبية احتياجات المواطنين بشكل أفضل. ستكون الساعات الجديدة من 9 صباحاً حتى 3 مساءً.',
        #         date_published=datetime(2025, 3, 1, 9, 0, 0),
        #         author='الإدارة العامة',
        #         announcement_type='عام',
        #         image_url='https://via.placeholder.com/300x200/4CAF50/FFFFFF?text=RAMADAN',
        #         document_url=None,
        #         deadline=None
        #     )
        #     announcement2 = Announcement(
        #         title='مناقصة: مشروع بناء قاعة متعددة الخدمات',
        #         content='تدعو بلدية ديرة الشركات المؤهلة لتقديم عروضها لمشروع بناء قاعة متعددة الخدمات في حي السلام.',
        #         date_published=datetime(2025, 6, 10, 10, 30, 0),
        #         author='قسم الهندسة',
        #         announcement_type='مناقصة',
        #         document_url='https://example.com/tender-hall-conditions.pdf',
        #         image_url='https://via.placeholder.com/300x200/2196F3/FFFFFF?text=TENDER',
        #         deadline=datetime(2025, 7, 10, 15, 0, 0)
        #     )
        #     announcement3 = Announcement(
        #         title='استشارة: تطوير الخدمات الرقمية للبلدية',
        #         content='تسعى البلدية للحصول على استشارات من الخبراء والشركات المتخصصة في مجال تطوير الخدمات الرقمية وتبسيط الإجراءات الإدارية.',
        #         date_published=datetime(2025, 6, 20, 11, 0, 0),
        #         author='قسم التخطيط',
        #         announcement_type='استشارة',
        #         document_url='https://example.com/consultation-digital-services.pdf',
        #         image_url='https://via.placeholder.com/300x200/FFC107/FFFFFF?text=CONSULT',
        #         deadline=datetime(2025, 8, 1, 12, 0, 0)
        #     )
        #     announcement4 = Announcement(
        #         title='مناقصة: صيانة شبكة الإنارة العمومية',
        #         content='تعلن بلدية ديرة عن فتح باب المناقصة لصيانة وتطوير شبكة الإنارة العمومية في أحياء المدينة.',
        #         date_published=datetime(2025, 7, 1, 14, 0, 0),
        #         author='قسم الأشغال العمومية',
        #         announcement_type='مناقصة',
        #         document_url='https://example.com/tender-lighting-conditions.pdf',
        #         image_url='https://via.placeholder.com/300x200/9C27B0/FFFFFF?text=LIGHTS',
        #         deadline=datetime(2025, 7, 25, 10, 0, 0)
        #     )
        #     db.session.add_all([announcement1, announcement2, announcement3, announcement4])
        #     db.session.commit()
        #     print("تم إضافة بيانات تجريبية للإعلانات بنجاح.")

        # if not Deliberation.query.first():
        #     print("إضافة بيانات تجريبية للمداولات...")
        #     delib1 = Deliberation(
        #         title="مداولة بشأن ميزانية 2025",
        #         description="مناقشة واعتماد مشروع ميزانية البلدية للعام المالي 2025، مع التركيز على أولويات التنمية المحلية.",
        #         date="2024-12-15",
        #         category="مالية",
        #         document_url="https://example.com/deliberation-budget-2025.pdf",
        #         image_url="https://via.placeholder.com/300x200/8BC34A/FFFFFF?text=Budget+2025"
        #     )
        #     delib2 = Deliberation(
        #         title="مداولة حول مخطط التهيئة العمرانية",
        #         description="عرض ومناقشة التعديلات المقترحة على مخطط التهيئة العمرانية للمدينة لضمان التنمية المستدامة.",
        #         date="2025-01-20",
        #         category="تخطيط عمراني",
        #         document_url="https://example.com/deliberation-urban-plan.pdf",
        #         image_url="https://via.placeholder.com/300x200/FF5722/FFFFFF?text=Urban+Plan"
        #     )
        #     delib3 = Deliberation(
        #         title="مداولة خدمات النظافة والبيئة",
        #         description="استعراض وتقييم عقود خدمات النظافة البلدية ومناقشة سبل تحسينها وتعزيز الوعي البيئي.",
        #         date="2025-03-10",
        #         category="خدمات بلدية",
        #         document_url="https://example.com/deliberation-cleanliness.pdf",
        #         image_url="https://via.placeholder.com/300x200/607D8B/FFFFFF?text=Cleanliness"
        #     )
        #     db.session.add_all([delib1, delib2, delib3])
        #     db.session.commit()
        #     print("تم إضافة بيانات تجريبية للمداولات بنجاح.")

        # if not Decision.query.first():
        #     print("إضافة بيانات تجريبية للقرارات...")
        #     dec1 = Decision(
        #         title="قرار رقم 123: تنظيم أسواق البلدية",
        #         type="تنظيمي",
        #         date="2024-11-01",
        #         document_url="https://example.com/decision-market-regulation.pdf"
        #     )
        #     dec2 = Decision(
        #         title="قرار رقم 456: تخصيص أراضي للمشاريع السكنية",
        #         type="تخطيطي",
        #         date="2024-10-20",
        #         document_url="https://example.com/decision-housing-land.pdf"
        #     )
        #     dec3 = Decision(
        #         title="قرار رقم 789: دعم الجمعيات المحلية",
        #         type="اجتماعي",
        #         date="2024-09-15",
        #         document_url="https://example.com/decision-associations-support.pdf"
        #     )
        #     db.session.add_all([dec1, dec2, dec3])
        #     db.session.commit()
        #     print("تم إضافة بيانات تجريبية للقرارات بنجاح.")

        # if not SiteSetting.query.first():
        #     print("إضافة بيانات تجريبية لإعدادات الموقع (معلومات الاتصال)...")
        #     setting1 = SiteSetting(setting_name="phone_number", setting_value="+971-4-123-4567")
        #     setting2 = SiteSetting(setting_name="email", setting_value="info@deiramunicipality.ae")
        #     setting3 = SiteSetting(setting_name="address", setting_value="شارع البلدية، ديرة، الإمارات العربية المتحدة")
        #     setting4 = SiteSetting(setting_name="working_hours", setting_value="الأحد - الخميس: 8:00 صباحاً - 4:00 مساءً")
        #     db.session.add_all([setting1, setting2, setting3, setting4])
        #     db.session.commit()
        #     print("تم إضافة بيانات تجريبية لإعدادات الموقع بنجاح.")

        # if not Service.query.first():
        #      print("إضافة بيانات تجريبية للخدمات...")
        #      svc1 = Service(name="خدمة تسجيل المواليد", description="إجراءات تسجيل المواليد الجدد.", required_documents="شهادة ميلاد، هوية الأبوين", steps="1. تقديم الطلب 2. التحقق من الوثائق 3. إصدار الشهادة", fees=0.0, working_hours="9:00 - 14:00")
        #      db.session.add(svc1)
        #      db.session.commit()
        #      print("تم إضافة بيانات تجريبية للخدمات بنجاح.")

    app.run(debug=True, host='0.0.0.0')
