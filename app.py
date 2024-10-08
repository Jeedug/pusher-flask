from flask import Flask, render_template, jsonify, request, send_from_directory
from pusher import Pusher
import mysql.connector
import os
import uuid  # Para generar un ID único
import json

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

@app.route("/")
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

    return render_template("index.html", data=data)

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
            'archivo': str(ultimo_registro[2]),
            'action': "insert"
        })

        return jsonify(success=True, message="Comprobante enviado correctamente")

    except mysql.connector.Error as err:
        print(f"Error en la base de datos: {err}")
        return jsonify(success=False, message="Error al procesar el comprobante"), 500

    finally:
        if con.is_connected():
            cursor.close()
            con.close()

@app.route('/actualizar-comprobante', methods=['POST'])
def actualizar_comprobante():
    # Obtiene los datos enviados como FormData
    id_comprobante = request.form.get('id_comprobante')  # Obtiene el ID enviado
    telefono = request.form.get('telefono')  # Obtiene el teléfono enviado
    archivo = request.files.get('comprobante')  # Obtiene el archivo si se envió

    # Validación de los campos requeridos
    if not id_comprobante:
        return jsonify(success=False, message="No se recibió el ID"), 400
    if not telefono:
        return jsonify(success=False, message="No se recibió el teléfono"), 400

    # Guardar el nuevo archivo en el servidor, si se proporciona uno
    stored_file_name = None
    if archivo:
        file_id = str(uuid.uuid4())  # Genera un ID único
        file_name = f"{file_id}_{archivo.filename}"  # Nombre único del archivo
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        archivo.save(file_path)
        stored_file_name = file_name

    try:
        con = mysql.connector.connect(
            host="185.232.14.52",
            database="u760464709_tst_sep",
            user="u760464709_tst_sep_usr",
            password="dJ0CIAFF="
        )
        cursor = con.cursor()

        # Actualiza el registro solo si hay un nuevo archivo
        if stored_file_name:
            sql = "UPDATE tst0_cursos_pagos SET Telefono = %s, Archivo = %s WHERE Id_Curso_Pago = %s"
            cursor.execute(sql, (telefono, stored_file_name, id_comprobante))
        else:
            sql = "UPDATE tst0_cursos_pagos SET Telefono = %s WHERE Id_Curso_Pago = %s"
            cursor.execute(sql, (telefono, id_comprobante))

        con.commit()

        # Obtener el registro actualizado para enviar por Pusher
        cursor.execute("SELECT * FROM tst0_cursos_pagos WHERE Id_Curso_Pago = %s", (id_comprobante,))
        updated_record = cursor.fetchone()

        # Convertir a tipos serializables y enviar a Pusher
        pusher.trigger('my-channel', 'my-event', {
            'id': str(updated_record[0]),
            'telefono': str(updated_record[1]),
            'archivo': str(updated_record[2]),
            'action': "update"
        })

        return jsonify(success=True, message="Comprobante actualizado correctamente")

    except mysql.connector.Error as err:
        print(f"Error en la base de datos: {err}")
        return jsonify(success=False, message="Error al actualizar el comprobante"), 500

    finally:
        if con.is_connected():
            cursor.close()
            con.close()

@app.route('/eliminar-comprobante', methods=['GET'])
def eliminar_comprobante():
    
    id_comprobante = request.args.get("id_comprobante")

    if not id_comprobante:
        return jsonify(success=False, message="No se recibió el ID"), 400

    try:
        con = mysql.connector.connect(
            host="185.232.14.52",
            database="u760464709_tst_sep",
            user="u760464709_tst_sep_usr",
            password="dJ0CIAFF="
        )
        cursor = con.cursor()

        # Eliminar el registro de la base de datos
        sql = "DELETE FROM tst0_cursos_pagos WHERE Id_Curso_Pago = %s"
        cursor.execute(sql, (id_comprobante,))
        con.commit()

        # Notificar a Pusher sobre la eliminación
        pusher.trigger('my-channel', 'my-event', {
            'id': id_comprobante,
            'action': "delete"
        })

        return jsonify(success=True, message="Comprobante eliminado correctamente")

    except mysql.connector.Error as err:
        print(f"Error en la base de datos: {err}")
        return jsonify(success=False, message="Error al eliminar el comprobante"), 500

    finally:
        if con.is_connected():
            cursor.close()
            con.close()



@app.route('/nueva-nota')
def nueva_nota():
    pusher.trigger('my-channel', 'my-event', {'message': 'Nueva nota creada'})
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50001)
    app.run(debug=True)
