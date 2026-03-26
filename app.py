import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error

base_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
            static_folder=os.path.join(base_dir, 'static'),
            template_folder=os.path.join(base_dir, 'templates'))

app.secret_key = 'ingenieria_tese_karen_2026'

cert_path = os.path.join(base_dir, 'DigiCertGlobalRootG2.crt.pem')

def get_db_connection():
    return mysql.connector.connect(
        host='sistema-alumbrado-tese.mysql.database.azure.com',
        user='admin_alumbrado', 
        password='Tese2023', 
        database='sistema_alumbrado',
        port=3306,
        ssl_ca=cert_path
    )

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
            flash(f"Error de conexión a Azure: {e}", "warning")
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
    
    # Obtener fechas del formulario (metodo GET)
    f_inicio = request.args.get('fecha_inicio')
    f_fin = request.args.get('fecha_fin')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Consulta base
        query = "SELECT id, fecha_registro, poste, estado, luz, validacion FROM historico"
        params = []

        # Si el usuario eligió fechas, filtramos
        if f_inicio and f_fin:
            query += " WHERE DATE(fecha_registro) BETWEEN %s AND %s"
            params = [f_inicio, f_fin]
        
        query += " ORDER BY fecha_registro DESC LIMIT 100"
        
        cursor.execute(query, params)
        datos = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('monitoreo.html', registros=datos, f_ini=f_inicio, f_fin=f_fin)
    except Error as e:
        return f"Error en el filtro de monitoreo: {e}"

@app.route('/usuarios')
def usuarios():
    if 'loggedin' not in session or session.get('rol') != 'admin':
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
        return f"Error: {e}"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
