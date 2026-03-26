import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error

# 1. Configuración de Rutas Base (Evita el Error de Carpetas)
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates')
static_dir = os.path.join(base_dir, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = 'ingenieria_tese_karen_2026'

# 2. Ruta del Certificado SSL para Azure
cert_path = os.path.join(base_dir, 'DigiCertGlobalRootG2.crt.pem')

def get_db_connection():
    """Establece conexión con Azure MySQL"""
    return mysql.connector.connect(
        host='sistema-alumbrado-tese.mysql.database.azure.com',
        user='admin_alumbrado', # Si falla, intenta: 'admin_alumbrado@sistema-alumbrado-tese'
        password='Tese2023', # <--- REEMPLAZA ESTO
        database='sistema_alumbrado',
        port=3306,
        ssl_ca=cert_path
    )

# --- RUTAS ---

@app.route('/')
def index():
    if 'loggedin' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            # Validación de usuario
            query = "SELECT * FROM usuarios WHERE username = %s AND password = %s"
            cursor.execute(query, (user, pw))
            account = cursor.fetchone()
            cursor.close()
            conn.close()

            if account:
                session['loggedin'] = True
                session['username'] = account['username']
                session['rol'] = account['rol']
                return redirect(url_for('dashboard'))
            else:
                flash("Usuario o contraseña incorrectos", "danger")
        except Error as e:
            # Esto ayuda a ver el error real en la pantalla de login si falla la BD
            flash(f"Error de base de datos: {e}", "warning")
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'], rol=session['rol'])

@app.route('/monitoreo')
def monitoreo():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Ajustado a las columnas que vimos en tus imágenes anteriores
        cursor.execute("SELECT id, fecha_registro, poste, estado, luz, validacion FROM historico ORDER BY id DESC LIMIT 50")
        datos = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('monitoreo.html', registros=datos)
    except Error as e:
        return f"Error al cargar datos de monitoreo: {e}"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- ARRANQUE ---
if __name__ == '__main__':
    # Render usa la variable de entorno PORT, si no existe usa el 5000
    port = int(os.environ.get("PORT", 5000))
    # debug=True es vital para que si algo falla, Render te diga qué es
    app.run(host='0.0.0.0', port=port, debug=True)
