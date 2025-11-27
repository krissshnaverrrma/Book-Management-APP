import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from fpdf import FPDF
import io
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import secrets
import socket

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

app.config['UPLOAD_FOLDER'] = 'static/pdfs'
app.config['PROFILE_FOLDER'] = 'static/profiles'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROFILE_FOLDER'], exist_ok=True)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'error'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    profile_pic = db.Column(db.String(100), nullable=True)
    recovery_answer = db.Column(db.String(100), nullable=False)
    reset_token = db.Column(db.String(100), nullable=True, unique=True)
    token_expiration = db.Column(db.DateTime, nullable=True)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Available')
    pdf_file = db.Column(db.String(200), nullable=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def send_email(subject, recipient, template, **kwargs):
    """Sends an email using a specified HTML template with a timeout."""
    msg = Message(subject, recipients=[recipient])
    msg.html = render_template(f'emails/{template}.html', **kwargs)

    try:

        with app.app_context():
            with mail.connect as conn:
                conn.send(msg)
        return True
    except socket.timeout as e:
        print(f"EMAIL FAILED: Connection timed out. Error: {e}")
        return False
    except Exception as e:
        print(f"EMAIL FAILED: General SMTP Error. Error: {e}")
        return False


def generate_reset_token(user):
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.token_expiration = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()
    return token


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_addr = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email_addr).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email_addr = request.form.get('email')  # <--- USING EMAIL
        name = request.form.get('name')
        password = request.form.get('password')
        recovery = request.form.get('recovery_answer').lower().strip()
        user = User.query.filter_by(
            email=email_addr).first()  # <--- QUERY BY EMAIL
        if user:
            flash('Email already registered', 'error')
            return redirect(url_for('register'))

        new_user = User(
            email=email_addr, name=name, recovery_answer=recovery,  # <--- SAVE EMAIL
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )
        db.session.add(new_user)
        db.session.commit()

        send_email(
            subject="Welcome to Book-Management-APP!", recipient=email_addr,
            template='welcome_mail', name=name, username=email_addr
        )

        login_user(new_user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()

        if user:
            token = generate_reset_token(user)
            reset_url = url_for('reset_password', token=token, _external=True)

            send_email(
                subject="Password Reset Request",
                recipient=app.config['MAIL_USERNAME'],
                template='reset_link_email',
                username=username,
                reset_url=reset_url
            )
            flash(
                'A password reset link has been sent to your registered email address.', 'success')
        else:
            flash('No account found with that username.', 'error')

        return redirect(url_for('login'))

    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()

    if not user or user.token_expiration < datetime.utcnow():
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password')

        user.password = generate_password_hash(
            new_password, method='pbkdf2:sha256')
        user.reset_token = None
        user.token_expiration = None
        db.session.commit()

        send_email(
            subject="Password Changed Successfully",
            recipient=app.config['MAIL_USERNAME'],
            template='password_reset_confirmation',
            username=user.username
        )

        flash('Your password has been successfully updated. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.username = request.form.get('username')
        new_password = request.form.get('password')
        if new_password:
            current_user.password = generate_password_hash(
                new_password, method='pbkdf2:sha256')
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file.filename != '':
                filename = f"user_{current_user.id}_{secure_filename(file.filename)}"
                file.save(os.path.join(app.config['PROFILE_FOLDER'], filename))
                current_user.profile_pic = filename
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        except:
            db.session.rollback()
            flash('Username already taken.', 'error')
            return redirect(url_for('update_profile'))
    return render_template('update_profile.html')


@app.route('/remove_profile_pic', methods=['POST'])
@login_required
def remove_profile_pic():
    if current_user.profile_pic:
        file_path = os.path.join(
            app.config['PROFILE_FOLDER'], current_user.profile_pic)
        if os.path.exists(file_path):
            os.remove(file_path)
        current_user.profile_pic = None
        db.session.commit()
        flash('Profile picture removed!', 'success')
    return redirect(url_for('update_profile'))


@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    username = current_user.username
    user_id = current_user.id
    if current_user.profile_pic:
        file_path = os.path.join(
            app.config['PROFILE_FOLDER'], current_user.profile_pic)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(current_user)
    db.session.commit()
    logout_user()

    send_email(
        subject="Account Deletion Confirmation", recipient=app.config['MAIL_USERNAME'],
        template='delete_confirmation', username=username, user_id=user_id
    )

    flash('Your account has been permanently deleted.', 'success')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def dashboard():
    all_books = Book.query.all()
    total_books = len(all_books)
    available_books = len([b for b in all_books if b.status == 'Available'])
    borrowed_books = total_books - available_books

    return render_template('dashboard.html',
                           books=all_books, total_books=total_books,
                           available_books=available_books, borrowed_books=borrowed_books)


@app.route('/api/add', methods=['POST'])
@login_required
def api_add_book():
    data = request.get_json()
    new_book = Book(title=data['title'], author=data['author'],
                    category=data['category'], status='Available')
    db.session.add(new_book)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Book added successfully!'})


@app.route('/upload_pdf/<int:book_id>', methods=['POST'])
@login_required
def upload_pdf(book_id):
    if 'file' not in request.files:
        return redirect(url_for('dashboard'))
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        flash('Invalid file or file type. Only PDF is allowed.', 'error')
        return redirect(url_for('dashboard'))
    if file:
        filename = secure_filename(f"book_{book_id}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        book = Book.query.get_or_404(book_id)
        book.pdf_file = filename
        db.session.commit()
        flash('PDF uploaded successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/delete/<int:id>')
@login_required
def delete_book(id):
    book = Book.query.get_or_404(id)
    if book.pdf_file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], book.pdf_file)
        if os.path.exists(file_path):
            os.remove(file_path)
    db.session.delete(book)
    db.session.commit()
    flash('Book successfully deleted!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/issue/<int:id>')
@login_required
def issue_book(id):
    book = Book.query.get_or_404(id)
    if book.status == 'Available':
        book.status = 'Borrowed'
        db.session.commit()
        flash(f'Book issued successfully.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/return/<int:id>')
@login_required
def return_book(id):
    book = Book.query.get_or_404(id)
    if book.status == 'Borrowed':
        book.status = 'Available'
        db.session.commit()
        flash('Book successfully returned!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/download_report')
@login_required
def download_report():
    books = Book.query.all()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="BiblioTech Library Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", style="B", size=12)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(80, 10, "Title", 1, 0, 'C', True)
    pdf.cell(50, 10, "Author", 1, 0, 'C', True)
    pdf.cell(30, 10, "Category", 1, 0, 'C', True)
    pdf.cell(30, 10, "Status", 1, 1, 'C', True)
    pdf.set_font("Arial", size=10)
    for book in books:
        title = (book.title[:35] +
                 '...') if len(book.title) > 35 else book.title
        author = (book.author[:20] +
                  '...') if len(book.author) > 20 else book.author
        pdf.cell(80, 10, title, 1)
        pdf.cell(50, 10, author, 1)
        pdf.cell(30, 10, book.category, 1)
        pdf.cell(30, 10, book.status, 1, 1)
    pdf_output = io.BytesIO(pdf.output(dest='S').encode('latin-1'))
    pdf_output.seek(0)
    return send_file(pdf_output, as_attachment=True, download_name='Library_Catalog.pdf', mimetype='application/pdf')


if __name__ == "__main__":
    app.run(debug=True)
