# Lógica del sistema de predicciones
from config.config import config
from app import create_app
def main():
    # Inicialización de la aplicación
    app = create_app()

    # Información inicial, mostrada por consola
    print("🚀 Servicio de datos iniciado")
    print("🌐 Url: http://localhost:10000")
    # Ejecución del servidor de la aplicación
    app.run(host='0.0.0.0', port=10000, debug=config['development'])

if __name__ == '__main__':
    main()