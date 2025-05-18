import pandas as pd
import sqlite3
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib


def import_excel_to_db(excel_file, db_file):
    """
    Lee el archivo Excel con los datos y los inserta en la tabla 'patients' de la base de datos.
    """
    try:
        # Leer el archivo Excel
        data = pd.read_excel(excel_file)

        # Renombrar columnas para que coincidan con los nombres de la tabla en la base de datos
        data.rename(columns={
            'Edad': 'edad',
            'Etnia': 'etnia',
            'Dias de Menstruacion': 'dias_menstruacion',
            'Alargue de Duracion de Menstruacion': 'alargue_duracion',
            'Dolores': 'dolores',
            'Aumento de Sangrado': 'aumento_sangrado',
            'Infertilidad': 'infertilidad',
            'Dispareunia': 'dispareunia',
            'Dismenorrea': 'dismenorrea',
            'Endometriosis': 'endometriosis'
        }, inplace=True)

        # Conectar a la base de datos
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Insertar cada fila en la tabla patients
        for index, row in data.iterrows():
            # Se asigna un nombre genérico para el paciente
            nombre = f"Paciente_{index}"

            query = """
            INSERT INTO patients (
                nombre, edad, etnia, dias_menstruacion, alargue_duracion, 
                dolores, aumento_sangrado, infertilidad, dispareunia, dismenorrea, endometriosis
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            values = (
                nombre,
                int(row['edad']),
                int(row['etnia']),
                int(row['dias_menstruacion']),
                int(row['alargue_duracion']),
                int(row['dolores']),
                int(row['aumento_sangrado']),
                int(row['infertilidad']),
                int(row['dispareunia']),
                int(row['dismenorrea']),
                int(row['endometriosis'])
            )
            cursor.execute(query, values)

        conn.commit()
        conn.close()
        print("Datos importados exitosamente a la base de datos.")

    except Exception as e:
        print("Error al importar los datos:", e)


def train_random_forest_model(db_file, model_file='random_forest_model.pkl'):
    """
    Extrae los datos de la tabla 'patients', entrena un clasificador Random Forest para predecir
    la variable 'endometriosis' y guarda el modelo entrenado en un archivo.
    """
    try:
        # Conectar a la base de datos y extraer los datos
        conn = sqlite3.connect(db_file)
        query = """
        SELECT 
            edad, etnia, dias_menstruacion, alargue_duracion, 
            dolores, aumento_sangrado, infertilidad, dispareunia, dismenorrea, endometriosis 
        FROM patients
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        # Separar las características (X) y la etiqueta (y)
        X = df.drop(columns=['endometriosis'])
        y = df['endometriosis']

        # Dividir el conjunto de datos en entrenamiento y prueba
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Crear y entrenar el clasificador Random Forest
        clf = RandomForestClassifier(random_state=42)
        clf.fit(X_train, y_train)

        # Evaluar el modelo
        y_pred = clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Accuracy del modelo en el conjunto de prueba: {accuracy:.2f}")

        # Guardar el modelo entrenado en un archivo
        joblib.dump(clf, model_file)
        print(f"Modelo entrenado guardado en '{model_file}'.")

    except Exception as e:
        print("Error al entrenar el modelo:", e)


if __name__ == "__main__":
    # Rutas de los archivos: ajusta estas rutas según la ubicación de tus archivos
    excel_file = "Endometriosis_Patients_Dataset.xlsx"
    db_file = "endometriosis_app.db"

    # 1. Importar los datos del Excel a la base de datos
    import_excel_to_db(excel_file, db_file)

    # 2. Entrenar el modelo Random Forest con los datos importados
    train_random_forest_model(db_file)
