from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = 'ingenieria_tese_karen_2026'

# Ruta para el certificado en Render
base_dir = os.path.dirname(os.path.abspath(__file__))
cert_path = os.path.join(base_dir, 'DigiCertGlobalRootG2.crt.pem')

def get_db_connection():
    return mysql.connector.connect(
        host='sistema-alumbrado-tese.mysql.database.azure.com',
        user='admin_alumbrado',
        password='TU_CONTRASEÑA_DE_AZURE', # <-- Pon tu contraseña real aquí
        database='sistema_alumbrado',
        ssl_ca=cert_path
    )

@app.route('/')
def index():
    if 'loggedin' in session: return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user, pw = request.form['username'], request.form['password']
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (user, pw))
            account = cursor.fetchone()
            cursor.close()
            conn.close()
            if account:
                session.update({'loggedin': True, 'username': account['username'], 'rol': account['rol']})
                return redirect(url_for('dashboard'))
            flash("Usuario o contraseña incorrectos")
        except Exception as e:
            flash(f"Error de conexión: {str(e)}")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'loggedin' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'], rol=session['rol'])

@app.route('/monitoreo')
def monitoreo():
    if 'loggedin' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM historico ORDER BY id DESC LIMIT 50")
    datos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('monitoreo.html', registros=datos)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Render usa la variable de entorno PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)