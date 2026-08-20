"""
main.py
Punto de entrada del Sistema de Gestión de Biblioteca Escolar.

Inicializa la base de datos SQLite3 (creación de tablas si no existen,
con sus restricciones de integridad) y lanza la interfaz gráfica.
"""

from conexion import ConexionDB
from gui import AplicacionBiblioteca


def main():
    ConexionDB.inicializar_base_datos()
    app = AplicacionBiblioteca()
    app.mainloop()


if __name__ == "__main__":
    main()
