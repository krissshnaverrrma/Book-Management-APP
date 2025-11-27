# 📚 Book-Management-APP

This is a Flask-based Book Management Application designed to help users manage their personal or small library collections. It integrates with the Google Books API for easy book discovery and includes user authentication, profile management, and PDF report generation.

## ✨ Features

-   **User Authentication:** Secure login, registration, and password reset functionality with email-based token verification.
-   **Dashboard Overview:** At-a-glance statistics for total, available, and borrowed books.
-   **Google Books API Integration:** Search for books by title, author, or ISBN directly from the dashboard.
-   **Library Management:** Add new books to your collection, categorize them, and track their availability status (Available/Borrowed).
-   **PDF Report Generation:** Download a PDF report of your entire book collection.
-   **User Profiles:** Update personal information and profile pictures.
-   **Responsive UI:** Modern dark theme with glassmorphism design, built with Bootstrap 5.
-   **Email Notifications:** Welcome emails, password reset links, and account deletion confirmations.

## 🚀 Getting Started

Follow these steps to set up and run the application locally.

### Prerequisites

-   Python 3.8+
-   `pip` (Python package installer)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/krissshnaverrrma/Book-Management-APP.git](https://github.com/krissshnaverrrma/Book-Management-APP.git)
    cd Book-Management-APP
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    -   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    -   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(If `requirements.txt` doesn't exist, create it with `pip freeze > requirements.txt` after installing Flask, Flask-SQLAlchemy, Flask-Login, Flask-Mail, FPDF, Werkzeug, requests, python-dotenv (if used), secrets)*

### Configuration

Before running, you need to configure your email settings and a secret key:

1.  **Open `app.py`** and update the following lines with your details:
    ```python
    app.config['SECRET_KEY'] = 'YOUR_SECRET_KEY_PASTE_HERE'
    app.config['MAIL_USERNAME'] = 'YOUR_EMAIL_ADDRESS@gmail.com'
    app.config['MAIL_PASSWORD'] = 'YOUR_GENERATED_APP_PASSWORD' (required for 2FA)
    app.config['MAIL_DEFAULT_SENDER'] = 'YOUR_EMAIL_ADDRESS@gmail.com'
    ```
    * **Google App Password:** If you use 2-Factor Authentication, you MUST generate an [App Password](https://support.google.com/accounts/answer/185833) from your Google Account security settings. Regular passwords will not work.

### Running the Application

1.  **Ensure your virtual environment is active.**
2.  **Delete any old `library.db` file** if you're starting fresh or encounter database errors (`no such column`). This will create a new database with the correct schema.
3.  **Run the Flask application:**
    ```bash
    python app.py
    ```
    or
    ```bash
    flask run --debug
    ```

4.  Open your web browser and navigate to `http://127.0.0.1:5000`.

## 📸 Screenshot

Here's a glimpse of the Book-Management-APP dashboard:

![Book-Management-APP Dashboard](static/images/dashboard-screenshot.png)

*(You will need to replace `static/images/dashboard-screenshot.png` with the actual path to your image file once you've saved it.)*

## 🧑‍💻 Development

Developed by [Krishna Verma](https://www.linkedin.com/in/krishnaverma/)(https://github.com/krissshnaverrrma).

---