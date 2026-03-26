import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error

# 1. Configuración de Rutas para la Nube (Render)
base_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
            static_folder=os.path.join(base_dir, 'static'),
            template_folder=os.path.join(base_dir, 'templates'))

app.secret_key = 'ingenieria_tese_karen_2026'

# 2. Configuración de la Base de Datos Azure
# Asegúrate de que el archivo DigiCertGlobalRootG2.crt.pem esté en la raíz de tu GitHub
cert_path = os.path.join(base_dir, 'DigiCertGlobalRootG2.crt.pem')

def get_db_connection():
    """Establece la conexión con Azure MySQL utilizando el certificado SSL"""
    return mysql.connector.connect(
        host='sistema-alumbrado-tese.mysql.database.azure.com',
        user='admin_alumbrado', 
        password='Tese2023', 
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
        # Estos nombres deben coincidir con el 'name' de tus inputs en HTML
        user = request.form.get('username')
        pw = request.form.get('password')
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            # Validación de usuario en la tabla
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
            # Si hay error de conexión, lo mostrará en pantalla
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
        # Consulta para traer los datos del alumbrado
        cursor.execute("SELECT id, fecha_registro, poste, estado, luz, validacion FROM historico ORDER BY id DESC LIMIT 50")
        datos = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('monitoreo.html', registros=datos)
    except Error as e:
        return f"Error al cargar monitoreo: {e}"

@app.route('/usuarios')
def usuarios():
    """Ruta para la gestión de usuarios (Solo para Admin)"""
    if 'loggedin' not in session or session.get('rol') != 'admin':
        flash("Acceso no autorizado", "danger")
        return redirect(url_for('dashboard'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, rol FROM usuarios")
        lista = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('usuarios.html', lista_usuarios=lista)
    except Error as e:
        return f"Error en catálogo: {e}"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- CONFIGURACIÓN DE ARRANQUE PARA RENDER ---

if __name__ == '__main__':
    # Render asigna el puerto automáticamente mediante una variable de entorno
    port = int(os.environ.get("PORT", 5000))
    # debug=True es útil para ver errores en tiempo real durante tu entrega
    app.run(host='0.0.0.0', port=port, debug=True)
            
