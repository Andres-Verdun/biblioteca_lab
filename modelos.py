"""
modelos.py
Clases de dominio (modelos) del sistema de gestión de biblioteca escolar.

Cada clase representa una entidad del sistema y aplica encapsulamiento:
los atributos se guardan como privados (prefijo "_") y se accede/modifica
a través de propiedades (@property / @setter), que además validan los
datos antes de asignarlos. De esta forma ninguna otra capa del sistema
(DAO, GUI) puede dejar un objeto en un estado inválido.
"""

GENEROS = [
    "Cuento", "Novela", "Poesía", "Fábula",
    "Cómic/Historieta", "Divulgación", "Enciclopedia", "Otro",
]

CICLOS = ["Inicial", "Primer Ciclo", "Segundo Ciclo"]

EDADES_RECOMENDADAS = ["3-5 años", "6-8 años", "9-11 años", "12-13 años"]

ESTADOS_PRESTAMO = ["Prestado", "Devuelto", "Atrasado"]

TIPOS_SOLICITANTE = ["Estudiante", "Docente"]


class Libro:
    """Representa un libro del catálogo de la biblioteca escolar."""

    def __init__(self, titulo, autor, genero, edad_recomendada, ciclo,
                 stock, disponibles=None, editorial="", isbn="", id_libro=None):
        self.titulo = titulo
        self.autor = autor
        self.editorial = editorial
        self.isbn = isbn
        self.genero = genero
        self.edad_recomendada = edad_recomendada
        self.ciclo = ciclo
        self.stock = stock
        self.disponibles = disponibles if disponibles is not None else self.stock
        self._id_libro = id_libro

    @property
    def id_libro(self):
        return self._id_libro

    @property
    def titulo(self):
        return self._titulo

    @titulo.setter
    def titulo(self, valor):
        if not valor or not str(valor).strip():
            raise ValueError("El título del libro no puede estar vacío.")
        self._titulo = str(valor).strip()

    @property
    def autor(self):
        return self._autor

    @autor.setter
    def autor(self, valor):
        if not valor or not str(valor).strip():
            raise ValueError("El autor del libro no puede estar vacío.")
        self._autor = str(valor).strip()

    @property
    def editorial(self):
        return self._editorial

    @editorial.setter
    def editorial(self, valor):
        self._editorial = str(valor).strip() if valor else ""

    @property
    def isbn(self):
        return self._isbn

    @isbn.setter
    def isbn(self, valor):
        self._isbn = str(valor).strip() if valor else ""

    @property
    def genero(self):
        return self._genero

    @genero.setter
    def genero(self, valor):
        if not valor:
            raise ValueError("Debe seleccionar un género para el libro.")
        self._genero = valor

    @property
    def edad_recomendada(self):
        return self._edad_recomendada

    @edad_recomendada.setter
    def edad_recomendada(self, valor):
        # Campo opcional: se admite dejarlo en blanco (no todos los libros
        # tienen una franja etaria definida, por ejemplo material de consulta).
        self._edad_recomendada = valor.strip() if valor else ""

    @property
    def ciclo(self):
        return self._ciclo

    @ciclo.setter
    def ciclo(self, valor):
        if not valor:
            raise ValueError("Debe seleccionar un ciclo para el libro.")
        self._ciclo = valor

    @property
    def stock(self):
        return self._stock

    @stock.setter
    def stock(self, valor):
        try:
            valor = int(valor)
        except (TypeError, ValueError):
            raise ValueError("El stock debe ser un número entero.")
        if valor < 0:
            raise ValueError("El stock no puede ser negativo.")
        self._stock = valor

    @property
    def disponibles(self):
        return self._disponibles

    @disponibles.setter
    def disponibles(self, valor):
        try:
            valor = int(valor)
        except (TypeError, ValueError):
            raise ValueError("Los ejemplares disponibles deben ser un número entero.")
        if valor < 0:
            raise ValueError("Los ejemplares disponibles no pueden ser negativos.")
        self._disponibles = valor

    def __str__(self):
        return f"{self._titulo} - {self._autor} ({self._genero})"


class Estudiante:
    """Representa a un estudiante que puede solicitar préstamos de libros."""

    def __init__(self, nombre, apellido, grado, dni, id_estudiante=None):
        self.nombre = nombre
        self.apellido = apellido
        self.grado = grado
        self.dni = dni
        self._id_estudiante = id_estudiante

    @property
    def id_estudiante(self):
        return self._id_estudiante

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if not valor or not str(valor).strip():
            raise ValueError("El nombre del estudiante no puede estar vacío.")
        self._nombre = str(valor).strip()

    @property
    def apellido(self):
        return self._apellido

    @apellido.setter
    def apellido(self, valor):
        if not valor or not str(valor).strip():
            raise ValueError("El apellido del estudiante no puede estar vacío.")
        self._apellido = str(valor).strip()

    @property
    def grado(self):
        return self._grado

    @grado.setter
    def grado(self, valor):
        if not valor or not str(valor).strip():
            raise ValueError("Debe indicar el grado del estudiante.")
        self._grado = str(valor).strip()

    @property
    def dni(self):
        return self._dni

    @dni.setter
    def dni(self, valor):
        if not valor or not str(valor).strip():
            raise ValueError("El DNI del estudiante no puede estar vacío.")
        self._dni = str(valor).strip()

    def nombre_completo(self):
        return f"{self._apellido}, {self._nombre}"

    def __str__(self):
        return self.nombre_completo()


class Docente:
    """Representa a un docente que puede solicitar préstamos de libros."""

    def __init__(self, nombre, apellido, area, dni, id_docente=None):
        self.nombre = nombre
        self.apellido = apellido
        self.area = area
        self.dni = dni
        self._id_docente = id_docente

    @property
    def id_docente(self):
        return self._id_docente

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if not valor or not str(valor).strip():
            raise ValueError("El nombre del docente no puede estar vacío.")
        self._nombre = str(valor).strip()

    @property
    def apellido(self):
        return self._apellido

    @apellido.setter
    def apellido(self, valor):
        if not valor or not str(valor).strip():
            raise ValueError("El apellido del docente no puede estar vacío.")
        self._apellido = str(valor).strip()

    @property
    def area(self):
        return self._area

    @area.setter
    def area(self, valor):
        self._area = str(valor).strip() if valor else ""

    @property
    def dni(self):
        return self._dni

    @dni.setter
    def dni(self, valor):
        if not valor or not str(valor).strip():
            raise ValueError("El DNI del docente no puede estar vacío.")
        self._dni = str(valor).strip()

    def nombre_completo(self):
        return f"{self._apellido}, {self._nombre}"

    def __str__(self):
        return self.nombre_completo()


class Prestamo:
    """Representa el préstamo de un libro a un estudiante o a un docente."""

    def __init__(self, id_libro, tipo_solicitante, id_solicitante,
                 fecha_prestamo, fecha_devolucion_estimada,
                 fecha_devolucion_real=None, estado="Prestado", id_prestamo=None):
        self.id_libro = id_libro
        self.tipo_solicitante = tipo_solicitante
        self.id_solicitante = id_solicitante
        self.fecha_prestamo = fecha_prestamo
        self.fecha_devolucion_estimada = fecha_devolucion_estimada
        self.fecha_devolucion_real = fecha_devolucion_real
        self.estado = estado
        self._id_prestamo = id_prestamo

    @property
    def id_prestamo(self):
        return self._id_prestamo

    @property
    def id_libro(self):
        return self._id_libro

    @id_libro.setter
    def id_libro(self, valor):
        if not valor:
            raise ValueError("Debe seleccionar un libro para el préstamo.")
        self._id_libro = valor

    @property
    def tipo_solicitante(self):
        return self._tipo_solicitante

    @tipo_solicitante.setter
    def tipo_solicitante(self, valor):
        if valor not in TIPOS_SOLICITANTE:
            raise ValueError("El tipo de solicitante debe ser 'Estudiante' o 'Docente'.")
        self._tipo_solicitante = valor

    @property
    def id_solicitante(self):
        return self._id_solicitante

    @id_solicitante.setter
    def id_solicitante(self, valor):
        if not valor:
            raise ValueError("Debe seleccionar un solicitante para el préstamo.")
        self._id_solicitante = valor

    @property
    def fecha_prestamo(self):
        return self._fecha_prestamo

    @fecha_prestamo.setter
    def fecha_prestamo(self, valor):
        if not valor:
            raise ValueError("Debe indicar la fecha de préstamo.")
        self._fecha_prestamo = valor

    @property
    def fecha_devolucion_estimada(self):
        return self._fecha_devolucion_estimada

    @fecha_devolucion_estimada.setter
    def fecha_devolucion_estimada(self, valor):
        if not valor:
            raise ValueError("Debe indicar la fecha estimada de devolución.")
        self._fecha_devolucion_estimada = valor

    @property
    def fecha_devolucion_real(self):
        return self._fecha_devolucion_real

    @fecha_devolucion_real.setter
    def fecha_devolucion_real(self, valor):
        self._fecha_devolucion_real = valor

    @property
    def estado(self):
        return self._estado

    @estado.setter
    def estado(self, valor):
        if valor not in ESTADOS_PRESTAMO:
            raise ValueError(f"Estado inválido. Debe ser uno de: {', '.join(ESTADOS_PRESTAMO)}")
        self._estado = valor
