from flask import Flask, render_template, jsonify
from pusher import Pusher

app = Flask(__name__)

# Configura Pusher
pusher = Pusher(
    app_id='1767327',
    key='0afe1c275b2ed6dbabd7',
    secret='e48639e9d2748fc8d53e',
    cluster='us2',
    ssl=True
)

@app.route('/')
def index():
    return render_template('index.html')  # Corregido: quitado 'templates/'

@app.route('/nueva-nota', methods=['POST'])
def nueva_nota():
    # Aquí puedes manejar la lógica para crear una nueva nota
    # Por ejemplo, guardar en una base de datos

    # Luego, envía un evento a través de Pusher
    pusher.trigger('my-channel', 'my-event', {'message': 'Nueva nota creada'})

    return jsonify(success=True)

if __name__ == '__main__':
    app.run(debug=True)
