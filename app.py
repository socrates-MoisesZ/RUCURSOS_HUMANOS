from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Clave secreta para manejar sesiones

# Crear la base de datos y las tablas si no existen
def init_db():
    if not os.path.exists('database.db'):  # Si la base de datos no existe
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Crear la tabla de administradores
        cursor.execute('''
            CREATE TABLE admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        # Crear la tabla de departamentos
        cursor.execute('''
            CREATE TABLE departamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL
            )
        ''')

        # Insertar departamentos por defecto
        cursor.executemany('''
            INSERT INTO departamentos (nombre) VALUES (?)
        ''', [("Ventas",), ("Recursos Humanos",), ("TI",), ("Marketing",), ("Finanzas",)])

        # Insertar un admin de ejemplo si la tabla está vacía
        cursor.execute('''
            INSERT INTO admins (username, password) 
            SELECT "admin", "admin123" 
            WHERE NOT EXISTS (SELECT 1 FROM admins WHERE username = "admin")
        ''')

        cursor.execute('''
            CREATE TABLE empleados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                cargo TEXT NOT NULL,
                departamento_id INTEGER,
                fecha_contratacion TEXT,
                FOREIGN KEY(departamento_id) REFERENCES departamentos(id)
            )
        ''')

        conn.commit()
        conn.close()

# Llamar a la función para inicializar la base de datos al iniciar la app
init_db()

# Ruta para la página de inicio de sesión
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Conexión a la base de datos
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Consulta para verificar si el admin existe
        cursor.execute("SELECT * FROM admins WHERE username = ? AND password = ?", (username, password))
        admin = cursor.fetchone()
        
        conn.close()

        if admin:
            session['logged_in'] = True  # Iniciar sesión
            return redirect(url_for('dashboard'))  # Redirigir al dashboard
        else:
            return render_template('login.html', error="Credenciales incorrectas. Intenta de nuevo.")  # Mostrar error

    return render_template('login.html')

# Ruta para el dashboard (administrador)
@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:  # Si no está logueado, redirigir al login
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# Ruta para gestionar departamentos
@app.route('/gestionar_departamentos', methods=['GET', 'POST'])
def gestionar_departamentos():
    if 'logged_in' not in session:  # Si no está logueado, redirigir al login
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Si se recibe una solicitud POST para agregar un nuevo departamento
    if request.method == 'POST':
        nombre = request.form['nombre']
        cursor.execute('INSERT INTO departamentos (nombre) VALUES (?)', (nombre,))
        conn.commit()

    # Obtener todos los departamentos para mostrar
    cursor.execute('SELECT * FROM departamentos')
    departamentos = cursor.fetchall()

    conn.close()
    return render_template('gestionar_departamentos.html', departamentos=departamentos)

# Ruta para eliminar un departamento
@app.route('/eliminar_departamento/<int:id>', methods=['GET'])
def eliminar_departamento(id):
    if 'logged_in' not in session:  # Si no está logueado, redirigir al login
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM departamentos WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('gestionar_departamentos'))

# Ruta para editar un departamento
@app.route('/editar_departamento/<int:id>', methods=['GET', 'POST'])
def editar_departamento(id):
    if 'logged_in' not in session:  # Si no está logueado, redirigir al login
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Si se recibe un POST para actualizar el departamento
    if request.method == 'POST':
        nombre = request.form['nombre']
        cursor.execute('UPDATE departamentos SET nombre = ? WHERE id = ?', (nombre, id))
        conn.commit()
        return redirect(url_for('gestionar_departamentos'))

    # Obtener el departamento actual para mostrar en el formulario
    cursor.execute('SELECT * FROM departamentos WHERE id = ?', (id,))
    departamento = cursor.fetchone()

    conn.close()
    return render_template('editar_departamento.html', departamento=departamento)


@app.route('/gestionar_empleados', methods=['GET', 'POST'])
def gestionar_empleados():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Si es una solicitud POST, se agregará un nuevo empleado
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        cargo = request.form['cargo']
        departamento_id = request.form['departamento_id']
        fecha_contratacion = request.form['fecha_contratacion']

        cursor.execute('''
            INSERT INTO empleados (nombre, apellido, cargo, departamento_id, fecha_contratacion)
            VALUES (?, ?, ?, ?, ?)
        ''', (nombre, apellido, cargo, departamento_id, fecha_contratacion))

        conn.commit()
        return redirect('/gestionar_empleados')

    # Obtener todos los empleados
    cursor.execute('''
        SELECT empleados.id, empleados.nombre, empleados.apellido, empleados.cargo, 
               departamentos.nombre AS departamento, empleados.fecha_contratacion
        FROM empleados
        JOIN departamentos ON empleados.departamento_id = departamentos.id
    ''')
    empleados = cursor.fetchall()
    conn.close()

    # Obtener todos los departamentos para mostrarlos en el formulario de agregar empleado
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM departamentos')
    departamentos = cursor.fetchall()
    conn.close()

    return render_template('gestionar_empleados.html', empleados=empleados, departamentos=departamentos)


# Ruta para editar empleado
@app.route('/editar_empleado/<int:id>', methods=['GET', 'POST'])
def editar_empleado(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        cargo = request.form['cargo']
        departamento_id = request.form['departamento_id']
        fecha_contratacion = request.form['fecha_contratacion']

        cursor.execute('''
            UPDATE empleados
            SET nombre = ?, apellido = ?, cargo = ?, departamento_id = ?, fecha_contratacion = ?
            WHERE id = ?
        ''', (nombre, apellido, cargo, departamento_id, fecha_contratacion, id))

        conn.commit()
        conn.close()
        return redirect('/gestionar_empleados')

    # Obtener los datos del empleado
    cursor.execute('SELECT * FROM empleados WHERE id = ?', (id,))
    empleado = cursor.fetchone()

    # Obtener todos los departamentos
    cursor.execute('SELECT * FROM departamentos')
    departamentos = cursor.fetchall()
    conn.close()

    return render_template('editar_empleado.html', empleado=empleado, departamentos=departamentos)


# Ruta para eliminar empleado
@app.route('/eliminar_empleado/<int:id>')
def eliminar_empleado(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM empleados WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/gestionar_empleados')


@app.route('/gestionar_reportes', methods=['GET', 'POST'])
def gestionar_reportes():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Obtener los departamentos
    cursor.execute("SELECT id, nombre FROM departamentos")
    departamentos = cursor.fetchall()

    empleados = []
    if request.method == 'POST':
        # Obtener el departamento seleccionado
        departamento_id = request.form['departamento_id']
        
        # Obtener los empleados del departamento seleccionado
        cursor.execute('''
        SELECT empleados.id, empleados.nombre, empleados.apellido 
        FROM empleados 
        WHERE empleados.id = ?
        ''', (departamento_id,))
        empleados = cursor.fetchall()

    conn.close()
    return render_template('gestionar_reportes.html', departamentos=departamentos, empleados=empleados)






# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.pop('logged_in', None)  # Eliminar la sesión
    return redirect(url_for('login'))  # Redirigir al login

if __name__ == '__main__':
    app.run(debug=True)
