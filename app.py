from flask import Flask, jsonify, request
import mysql.connector

app = Flask(__name__)

# Configuración de la conexión a la base de datos
db_config = {
    'host': 'autorack.proxy.rlwy.net',
    'user': 'root',
    'password': 'YTIkrpQjPuOCPjLOetrwOnIVpCcphxop',
    'database': 'railway',
    'port': 55698
}

# Ruta para verificar el usuario y la contraseña
@app.route('/verify_user', methods=['POST'])
def verify_user():
    data = request.get_json()
    username = data.get('User')
    password = data.get('Password')

    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Consulta para verificar el usuario y la contraseña
        cursor.execute("SELECT * FROM Users_escaner WHERE User = %s AND Password = %s", (username, password))
        user = cursor.fetchone()

        # Cerrar la conexión
        cursor.close()
        conn.close()

        if user:
            return jsonify({"message": "Credenciales válidas", "user": user}), 200
        else:
            return jsonify({"message": "Credenciales inválidas"}), 401

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

# Ruta para obtener los datos de los usuarios (opcional)
@app.route('/users', methods=['GET'])
def get_users():
    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Consulta para obtener los datos de los usuarios
        cursor.execute("SELECT id, User, Password FROM Users_escaner")
        users = cursor.fetchall()

        # Cerrar la conexión
        cursor.close()
        conn.close()

        # Retornar los datos en formato JSON
        return jsonify(users)

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

if __name__ == '__main__':
    app.run(debug=True)
