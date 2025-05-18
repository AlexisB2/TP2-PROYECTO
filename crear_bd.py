import sqlite3


def crear_conexion(db_file):
    """
    Crea una conexión a la base de datos SQLite especificada por db_file.
    """
    try:
        conn = sqlite3.connect(db_file)
        print("Conexión establecida a la base de datos:", db_file)
        return conn
    except sqlite3.Error as e:
        print(e)
    return None


def crear_tablas(conn):
    """
    Crea las tablas users, patients, reports y user_history en la base de datos.
    """
    try:
        cursor = conn.cursor()

        # Tabla de usuarios: médicos y administradores
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('medico', 'administrador'))
        );
        ''')

        # Tabla de pacientes: se incluyen los campos del dataset de endometriosis
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,  -- Campo adicional para identificar al paciente
            edad INTEGER NOT NULL,
            etnia INTEGER NOT NULL CHECK(etnia IN (0, 1)),
            dias_menstruacion INTEGER NOT NULL,  -- Rango 3 a 10
            alargue_duracion INTEGER NOT NULL,   -- Rango 0 a 7
            dolores INTEGER NOT NULL CHECK(dolores IN (0, 1)),
            aumento_sangrado INTEGER NOT NULL CHECK(aumento_sangrado IN (0, 1)),
            infertilidad INTEGER NOT NULL CHECK(infertilidad IN (0, 1)),
            dispareunia INTEGER NOT NULL CHECK(dispareunia IN (0, 1)),
            dismenorrea INTEGER NOT NULL CHECK(dismenorrea IN (0, 1)),
            endometriosis INTEGER NOT NULL CHECK(endometriosis IN (0, 1)),
            medico_id INTEGER,  -- Referencia al usuario (médico) que registró el paciente
            FOREIGN KEY(medico_id) REFERENCES users(id)
        );
        ''')

        # Tabla de reportes: cada reporte puede almacenar un diagnóstico y la predicción
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            medico_id INTEGER NOT NULL,
            report_date TEXT DEFAULT (datetime('now','localtime')),
            details TEXT,  -- Detalles o conclusiones del reporte
            predicted_endometriosis INTEGER NOT NULL CHECK(predicted_endometriosis IN (0, 1)),
            FOREIGN KEY(patient_id) REFERENCES patients(id),
            FOREIGN KEY(medico_id) REFERENCES users(id)
        );
        ''')

        # Tabla de historial de acciones de usuarios (opcional, para auditoría)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        ''')

        conn.commit()
        print("Tablas creadas exitosamente.")
    except sqlite3.Error as e:
        print("Error al crear las tablas:", e)


if __name__ == '__main__':
    # Nombre del archivo de la base de datos
    database = "endometriosis_app.db"
    conn = crear_conexion(database)

    if conn is not None:
        crear_tablas(conn)
        conn.close()
    else:
        print("No se pudo establecer la conexión a la base de datos.")
