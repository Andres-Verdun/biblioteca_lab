"""
dao.py
Capa de acceso a datos (DAO - Data Access Object).

Cada clase DAO es responsable EXCLUSIVAMENTE de la persistencia de una
entidad: aquí, y sólo aquí, se escribe SQL. La lógica de negocio y la
interfaz gráfica nunca acceden directamente a la base de datos: siempre
lo hacen a través de los métodos públicos que exponen estas clases,
protegiendo así el encapsulamiento del sistema.
"""

from conexion import ConexionDB
from modelos import Libro, Estudiante, Docente, Prestamo


class LibroDAO:
    """DAO encargado del acceso a datos de la entidad Libro."""

    def insertar(self, libro: Libro) -> int:
        conexion = ConexionDB.conectar()
        try:
            cursor = conexion.cursor()
            cursor.execute("""
                INSERT INTO libros
                    (titulo, autor, editorial, isbn, genero, edad_recomendada, ciclo, stock, disponibles)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (libro.titulo, libro.autor, libro.editorial, libro.isbn or None,
                  libro.genero, libro.edad_recomendada or None, libro.ciclo,
                  libro.stock, libro.disponibles))
            conexion.commit()
            return cursor.lastrowid
        finally:
            ConexionDB.cerrar(conexion)

    def obtener_todos(self):
        conexion = ConexionDB.conectar()
        try:
            filas = conexion.execute("SELECT * FROM libros ORDER BY titulo ASC").fetchall()
            return [self._fila_a_libro(f) for f in filas]
        finally:
            ConexionDB.cerrar(conexion)

    def obtener_por_id(self, id_libro):
        conexion = ConexionDB.conectar()
        try:
            fila = conexion.execute(
                "SELECT * FROM libros WHERE id_libro = ?", (id_libro,)
            ).fetchone()
            return self._fila_a_libro(fila) if fila else None
        finally:
            ConexionDB.cerrar(conexion)

    def actualizar(self, libro: Libro):
        if not libro.id_libro:
            raise ValueError("No se puede actualizar un libro sin id.")
        conexion = ConexionDB.conectar()
        try:
            conexion.execute("""
                UPDATE libros SET
                    titulo = ?, autor = ?, editorial = ?, isbn = ?,
                    genero = ?, edad_recomendada = ?, ciclo = ?,
                    stock = ?, disponibles = ?
                WHERE id_libro = ?
            """, (libro.titulo, libro.autor, libro.editorial, libro.isbn or None,
                  libro.genero, libro.edad_recomendada or None, libro.ciclo,
                  libro.stock, libro.disponibles, libro.id_libro))
            conexion.commit()
        finally:
            ConexionDB.cerrar(conexion)

    def eliminar(self, id_libro):
        conexion = ConexionDB.conectar()
        try:
            conexion.execute("DELETE FROM libros WHERE id_libro = ?", (id_libro,))
            conexion.commit()
        finally:
            ConexionDB.cerrar(conexion)

    def actualizar_disponibles(self, id_libro, delta):
        """Suma (o resta, si delta es negativo) unidades al stock disponible de un libro."""
        conexion = ConexionDB.conectar()
        try:
            conexion.execute(
                "UPDATE libros SET disponibles = disponibles + ? WHERE id_libro = ?",
                (delta, id_libro)
            )
            conexion.commit()
        finally:
            ConexionDB.cerrar(conexion)

    def busqueda_avanzada(self, titulo="", autor="", genero="Todos",
                           ciclo="Todos", edad="Todos", solo_disponibles=False):
        """
        Búsqueda combinable de libros por título, autor, género, ciclo,
        edad recomendada y disponibilidad de stock.
        """
        condiciones = []
        parametros = []

        if titulo:
            condiciones.append("titulo LIKE ?")
            parametros.append(f"%{titulo}%")
        if autor:
            condiciones.append("autor LIKE ?")
            parametros.append(f"%{autor}%")
        if genero and genero != "Todos":
            condiciones.append("genero = ?")
            parametros.append(genero)
        if ciclo and ciclo != "Todos":
            condiciones.append("ciclo = ?")
            parametros.append(ciclo)
        if edad and edad != "Todos":
            if edad == "Sin especificar":
                condiciones.append("(edad_recomendada IS NULL OR edad_recomendada = '')")
            else:
                condiciones.append("edad_recomendada = ?")
                parametros.append(edad)
        if solo_disponibles:
            condiciones.append("disponibles > 0")

        consulta = "SELECT * FROM libros"
        if condiciones:
            consulta += " WHERE " + " AND ".join(condiciones)
        consulta += " ORDER BY titulo ASC"

        conexion = ConexionDB.conectar()
        try:
            filas = conexion.execute(consulta, parametros).fetchall()
            return [self._fila_a_libro(f) for f in filas]
        finally:
            ConexionDB.cerrar(conexion)

    @staticmethod
    def _fila_a_libro(fila):
        return Libro(
            id_libro=fila["id_libro"],
            titulo=fila["titulo"],
            autor=fila["autor"],
            editorial=fila["editorial"],
            isbn=fila["isbn"],
            genero=fila["genero"],
            edad_recomendada=fila["edad_recomendada"],
            ciclo=fila["ciclo"],
            stock=fila["stock"],
            disponibles=fila["disponibles"],
        )


class EstudianteDAO:
    """DAO encargado del acceso a datos de la entidad Estudiante."""

    def insertar(self, estudiante: Estudiante) -> int:
        conexion = ConexionDB.conectar()
        try:
            cursor = conexion.cursor()
            cursor.execute("""
                INSERT INTO estudiantes (nombre, apellido, grado, dni)
                VALUES (?, ?, ?, ?)
            """, (estudiante.nombre, estudiante.apellido, estudiante.grado, estudiante.dni))
            conexion.commit()
            return cursor.lastrowid
        finally:
            ConexionDB.cerrar(conexion)

    def obtener_todos(self):
        conexion = ConexionDB.conectar()
        try:
            filas = conexion.execute(
                "SELECT * FROM estudiantes ORDER BY apellido ASC"
            ).fetchall()
            return [self._fila_a_estudiante(f) for f in filas]
        finally:
            ConexionDB.cerrar(conexion)

    def obtener_por_id(self, id_estudiante):
        conexion = ConexionDB.conectar()
        try:
            fila = conexion.execute(
                "SELECT * FROM estudiantes WHERE id_estudiante = ?", (id_estudiante,)
            ).fetchone()
            return self._fila_a_estudiante(fila) if fila else None
        finally:
            ConexionDB.cerrar(conexion)

    def actualizar(self, estudiante: Estudiante):
        conexion = ConexionDB.conectar()
        try:
            conexion.execute("""
                UPDATE estudiantes SET nombre = ?, apellido = ?, grado = ?, dni = ?
                WHERE id_estudiante = ?
            """, (estudiante.nombre, estudiante.apellido, estudiante.grado,
                  estudiante.dni, estudiante.id_estudiante))
            conexion.commit()
        finally:
            ConexionDB.cerrar(conexion)

    def eliminar(self, id_estudiante):
        conexion = ConexionDB.conectar()
        try:
            conexion.execute("DELETE FROM estudiantes WHERE id_estudiante = ?", (id_estudiante,))
            conexion.commit()
        finally:
            ConexionDB.cerrar(conexion)

    @staticmethod
    def _fila_a_estudiante(fila):
        return Estudiante(
            id_estudiante=fila["id_estudiante"],
            nombre=fila["nombre"],
            apellido=fila["apellido"],
            grado=fila["grado"],
            dni=fila["dni"],
        )


class DocenteDAO:
    """DAO encargado del acceso a datos de la entidad Docente."""

    def insertar(self, docente: Docente) -> int:
        conexion = ConexionDB.conectar()
        try:
            cursor = conexion.cursor()
            cursor.execute("""
                INSERT INTO docentes (nombre, apellido, area, dni)
                VALUES (?, ?, ?, ?)
            """, (docente.nombre, docente.apellido, docente.area, docente.dni))
            conexion.commit()
            return cursor.lastrowid
        finally:
            ConexionDB.cerrar(conexion)

    def obtener_todos(self):
        conexion = ConexionDB.conectar()
        try:
            filas = conexion.execute(
                "SELECT * FROM docentes ORDER BY apellido ASC"
            ).fetchall()
            return [self._fila_a_docente(f) for f in filas]
        finally:
            ConexionDB.cerrar(conexion)

    def obtener_por_id(self, id_docente):
        conexion = ConexionDB.conectar()
        try:
            fila = conexion.execute(
                "SELECT * FROM docentes WHERE id_docente = ?", (id_docente,)
            ).fetchone()
            return self._fila_a_docente(fila) if fila else None
        finally:
            ConexionDB.cerrar(conexion)

    def actualizar(self, docente: Docente):
        conexion = ConexionDB.conectar()
        try:
            conexion.execute("""
                UPDATE docentes SET nombre = ?, apellido = ?, area = ?, dni = ?
                WHERE id_docente = ?
            """, (docente.nombre, docente.apellido, docente.area,
                  docente.dni, docente.id_docente))
            conexion.commit()
        finally:
            ConexionDB.cerrar(conexion)

    def eliminar(self, id_docente):
        conexion = ConexionDB.conectar()
        try:
            conexion.execute("DELETE FROM docentes WHERE id_docente = ?", (id_docente,))
            conexion.commit()
        finally:
            ConexionDB.cerrar(conexion)

    @staticmethod
    def _fila_a_docente(fila):
        return Docente(
            id_docente=fila["id_docente"],
            nombre=fila["nombre"],
            apellido=fila["apellido"],
            area=fila["area"],
            dni=fila["dni"],
        )


class PrestamoDAO:
    """
    DAO encargado del acceso a datos de la entidad Prestamo.
    Implementa además consultas con JOIN para relacionar el préstamo
    con el libro y el solicitante (estudiante o docente) correspondiente.
    """

    def insertar(self, prestamo: Prestamo) -> int:
        conexion = ConexionDB.conectar()
        try:
            cursor = conexion.cursor()
            cursor.execute("""
                INSERT INTO prestamos
                    (id_libro, tipo_solicitante, id_solicitante, fecha_prestamo,
                     fecha_devolucion_estimada, fecha_devolucion_real, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (prestamo.id_libro, prestamo.tipo_solicitante, prestamo.id_solicitante,
                  prestamo.fecha_prestamo, prestamo.fecha_devolucion_estimada,
                  prestamo.fecha_devolucion_real, prestamo.estado))
            conexion.commit()
            return cursor.lastrowid
        finally:
            ConexionDB.cerrar(conexion)

    def actualizar(self, prestamo: Prestamo):
        conexion = ConexionDB.conectar()
        try:
            conexion.execute("""
                UPDATE prestamos SET
                    id_libro = ?, tipo_solicitante = ?, id_solicitante = ?,
                    fecha_prestamo = ?, fecha_devolucion_estimada = ?,
                    fecha_devolucion_real = ?, estado = ?
                WHERE id_prestamo = ?
            """, (prestamo.id_libro, prestamo.tipo_solicitante, prestamo.id_solicitante,
                  prestamo.fecha_prestamo, prestamo.fecha_devolucion_estimada,
                  prestamo.fecha_devolucion_real, prestamo.estado, prestamo.id_prestamo))
            conexion.commit()
        finally:
            ConexionDB.cerrar(conexion)

    def eliminar(self, id_prestamo):
        conexion = ConexionDB.conectar()
        try:
            conexion.execute("DELETE FROM prestamos WHERE id_prestamo = ?", (id_prestamo,))
            conexion.commit()
        finally:
            ConexionDB.cerrar(conexion)

    def registrar_devolucion(self, id_prestamo, fecha_devolucion_real):
        conexion = ConexionDB.conectar()
        try:
            conexion.execute("""
                UPDATE prestamos SET fecha_devolucion_real = ?, estado = 'Devuelto'
                WHERE id_prestamo = ?
            """, (fecha_devolucion_real, id_prestamo))
            conexion.commit()
        finally:
            ConexionDB.cerrar(conexion)

    def obtener_por_id(self, id_prestamo):
        conexion = ConexionDB.conectar()
        try:
            fila = conexion.execute(
                "SELECT * FROM prestamos WHERE id_prestamo = ?", (id_prestamo,)
            ).fetchone()
            if not fila:
                return None
            return Prestamo(
                id_prestamo=fila["id_prestamo"],
                id_libro=fila["id_libro"],
                tipo_solicitante=fila["tipo_solicitante"],
                id_solicitante=fila["id_solicitante"],
                fecha_prestamo=fila["fecha_prestamo"],
                fecha_devolucion_estimada=fila["fecha_devolucion_estimada"],
                fecha_devolucion_real=fila["fecha_devolucion_real"],
                estado=fila["estado"],
            )
        finally:
            ConexionDB.cerrar(conexion)

    def obtener_todos_detallado(self):
        """
        Consulta con JOIN: trae cada préstamo junto con el título del libro
        y el nombre completo del solicitante (estudiante o docente), resuelto
        dinámicamente según el campo tipo_solicitante.
        """
        consulta = """
            SELECT
                p.id_prestamo, p.id_libro, l.titulo AS titulo_libro,
                p.tipo_solicitante, p.id_solicitante,
                COALESCE(e.apellido || ', ' || e.nombre, d.apellido || ', ' || d.nombre) AS solicitante,
                p.fecha_prestamo, p.fecha_devolucion_estimada,
                p.fecha_devolucion_real, p.estado
            FROM prestamos p
            JOIN libros l ON l.id_libro = p.id_libro
            LEFT JOIN estudiantes e ON p.tipo_solicitante = 'Estudiante' AND e.id_estudiante = p.id_solicitante
            LEFT JOIN docentes d ON p.tipo_solicitante = 'Docente' AND d.id_docente = p.id_solicitante
            ORDER BY p.fecha_prestamo DESC
        """
        conexion = ConexionDB.conectar()
        try:
            filas = conexion.execute(consulta).fetchall()
            return [dict(f) for f in filas]
        finally:
            ConexionDB.cerrar(conexion)

    def buscar_detallado(self, estado="Todos", tipo_solicitante="Todos", texto=""):
        """Búsqueda combinable de préstamos por estado, tipo de solicitante y texto libre."""
        condiciones = []
        parametros = []

        if estado and estado != "Todos":
            condiciones.append("p.estado = ?")
            parametros.append(estado)
        if tipo_solicitante and tipo_solicitante != "Todos":
            condiciones.append("p.tipo_solicitante = ?")
            parametros.append(tipo_solicitante)
        if texto:
            condiciones.append("""
                (l.titulo LIKE ? OR
                 COALESCE(e.apellido || ' ' || e.nombre, d.apellido || ' ' || d.nombre) LIKE ?)
            """)
            parametros.extend([f"%{texto}%", f"%{texto}%"])

        consulta = """
            SELECT
                p.id_prestamo, p.id_libro, l.titulo AS titulo_libro,
                p.tipo_solicitante, p.id_solicitante,
                COALESCE(e.apellido || ', ' || e.nombre, d.apellido || ', ' || d.nombre) AS solicitante,
                p.fecha_prestamo, p.fecha_devolucion_estimada,
                p.fecha_devolucion_real, p.estado
            FROM prestamos p
            JOIN libros l ON l.id_libro = p.id_libro
            LEFT JOIN estudiantes e ON p.tipo_solicitante = 'Estudiante' AND e.id_estudiante = p.id_solicitante
            LEFT JOIN docentes d ON p.tipo_solicitante = 'Docente' AND d.id_docente = p.id_solicitante
        """
        if condiciones:
            consulta += " WHERE " + " AND ".join(condiciones)
        consulta += " ORDER BY p.fecha_prestamo DESC"

        conexion = ConexionDB.conectar()
        try:
            filas = conexion.execute(consulta, parametros).fetchall()
            return [dict(f) for f in filas]
        finally:
            ConexionDB.cerrar(conexion)
