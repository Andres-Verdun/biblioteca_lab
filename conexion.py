"""
conexion.py
Módulo encargado de la gestión centralizada de la conexión a la base de datos SQLite3.

Aplica el principio de responsabilidad única: esta clase sólo se ocupa de
abrir, cerrar y preparar la base de datos (creación de tablas y restricciones
de integridad). Ninguna otra parte del sistema debe abrir conexiones por su
cuenta: todas las clases DAO utilizan ConexionDB.conectar() / ConexionDB.cerrar().
"""

import sqlite3
import os

NOMBRE_BASE_DATOS = "biblioteca.db"


class ConexionDB:
    """
    Clase responsable de gestionar la conexión a la base de datos SQLite3
    de forma centralizada y segura.

    La base de datos se guarda como un único archivo (biblioteca.db) en la
    misma carpeta del programa. Esto permite la portabilidad de los datos:
    copiando ese archivo a otra máquina que tenga el sistema instalado, toda
    la información (libros, estudiantes, docentes y préstamos) viaja con él.
    """

    _ruta_base_datos = os.path.join(os.path.dirname(os.path.abspath(__file__)), NOMBRE_BASE_DATOS)

    @classmethod
    def obtener_ruta(cls):
        """Devuelve la ruta absoluta del archivo de base de datos."""
        return cls._ruta_base_datos

    @classmethod
    def conectar(cls):
        """
        Abre y devuelve una nueva conexión a la base de datos.
        Habilita el uso de claves foráneas (deshabilitadas por defecto en
        SQLite3) y configura row_factory para acceder a las columnas por nombre.
        """
        conexion = sqlite3.connect(cls._ruta_base_datos)
        conexion.execute("PRAGMA foreign_keys = ON;")
        conexion.row_factory = sqlite3.Row
        return conexion

    @classmethod
    def cerrar(cls, conexion):
        """Cierra de forma segura una conexión abierta."""
        if conexion:
            conexion.close()

    @classmethod
    def inicializar_base_datos(cls):
        """
        Crea las tablas del sistema si no existen, aplicando las restricciones
        de integridad correspondientes: PRIMARY KEY, FOREIGN KEY, NOT NULL,
        UNIQUE y CHECK.
        """
        conexion = cls.conectar()
        cursor = conexion.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS libros (
                id_libro INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                autor TEXT NOT NULL,
                editorial TEXT,
                isbn TEXT UNIQUE,
                genero TEXT NOT NULL,
                edad_recomendada TEXT,
                ciclo TEXT NOT NULL,
                stock INTEGER NOT NULL CHECK (stock >= 0),
                disponibles INTEGER NOT NULL CHECK (disponibles >= 0)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS estudiantes (
                id_estudiante INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                grado TEXT NOT NULL,
                dni TEXT NOT NULL UNIQUE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS docentes (
                id_docente INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                area TEXT,
                dni TEXT NOT NULL UNIQUE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prestamos (
                id_prestamo INTEGER PRIMARY KEY AUTOINCREMENT,
                id_libro INTEGER NOT NULL,
                tipo_solicitante TEXT NOT NULL CHECK (tipo_solicitante IN ('Estudiante', 'Docente')),
                id_solicitante INTEGER NOT NULL,
                fecha_prestamo TEXT NOT NULL,
                fecha_devolucion_estimada TEXT NOT NULL,
                fecha_devolucion_real TEXT,
                estado TEXT NOT NULL CHECK (estado IN ('Prestado', 'Devuelto', 'Atrasado')),
                FOREIGN KEY (id_libro) REFERENCES libros(id_libro) ON DELETE CASCADE
            );
        """)

        conexion.commit()
        cls._migrar_edad_recomendada_opcional(conexion)
        cls.cerrar(conexion)

    @classmethod
    def _migrar_edad_recomendada_opcional(cls, conexion):
        """
        Migra bases de datos generadas con una versión anterior del sistema,
        en la que 'edad_recomendada' era obligatoria (NOT NULL), para permitir
        dejarla en blanco. SQLite no permite modificar la restricción de una
        columna existente, así que se reconstruye la tabla sólo si hace falta.
        """
        columnas = conexion.execute("PRAGMA table_info(libros)").fetchall()
        columna_edad = next((c for c in columnas if c["name"] == "edad_recomendada"), None)
        if not columna_edad or columna_edad["notnull"] == 0:
            return  # ya está en la versión correcta (o la tabla se acaba de crear)

        cursor = conexion.cursor()
        cursor.execute("""
            CREATE TABLE libros_nueva (
                id_libro INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                autor TEXT NOT NULL,
                editorial TEXT,
                isbn TEXT UNIQUE,
                genero TEXT NOT NULL,
                edad_recomendada TEXT,
                ciclo TEXT NOT NULL,
                stock INTEGER NOT NULL CHECK (stock >= 0),
                disponibles INTEGER NOT NULL CHECK (disponibles >= 0)
            );
        """)
        cursor.execute("""
            INSERT INTO libros_nueva
                (id_libro, titulo, autor, editorial, isbn, genero, edad_recomendada, ciclo, stock, disponibles)
            SELECT id_libro, titulo, autor, editorial, isbn, genero, edad_recomendada, ciclo, stock, disponibles
            FROM libros;
        """)
        cursor.execute("DROP TABLE libros;")
        cursor.execute("ALTER TABLE libros_nueva RENAME TO libros;")
        conexion.commit()
