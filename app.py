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

# Ruta de inserción con GET
@app.route("/enviar-comprobante", methods=['GET'])
def enviar_comprobante():
    telefono = request.args.get("telefono")
    archivo = request.args.get("comprobante")

    if not telefono:
        return jsonify(success=False, message="No se recibió el teléfono"), 400

    stored_file_name = archivo if archivo else ""  # Guarda un valor vacío si no hay archivo

    try:
        con = mysql.connector.connect(
            host="185.232.14.52",
            database="u760464709_tst_sep",
            user="u760464709_tst_sep_usr",
            password="dJ0CIAFF="
        )
        cursor = con.cursor()

        sql = "INSERT INTO tst0_cursos_pagos (Telefono, Archivo) VALUES (%s, %s)"
        cursor.execute(sql, (telefono, stored_file_name))

        cursor.execute("SELECT * FROM tst0_cursos_pagos ORDER BY Id_Curso_Pago DESC LIMIT 1")
        ultimo_registro = cursor.fetchone()

        con.commit()

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

# Ruta de búsqueda con GET
@app.route('/buscar-comprobante', methods=['GET'])
def buscar_comprobante():
    telefono = request.args.get("telefono")

    if not telefono:
        return jsonify(success=False, message="No se recibió el teléfono"), 400

    try:
        con = mysql.connector.connect(
            host="185.232.14.52",
            database="u760464709_tst_sep",
            user="u760464709_tst_sep_usr",
            password="dJ0CIAFF="
        )
        cursor = con.cursor()

        # Consulta para buscar registros por teléfono
        sql = "SELECT * FROM tst0_cursos_pagos WHERE Telefono = %s"
        cursor.execute(sql, (telefono,))
        resultados = cursor.fetchall()

        con.close()

        # Devuelve los resultados en formato JSON
        data = [
            {'id': row[0], 'telefono': row[1], 'archivo': row[2]}
            for row in resultados
        ]
        return jsonify(success=True, data=data) if data else jsonify(success=False, message="No se encontraron comprobantes")

    except mysql.connector.Error as err:
        print(f"Error en la base de datos: {err}")
        return jsonify(success=False, message="Error al buscar el comprobante"), 500

    finally:
        if con.is_connected():
            cursor.close()
            con.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50001)
    app.run(debug=True)

