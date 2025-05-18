import pickle

from flask import Flask, request, jsonify, render_template, g, session, redirect
import sqlite3
from functools import wraps
import joblib

app = Flask(__name__)
app.secret_key = 'clave_super_secreta_123'

DATABASE = 'endometriosis_app.db'
model = joblib.load('random_forest_model.pkl')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Authorization header missing'}), 401
        try:
            token = token.split("Bearer ")[1]
        except:
            return jsonify({'message': 'Token format invalid'}), 401
        g.current_user = token  # 👈 Aquí se almacena el username
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
    conn.close()
    if user:
        session['username'] = username
        session['user_id'] = user['id']            # 🔹 Esto faltaba
        session['rol'] = user['role']
        return jsonify({
            'message': 'Inicio de sesión exitoso',
            'token': username,
            'role': user['role']
        })
    return jsonify({'message': 'Credenciales inválidas'}), 401



@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('/')


def predict_endometriosis(data):
    features = [[
        data["edad"], data["etnia"], data["dias_menstruacion"], data["alargue_duracion"],
        data["dolores"], data["aumento_sangrado"], data["infertilidad"],
        data["dispareunia"], data["dismenorrea"]
    ]]
    return int(model.predict(features)[0])



@app.route('/add_patient', methods=['POST'])
@token_required  # si estás usando autenticación
def add_patient():
    data = request.get_json()

    nombre = data.get("nombre")
    edad = data.get("edad")
    etnia = data.get("etnia")
    dias_menstruacion = data.get("dias_menstruacion")
    alargue_duracion = data.get("alargue_duracion")
    dolores = data.get("dolores")
    aumento_sangrado = data.get("aumento_sangrado")
    infertilidad = data.get("infertilidad")
    dispareunia = data.get("dispareunia")
    dismenorrea = data.get("dismenorrea")
    endometriosis = predict_endometriosis(data)  # usa tu modelo RF aquí

    medico_id = session['user_id']  # asumiendo que ya lo tienes en sesión

    conn = sqlite3.connect("endometriosis_app.db")
    conn.execute("""
        INSERT INTO patients (nombre, edad, etnia, dias_menstruacion, alargue_duracion,
        dolores, aumento_sangrado, infertilidad, dispareunia, dismenorrea, endometriosis, medico_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (nombre, edad, etnia, dias_menstruacion, alargue_duracion, dolores,
          aumento_sangrado, infertilidad, dispareunia, dismenorrea, endometriosis, medico_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Paciente registrado correctamente"}), 201


@app.route('/patients')
@token_required
def get_all_patients():
    conn = get_db_connection()
    patients = conn.execute('SELECT * FROM patients ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify({'patients': [dict(row) for row in patients]})

@app.route('/patients/<int:patient_id>', methods=['GET'])
@token_required
def get_patient(patient_id):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({'message': 'Paciente no encontrado'}), 404

@app.route('/patients/<int:patient_id>', methods=['PUT'])
@token_required
def update_patient(patient_id):
    data = request.get_json()
    try:
        features = [[
            int(data['edad']), int(data['etnia']), int(data['dias_menstruacion']),
            int(data['alargue_duracion']), int(data['dolores']), int(data['aumento_sangrado']),
            int(data['infertilidad']), int(data['dispareunia']), int(data['dismenorrea'])
        ]]
        prediction = model.predict(features)
        endometriosis_pred = int(prediction[0])
        conn = get_db_connection()
        conn.execute('''
            UPDATE patients SET
                nombre=?, edad=?, etnia=?, dias_menstruacion=?, alargue_duracion=?,
                dolores=?, aumento_sangrado=?, infertilidad=?, dispareunia=?, dismenorrea=?, endometriosis=?
            WHERE id=?
        ''', (
            data['nombre'], data['edad'], data['etnia'], data['dias_menstruacion'],
            data['alargue_duracion'], data['dolores'], data['aumento_sangrado'],
            data['infertilidad'], data['dispareunia'], data['dismenorrea'],
            endometriosis_pred, patient_id
        ))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Paciente actualizado correctamente'})
    except Exception as e:
        return jsonify({'message': 'Error al actualizar paciente'}), 500

@app.route('/patients/<int:patient_id>', methods=['DELETE'])
@token_required
def delete_patient(patient_id):
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM patients WHERE id = ?', (patient_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Paciente eliminado correctamente'})
    except Exception as e:
        return jsonify({'message': 'Error al eliminar paciente'}), 500

@app.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(user_id):
    conn = get_db_connection()
    user_data = conn.execute("SELECT role FROM users WHERE username = ?", (g.current_user,)).fetchone()
    if not user_data or user_data['role'] != 'administrador':
        conn.close()
        return jsonify({'message': 'No autorizado'}), 403

    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Usuario eliminado correctamente'})


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    role = data['role']
    if not username or not password or not role:
        return jsonify({'message': 'Todos los campos son obligatorios'}), 400
    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'message': 'El usuario ya existe'}), 409
    conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, role))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Usuario registrado correctamente'}), 201

@app.route('/patients_page')
def patients_page():
    rol = session.get('rol')
    return render_template('patients.html', rol=rol)

@app.route('/add_patient_page')
def add_patient_page():
    return render_template('add_patient.html')

@app.route('/edit_patient_page')
def edit_patient_page():
    return render_template('edit_patient.html')

@app.route('/register_page')
def register_page():
    return render_template('register.html')


@app.route('/users_page')
@token_required
def users_page():
    conn = get_db_connection()
    user_data = conn.execute("SELECT * FROM users WHERE username = ?", (g.current_user,)).fetchone()
    conn.close()
    if not user_data or user_data['role'] != 'administrador':
        return redirect('/')
    return render_template('users.html')

@app.route('/get_users', methods=['GET'])
def get_users():
    conn = sqlite3.connect('endometriosis_app.db')
    conn.row_factory = sqlite3.Row
    users = conn.execute("SELECT id, username, role FROM users WHERE role = 'medico'").fetchall()
    conn.close()
    return jsonify({'users': [dict(u) for u in users]})



if __name__ == '__main__':
    app.run(debug=True)




