from flask import Flask, request, jsonify
import psycopg2
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

def get_db_connection():
    conn = psycopg2.connect(host='192.168.50.223',
                            database='cotizacion-prestamo',
                            user='postgres',
                            password='postgres')
    return conn


@app.route('/registrarUsuario/', methods=['POST'])
@cross_origin()
def register_user():
    conn = get_db_connection()
    cur = conn.cursor()
    body = request.get_json()
    apellido_paterno = body['apellido_paterno']
    apellido_materno = body['apellido_materno']
    nombres = body['nombres']
    usuario = body['usuario']
    contrasena = body['contrasena']
    rfc = body['rfc']
    edad = body['edad']
    telefono = body['telefono']
    correo = body['correo']
    cur.execute(
                'INSERT INTO public.clientes'
                '(apellido_paterno, apellido_materno, nombres, usuario, contrasena, rfc, edad, fecha_alta, telefono, correo) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, %s, %s);',
                (apellido_paterno, apellido_materno, nombres, usuario, contrasena, rfc, edad, telefono, correo))
    conn.commit()
    cur.close()
    conn.close()
    data_inserted = {
        "apellido_paterno": apellido_paterno,
        "apellido_materno": apellido_materno,
        "nombres": nombres,
        "usuario": usuario,
        "contrasena": contrasena,
        "rfc": rfc,
        "edad": edad,
        "telefono": telefono,
        "correo": correo,
    }

    return jsonify({"response": "Usuario registrado exitosamente", "data": data_inserted}), 201

@app.route('/iniciarSesion/', methods=['POST'])
@cross_origin()
def logIn():
    conn = get_db_connection()
    cur = conn.cursor()
    body = request.get_json()
    user = body['usuario']
    password = body['contrasena']
    cur.execute('SELECT * FROM clientes WHERE usuario = %s',
                (str(user),))
    user_recovered = cur.fetchone()
    if password == user_recovered[5]:
        user_data = {
            'id_cliente': int(user_recovered[0]),
            'apellido_paterno': user_recovered[1],
            'apellido_materno': user_recovered[2],
            'nombres': user_recovered[3],
            'usuario': user_recovered[4],
            'rfc': user_recovered[6],
            'edad': int(user_recovered[7]),
            'fecha_alta': user_recovered[8],
            'telefono': int(user_recovered[9]),
            'correo': user_recovered[10]
        }
        return jsonify({'response': 'Usuario autenticado exitosamente', 'data': user_data}), 200
    else:
        return jsonify({'response': 'Error al iniciar sesión: contraseña incorrecta'}), 400

@app.route('/crearCotizacion/', methods=['POST'])
@cross_origin()
def create_price():
    conn = get_db_connection()
    cur = conn.cursor()
    body = request.get_json()
    prestamista = body['prestamista']
    print(prestamista)
    cur.execute('SELECT * FROM prestamistas WHERE nombre = %s',
                (prestamista,))
    bank = cur.fetchone()
    print(bank)
    tipo_prestamo = body['tipo_prestamo']
    r = float(bank[2]) / 12 / 100
    n = float(body['anios']) * 12
    pmt = None
    p = None
    if tipo_prestamo == 'Total':
        p = float(body['prestamo'])
        pmt = (p*r*pow((1+r), n))/(pow((1+r), n)-1)
    elif tipo_prestamo == 'Sueldo':
        pmt = float(body['sueldo_mensual']) * 0.4
        p = (pmt*(pow((1+r), n)-1))/(r*(pow((1+r), n)))
    data_price = {
        "nombre_prestamo": body["nombre"],
        "mensualidad": pmt,
        "interes_mensual": r*100,
        "meses_a_pagar": int(n),
        "total_a_pagar": pmt*n+(p * 1+(float(bank[3]/100))),
        "tipo_prestamo": tipo_prestamo,
        "id_prestamista": int(bank[0])
    }

    return jsonify({"response": "Cotización calculada exitosamente", "data": data_price}), 201

@app.route('/guardarCotizacion/<usuario>/', methods=['POST'])
@cross_origin()
def save_price(usuario):
    conn = get_db_connection()
    cur = conn.cursor()
    data = request.get_json()
    cur.execute('INSERT INTO public.cotizaciones('
	            'nombre_prestamo, mensualidad, interes_mensual, meses_a_pagar, total_a_pagar, tipo_prestamo, id_cliente, id_prestamista) '
	            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s);',
                (data['nombre_prestamo'], data['mensualidad'], data['interes_mensual'], data['meses_a_pagar'], data['total_a_pagar'], data['tipo_prestamo'], usuario, data['id_prestamista']))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"response": "Cotización registrada exitosamente", "data": data}), 201

@app.route("/verCotizaciones/<usuario>/", methods=['GET'])
@cross_origin()
def getPrices(usuario):
    conn = get_db_connection()
    cur = conn.cursor()
    if not int(usuario) == 1:
        cur.execute('SELECT * FROM cotizaciones WHERE id_cliente = %s',
                    (int(usuario),))
    else:
        cur.execute('SELECT * FROM cotizaciones')
    prices = cur.fetchall()
    prices_list = []
    for price in prices:
        cur.execute('SELECT nombre FROM prestamistas WHERE id_prestamistas = %s',
                    (price[8],))
        bank = cur.fetchone()
        price_object = {
            'id_cotizacion': price[0],
            'nombre_prestamo': price[1],
            'mensualidad': price[2],
            'interes_mensual': price[3],
            'meses_a_pagar': price[4],
            'total_a_pagar': price[5],
            'tipo_prestamo': price[6],
            'prestamista': bank[0]
        }
        prices_list.append(price_object)
    cur.close()
    conn.close()

    return jsonify({"response": "Cotizaciones retornadas exitosamente", "data": prices_list}), 201

if __name__ == '__main__':
    app.run(host='25.57.211.155', port=5000, debug=True)