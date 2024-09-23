from flask import Flask, render_template, jsonify, request, send_from_directory
from pusher import Pusher
import mysql.connector
import os
import uuid  # Para generar un ID único

app = Flask(__name__)

pusher = Pusher(
    app_id='1767327',
    key='0afe1c275b2ed6dbabd7',
    secret='e48639e9d2748fc8d53e',
    cluster='us2',
    ssl=True
)

# Define el directorio donde se guardarán los archivos
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configurar una ruta para acceder a los archivos subidos
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/')
def index():
    return render_template('index.html') 

@app.route("/about")
def about():
    con = mysql.connector.connect(
        host="185.232.14.52",
        database="u760464709_tst_sep",
        user="u760464709_tst_sep_usr",
        password="dJ0CIAFF="
    )

    if not con.is_connected():
        con.reconnect()
    
    cursor = con.cursor()
    sql = "SELECT * FROM tst0_cursos_pagos"
    cursor.execute(sql)
    data = cursor.fetchall() 
    con.close()

    return render_template("about.html", data=data)

@app.route("/enviar-comprobante", methods=['POST'])
def enviar_comprobante():
    telefono = request.form.get("telefono")
    archivo = request.files.get("comprobante")

    print(f"T: {telefono}")
    print(f"A: {archivo}")

    if archivo is None:
        return jsonify(success=False, message="No se recibió ningún archivo"), 400

    if not telefono:
        return jsonify(success=False, message="No se recibió el teléfono"), 400

    print(f"Nombre del archivo: {archivo.filename}")

    # Guardar el archivo en el servidor
    file_id = str(uuid.uuid4())  # Genera un ID único
    file_name = f"{file_id}_{archivo.filename}"  # Nombre único del archivo
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    archivo.save(file_path)

    # En lugar de la URL, almacena solo el nombre del archivo
    stored_file_name = file_name

    try:
        con = mysql.connector.connect(
            host="185.232.14.52",
            database="u760464709_tst_sep",
            user="u760464709_tst_sep_usr",
            password="dJ0CIAFF="
        )
        cursor = con.cursor()

        sql = "INSERT INTO tst0_cursos_pagos (Telefono, Archivo) VALUES (%s, %s)"
        cursor.execute(sql, (telefono, stored_file_name))  # Almacena solo el nombre del archivo

        cursor.execute("SELECT * FROM tst0_cursos_pagos ORDER BY Id_Curso_Pago DESC LIMIT 1")
        ultimo_registro = cursor.fetchone()

        con.commit()

        print(f"A: {str(ultimo_registro[0])}")


        # Convertir a tipos serializables
        pusher.trigger('my-channel', 'my-event', {
            'id': str(ultimo_registro[0]),
            'telefono': str(ultimo_registro[1]),
            'archivo': str(ultimo_registro[2])
        })

        return jsonify(success=True, message="Comprobante enviado correctamente")

    except mysql.connector.Error as err:
        print(f"Error en la base de datos: {err}")
        return jsonify(success=False, message="Error al procesar el comprobante"), 500

    finally:
        if con.is_connected():
            cursor.close()
            con.close()

@app.route('/nueva-nota')
def nueva_nota():
    pusher.trigger('my-channel', 'my-event', {'message': 'Nueva nota creada'})
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(debug=True)
