from flask import Flask, render_template, request, redirect, session, send_from_directory, url_for
import mysql.connector
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename





app = Flask(__name__)
app.secret_key = 'clave_secreta'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')


#la vuelta esa del email

# Conexión a la base de datos con XAMPP
def conectar_db():
    return mysql.connector.connect(
        host="centerbeam.proxy.rlwy.net",
        user="root",
        password="IWYFWwjaMTNNChejrLNgdQUkfBHEASir",
        database="railway",
        port = "25323"
    )

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    db = conectar_db()
    cursor = db.cursor(dictionary=True)
    
    # Obtener todas las categorías
    cursor.execute("SELECT * FROM categorias")
    categorias = cursor.fetchall()

    categoria_id = request.args.get('categoria_id') 
    if categoria_id:
       
        # Filtrar recetas por categoría
        cursor.execute("""
            SELECT recetas.*, categorias.nombre AS categoria_nombre
            FROM recetas
            JOIN categorias ON recetas.categoria_id = categorias.id
            WHERE recetas.categoria_id = %s
        """, (categoria_id,))
    else:
        # Obtener todas las recetas
        cursor.execute("""
            SELECT recetas.*, categorias.nombre AS categoria_nombre
            FROM recetas
            JOIN categorias ON recetas.categoria_id = categorias.id
        """)
    
    recetas = cursor.fetchall()

    # Insertar una nueva receta con metodo post
    if request.method == 'POST':
        titulo = request.form['titulo']
        ingredientes = request.form['ingredientes']
        pasos = request.form['pasos']
        categoria_id = int(request.form['categoria_id'])
        usuario_id = session['usuario_id']

        # Manejo de la imagen
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                imagen = filename 

                # Insertar la receta con la imagen
                cursor.execute("""
                    INSERT INTO recetas (titulo, ingredientes, pasos, categoria_id, usuario_id, imagen)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (titulo, ingredientes, pasos, categoria_id, usuario_id, imagen))
                db.commit()
    
    db.close()
    
    return render_template('index.html', recetas=recetas, categorias=categorias)




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            db = conectar_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            usuario = cursor.fetchone()
            db.close()

            if usuario and check_password_hash(usuario['password'], password):
                session['usuario_id'] = usuario['id']
                session['usuario'] = usuario['nombre']
                return redirect('/dashboard')

            return render_template('login.html', error="Credenciales inválidas")
        
        except Exception as e:
            return f"Ocurrió un error en el servidor: {str(e)}"

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        db = conectar_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)",
                       (nombre, email, password))
        db.commit()
        db.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect('/login')

    db = conectar_db()
    cursor = db.cursor(dictionary=True)

    # Obtener recetas del usuario
    cursor.execute("SELECT * FROM recetas WHERE usuario_id = %s", (session['usuario_id'],))
    recetas = cursor.fetchall()

    # Obtener datos del usuario
    cursor.execute("SELECT nombre, email FROM usuarios WHERE id = %s", (session['usuario_id'],))
    usuario = cursor.fetchone()

    db.close()

    return render_template(
        'dashboard.html',
        recetas=recetas,
        nombre_usuario=usuario['nombre'],
        email=usuario['email']
    )

@app.route('/perfil')
def perfil():
    if 'usuario_id' not in session:
        return redirect('/login')
    db = conectar_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (session['usuario_id'],))
    usuario = cursor.fetchone()
    db.close()
    return render_template('perfil.html', usuario=usuario)

@app.route('/perfil')
def perfil_usuario():
    if 'usuario_id' not in session:
        return redirect('/login')
    db = conectar_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (session['usuario_id'],))
    usuario = cursor.fetchone()
    db.close()
    return render_template('perfil.html', usuarios=usuario)




@app.route('/publicar', methods=['GET', 'POST'])
def publicar():
    if 'usuario_id' not in session:
        return redirect('/login')

    db = conectar_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM categorias")
    categorias = cursor.fetchall()

    if request.method == 'POST':
        titulo = request.form['titulo']
        ingredientes = request.form['ingredientes']
        pasos = request.form['pasos']
        categoria_id = int(request.form['categoria'])
        usuario_id = session['usuario_id']

        # Manejo de la imagen
        imagen = None
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_path = os.path.join('static/uploads', filename)
                file.save(upload_path)
                
                imagen = filename 

        # Insertar la receta en la base de datos
        cursor.execute("""
            INSERT INTO recetas (titulo, ingredientes, pasos, categoria_id, usuario_id, imagen)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (titulo, ingredientes, pasos, categoria_id, usuario_id, imagen))
        db.commit()
        db.close()
        return redirect('/dashboard')

    db.close()
    return render_template('publicar.html', categorias=categorias)



@app.route('/mis_recetas')
def mis_recetas():
    if 'usuario_id' not in session:
        return redirect('/login') 
    
    db = conectar_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM recetas WHERE usuario_id = %s", (session['usuario_id'],))
    recetas = cursor.fetchall()
    db.close()
    
    return render_template('mis_recetas.html', recetas=recetas)

@app.route('/receta/<int:receta_id>')
def detalle_receta(receta_id):
    db = conectar_db()
    cursor = db.cursor(dictionary=True)

    # Obtener receta
    cursor.execute("SELECT * FROM recetas WHERE id = %s", (receta_id,))
    receta = cursor.fetchone()
    if receta is None:
        db.close()
        return "Receta no encontrada", 404

    # Obtener autor de la receta
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (receta['usuario_id'],))
    autor = cursor.fetchone()

    # Obtener comentarios con nombres de usuario
    cursor.execute("""
        SELECT c.contenido, c.calificacion, u.nombre AS usuario_nombre
        FROM comentarios c
        JOIN usuarios u ON c.usuario_id = u.id
        WHERE c.receta_id = %s
        ORDER BY c.fecha DESC
    """, (receta_id,))
    comentarios = cursor.fetchall()

    # Verificar si es favorita (solo si el usuario está logueado)
    es_favorita = False
    if 'usuario_id' in session:
        cursor.execute("""
            SELECT 1 FROM favoritos
            WHERE usuario_id = %s AND receta_id = %s
        """, (session['usuario_id'], receta_id))
        es_favorita = cursor.fetchone() is not None

    db.close()
    return render_template('detalle_receta.html', receta=receta, autor=autor, comentarios=comentarios, es_favorita=es_favorita)


@app.route('/estadisticas')
def estadisticas():
    return render_template('estadisticas.html')

@app.route('/buscar')
def buscar():
    consulta = request.args.get('q', '')
    db = conectar_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT r.*, c.nombre AS categoria_nombre
        FROM recetas r
        JOIN categorias c ON r.categoria_id = c.id
        WHERE r.titulo LIKE %s OR r.ingredientes LIKE %s OR r.pasos LIKE %s
    """, (f"%{consulta}%", f"%{consulta}%", f"%{consulta}%"))
    
    recetas = cursor.fetchall()
    db.close()
    
    return render_template('buscar_resultados.html', recetas=recetas, consulta=consulta)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/comentario/<int:receta_id>', methods=['POST'])
def agregar_comentario(receta_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    contenido = request.form['contenido']
    calificacion = int(request.form['calificacion'])
    usuario_id = session['usuario_id']

    db = conectar_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO comentarios (usuario_id, receta_id, contenido, calificacion)
        VALUES (%s, %s, %s, %s)
    """, (usuario_id, receta_id, contenido, calificacion))
    db.commit()
    db.close()

    return redirect(url_for('detalle_receta', receta_id=receta_id))

@app.route('/toggle_favorito/<int:receta_id>', methods=['POST'])
def toggle_favorito(receta_id):
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 403

    usuario_id = session['usuario_id']
    db = conectar_db()
    cursor = db.cursor()

    cursor.execute("SELECT id FROM favoritos WHERE usuario_id = %s AND receta_id = %s", (usuario_id, receta_id))
    favorito = cursor.fetchone()

    try:
        if favorito:
            cursor.execute("DELETE FROM favoritos WHERE usuario_id = %s AND receta_id = %s", (usuario_id, receta_id))
            db.commit()
            estado = 'removido'
        else:
            cursor.execute("INSERT INTO favoritos (usuario_id, receta_id) VALUES (%s, %s)", (usuario_id, receta_id))
            db.commit()
            estado = 'agregado'
             
    except Exception as e:
        db.rollback()
        print("Error:", e)
        return jsonify({'error': 'Error interno'}), 500
    finally:
        db.close()

    return jsonify({'estado': estado})


@app.route('/favoritos')
def ver_favoritos():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    db = conectar_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT r.*
        FROM recetas r
        JOIN favoritos f ON r.id = f.receta_id
        WHERE f.usuario_id = %s
        ORDER BY f.id DESC
    """, (session['usuario_id'],))

    recetas_favoritas = cursor.fetchall()
    db.close()

    return render_template('favoritos.html', recetas=recetas_favoritas)

@app.route('/seguir/<int:seguido_id>', methods=['POST'])
def seguir_usuario(seguido_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    seguidor_id = session['usuario_id']
    if seguidor_id == seguido_id:
        return "No puedes seguirte a ti mismo", 400

    db = conectar_db()
    cursor = db.cursor()

    # Insertar solo si no existe ya
    try:
        cursor.execute("""
            INSERT INTO seguimientos (seguidor_id, seguido_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE fecha = CURRENT_TIMESTAMP
        """, (seguidor_id, seguido_id))
        db.commit()
        
    except Exception as e:
        db.rollback()
        return f"Error al seguir: {e}", 500
    finally:
        db.close()

    return redirect(request.referrer or url_for('dashboard'))


@app.route('/dejar_de_seguir/<int:seguido_id>', methods=['POST'])
def dejar_de_seguir(seguido_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    seguidor_id = session['usuario_id']

    db = conectar_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            DELETE FROM seguimientos WHERE seguidor_id = %s AND seguido_id = %s
        """, (seguidor_id, seguido_id))
        db.commit()
    except Exception as e:
        db.rollback()
        return f"Error al dejar de seguir: {e}", 500
    finally:
        db.close()

    return redirect(request.referrer or url_for('dashboard'))

@app.route('/usuario/<int:usuario_id>')
def ver_perfil(usuario_id):
    db = conectar_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
    usuario = cursor.fetchone()

    if usuario is None:
        db.close()
        return "Usuario no encontrado", 404

    es_seguido = False
    if 'usuario_id' in session:
        cursor.execute("""
            SELECT 1 FROM seguimientos
            WHERE seguidor_id = %s AND seguido_id = %s
        """, (session['usuario_id'], usuario_id))
        es_seguido = cursor.fetchone() is not None

    db.close()
    return render_template('perfil.html', usuario=usuario, es_seguido=es_seguido)


@app.route('/editar_receta/<int:receta_id>', methods=['GET', 'POST'])
def editar_receta(receta_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    db = conectar_db()
    cursor = db.cursor(dictionary=True)

    # Obtener la receta
    cursor.execute("SELECT * FROM recetas WHERE id = %s", (receta_id,))
    receta = cursor.fetchone()

    if receta is None or receta['usuario_id'] != session['usuario_id']:
        db.close()
        return "No tienes permiso para editar esta receta", 403

    if request.method == 'POST':
        try:
            titulo = request.form['titulo']
            ingredientes = request.form['ingredientes']
            pasos = request.form['pasos']

            cursor.execute("""
                UPDATE recetas
                SET titulo = %s, ingredientes = %s, pasos = %s
                WHERE id = %s
            """, (titulo, ingredientes, pasos, receta_id))

            db.commit()
            db.close()
            return redirect(url_for('detalle_receta', receta_id=receta_id))

        except Exception as e:
            db.close()
            return f"Error al actualizar la receta: {str(e)}", 500

    db.close()
    return render_template('editar_receta.html', receta=receta)






if __name__ == '__main__':
    app.run(debug=True)
