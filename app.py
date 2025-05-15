# app.py

import logging
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_required, current_user
from models import db, User, Script, Option
from auth import auth_bp, admin_required

# Включаем логгинг для отладки
logging.basicConfig(level=logging.DEBUG)

# Flask-приложение
app = Flask(__name__)
app.secret_key = 'super_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных
db.init_app(app)

# Подключение Blueprints
app.register_blueprint(auth_bp)

# Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)
with app.app_context():
    if os.path.exists("db.sqlite"):
        os.remove("db.sqlite")  # удалим сломанную БД
    db.create_all()
    if not User.query.filter_by(phone="998901234567").first():
        admin = User(phone="998901234567", role="admin")
        admin.set_password("adminpass")
        db.session.add(admin)
        db.session.commit()
        print("✅ Админ создан")




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------- Роуты ----------

@app.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_panel'))
        else:
            return redirect(url_for('operator_panel'))
    return redirect(url_for('auth.login'))

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    scripts = Script.query.all()
    return render_template('admin_panel.html', scripts=scripts)

@app.route('/script')
@login_required
def script_start():
    if current_user.role != 'admin':
        return redirect(url_for('operator_panel'))  # 🚫 операторов разворачиваем
    return redirect(url_for('script_step', step_id=1))



@app.route('/script/<int:step_id>')
@login_required
def script_step(step_id):
    step = Script.query.get_or_404(step_id)
    return render_template('operator_view.html', step=step)

@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_script():
    if request.method == 'POST':
        text = request.form['text']
        script = Script(text=text)
        db.session.add(script)
        db.session.commit()
        flash('Шаг добавлен!')
        return redirect(url_for('admin_panel'))
    return render_template('admin_add.html')

@app.route('/admin/edit/<int:script_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_script(script_id):
    script = Script.query.get_or_404(script_id)

    if request.method == 'POST':
        script.text = request.form['text']
        db.session.query(Option).filter_by(script_id=script.id).delete()

        options_data = zip(request.form.getlist('opt_text'), request.form.getlist('opt_next'))
        for text, next_id in options_data:
            if text.strip():
                option = Option(text=text, next_id=int(next_id or 0), script=script)
                db.session.add(option)

        db.session.commit()
        flash('Шаг обновлён!')
        return redirect(url_for('admin_panel'))

    return render_template('admin_edit.html', script=script)

@app.route('/admin/delete/<int:script_id>', methods=['POST'])
@login_required
@admin_required
def delete_script(script_id):
    script = Script.query.get_or_404(script_id)
    db.session.delete(script)
    db.session.commit()
    flash('Шаг удалён.')
    return redirect(url_for('admin_panel'))

@app.route('/admin/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.role = request.form['role']
        new_password = request.form['password']
        if new_password:
            user.set_password(new_password)
        db.session.commit()
        flash("Пользователь обновлён")
        return redirect(url_for('manage_users'))
    return render_template('edit_user.html', user=user)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash("Нельзя удалить самого себя")
        return redirect(url_for('manage_users'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("Пользователь удалён")
    return redirect(url_for('manage_users'))

@app.route('/admin/users/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    phone = request.form['phone']
    password = request.form['password']
    role = request.form['role']

    if User.query.filter_by(phone=phone).first():
        flash("Такой пользователь уже существует.")
        return redirect(url_for('manage_users'))

    user = User(phone=phone, role=role)
    user.set_password(password)  # ← ⚠️ вот это обязательно!
    db.session.add(user)
    db.session.commit()
    flash("Пользователь создан.")
    return redirect(url_for('manage_users'))

@app.route('/operator')
@login_required
def operator_panel():
    scripts = Script.query.all()
    return render_template('operator_list.html', scripts=scripts)


# в самом конце app.py
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
