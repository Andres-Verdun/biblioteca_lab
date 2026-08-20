"""
gui.py
Interfaz gráfica de usuario (Tkinter) del sistema de gestión de biblioteca escolar.

Esta capa NUNCA accede directamente a la base de datos: toda la persistencia
se resuelve a través de las clases DAO (dao.py). La GUI sólo se encarga de:
- Capturar datos de los formularios.
- Instanciar clases de dominio (modelos.py), que validan los datos.
- Invocar los métodos públicos de los DAO.
- Mostrar resultados en tablas (ttk.Treeview) y mensajes (tkinter.messagebox).
"""

import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta

from modelos import (
    Libro, Estudiante, Docente, Prestamo,
    GENEROS, CICLOS, EDADES_RECOMENDADAS, TIPOS_SOLICITANTE,
)
from dao import LibroDAO, EstudianteDAO, DocenteDAO, PrestamoDAO
from exportador_pdf import ExportadorPDF
from conexion import ConexionDB

FORMATO_FECHA = "%d/%m/%Y"


def _validar_fecha(texto):
    try:
        datetime.strptime(texto.strip(), FORMATO_FECHA)
        return True
    except ValueError:
        return False


class AplicacionBiblioteca(tk.Tk):
    """Ventana principal del sistema de gestión de biblioteca escolar."""

    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestión de Biblioteca Escolar")
        self.geometry("1150x680")
        self.minsize(1000, 600)

        # Instancias únicas de los DAO utilizados en toda la aplicación.
        self.libro_dao = LibroDAO()
        self.estudiante_dao = EstudianteDAO()
        self.docente_dao = DocenteDAO()
        self.prestamo_dao = PrestamoDAO()

        self._crear_menu()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_libros = ttk.Frame(self.notebook)
        self.tab_estudiantes = ttk.Frame(self.notebook)
        self.tab_docentes = ttk.Frame(self.notebook)
        self.tab_prestamos = ttk.Frame(self.notebook)
        self.tab_busqueda = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_libros, text="Libros")
        self.notebook.add(self.tab_estudiantes, text="Estudiantes")
        self.notebook.add(self.tab_docentes, text="Docentes")
        self.notebook.add(self.tab_prestamos, text="Préstamos")
        self.notebook.add(self.tab_busqueda, text="Búsqueda avanzada")

        self._construir_tab_libros()
        self._construir_tab_estudiantes()
        self._construir_tab_docentes()
        self._construir_tab_prestamos()
        self._construir_tab_busqueda()

        self._refrescar_libros()
        self._refrescar_estudiantes()
        self._refrescar_docentes()
        self._refrescar_prestamos()

    # ------------------------------------------------------------------
    # Menú superior: portabilidad de la base de datos
    # ------------------------------------------------------------------
    def _crear_menu(self):
        menu_barra = tk.Menu(self)

        menu_bd = tk.Menu(menu_barra, tearoff=0)
        menu_bd.add_command(label="Exportar copia de seguridad...", command=self._exportar_backup)
        menu_bd.add_command(label="Importar / Restaurar copia de seguridad...", command=self._importar_backup)
        menu_bd.add_separator()
        menu_bd.add_command(label="Salir", command=self.destroy)
        menu_barra.add_cascade(label="Base de datos", menu=menu_bd)

        self.config(menu=menu_barra)

    def _exportar_backup(self):
        """Copia el archivo biblioteca.db a la ubicación que elija el usuario (pendrive, etc.)."""
        destino = filedialog.asksaveasfilename(
            title="Guardar copia de seguridad",
            defaultextension=".db",
            initialfile="biblioteca_backup.db",
            filetypes=[("Base de datos SQLite", "*.db")],
        )
        if not destino:
            return
        try:
            shutil.copy(ConexionDB.obtener_ruta(), destino)
            messagebox.showinfo("Copia de seguridad", f"Copia guardada correctamente en:\n{destino}")
        except OSError as error:
            messagebox.showerror("Error", f"No se pudo generar la copia de seguridad.\n{error}")

    def _importar_backup(self):
        """Reemplaza la base de datos actual por un archivo .db elegido por el usuario."""
        origen = filedialog.askopenfilename(
            title="Seleccionar copia de seguridad",
            filetypes=[("Base de datos SQLite", "*.db")],
        )
        if not origen:
            return
        confirmar = messagebox.askyesno(
            "Confirmar restauración",
            "Esta acción reemplaza TODOS los datos actuales por los del archivo "
            "seleccionado. Esta operación no se puede deshacer.\n\n¿Desea continuar?",
        )
        if not confirmar:
            return
        try:
            shutil.copy(origen, ConexionDB.obtener_ruta())
            messagebox.showinfo(
                "Restauración completa",
                "Los datos se restauraron correctamente.",
            )
            self._refrescar_libros()
            self._refrescar_estudiantes()
            self._refrescar_docentes()
            self._refrescar_prestamos()
            self._refrescar_combobox_libros_prestamo()
            self._refrescar_combobox_solicitantes()
        except OSError as error:
            messagebox.showerror("Error", f"No se pudo restaurar la copia de seguridad.\n{error}")

    # ==================================================================
    # TAB LIBROS
    # ==================================================================
    def _construir_tab_libros(self):
        contenedor = self.tab_libros
        panel_form = ttk.LabelFrame(contenedor, text="Datos del libro")
        panel_form.pack(fill="x", padx=8, pady=8)

        self.var_libro_titulo = tk.StringVar()
        self.var_libro_autor = tk.StringVar()
        self.var_libro_editorial = tk.StringVar()
        self.var_libro_isbn = tk.StringVar()
        self.var_libro_genero = tk.StringVar()
        self.var_libro_edad = tk.StringVar()
        self.var_libro_ciclo = tk.StringVar()
        self.var_libro_stock = tk.StringVar()
        self._id_libro_seleccionado = None

        campos_texto = [
            ("Título*", self.var_libro_titulo), ("Autor*", self.var_libro_autor),
            ("Editorial", self.var_libro_editorial), ("ISBN", self.var_libro_isbn),
        ]
        for i, (texto, var) in enumerate(campos_texto):
            ttk.Label(panel_form, text=texto).grid(row=0, column=i * 2, sticky="w", padx=4, pady=4)
            ttk.Entry(panel_form, textvariable=var, width=20).grid(row=0, column=i * 2 + 1, padx=4, pady=4)

        ttk.Label(panel_form, text="Género*").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Combobox(panel_form, textvariable=self.var_libro_genero, values=GENEROS,
                     state="readonly", width=18).grid(row=1, column=1, padx=4, pady=4)

        ttk.Label(panel_form, text="Edad recomendada").grid(row=1, column=2, sticky="w", padx=4, pady=4)
        ttk.Combobox(panel_form, textvariable=self.var_libro_edad, values=[""] + EDADES_RECOMENDADAS,
                     state="readonly", width=18).grid(row=1, column=3, padx=4, pady=4)

        ttk.Label(panel_form, text="Ciclo*").grid(row=1, column=4, sticky="w", padx=4, pady=4)
        ttk.Combobox(panel_form, textvariable=self.var_libro_ciclo, values=CICLOS,
                     state="readonly", width=18).grid(row=1, column=5, padx=4, pady=4)

        ttk.Label(panel_form, text="Stock*").grid(row=1, column=6, sticky="w", padx=4, pady=4)
        tk.Spinbox(panel_form, from_=0, to=9999, textvariable=self.var_libro_stock,
                   width=8).grid(row=1, column=7, padx=4, pady=4)

        panel_botones = ttk.Frame(contenedor)
        panel_botones.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(panel_botones, text="Agregar", command=self._agregar_libro).pack(side="left", padx=4)
        ttk.Button(panel_botones, text="Modificar", command=self._modificar_libro).pack(side="left", padx=4)
        ttk.Button(panel_botones, text="Eliminar", command=self._eliminar_libro).pack(side="left", padx=4)
        ttk.Button(panel_botones, text="Limpiar", command=self._limpiar_form_libro).pack(side="left", padx=4)
        ttk.Button(panel_botones, text="Exportar catálogo a PDF",
                   command=self._exportar_libros_pdf).pack(side="right", padx=4)

        columnas = ("id", "titulo", "autor", "editorial", "isbn", "genero", "edad", "ciclo", "stock", "disponibles")
        encabezados = ("ID", "Título", "Autor", "Editorial", "ISBN", "Género", "Edad", "Ciclo", "Stock", "Disp.")
        self.tabla_libros = ttk.Treeview(contenedor, columns=columnas, show="headings", height=14)
        for col, enc in zip(columnas, encabezados):
            self.tabla_libros.heading(col, text=enc)
            self.tabla_libros.column(col, width=100, anchor="center")
        self.tabla_libros.column("titulo", width=180, anchor="w")
        self.tabla_libros.column("autor", width=140, anchor="w")
        self.tabla_libros.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.tabla_libros.bind("<<TreeviewSelect>>", self._seleccionar_libro)

    def _limpiar_form_libro(self):
        self._id_libro_seleccionado = None
        for var in (self.var_libro_titulo, self.var_libro_autor, self.var_libro_editorial,
                    self.var_libro_isbn, self.var_libro_genero, self.var_libro_edad,
                    self.var_libro_ciclo, self.var_libro_stock):
            var.set("")
        self.tabla_libros.selection_remove(self.tabla_libros.selection())

    def _leer_form_libro(self, disponibles=None):
        return Libro(
            id_libro=self._id_libro_seleccionado,
            titulo=self.var_libro_titulo.get(),
            autor=self.var_libro_autor.get(),
            editorial=self.var_libro_editorial.get(),
            isbn=self.var_libro_isbn.get(),
            genero=self.var_libro_genero.get(),
            edad_recomendada=self.var_libro_edad.get(),
            ciclo=self.var_libro_ciclo.get(),
            stock=self.var_libro_stock.get() or 0,
            disponibles=disponibles,
        )

    def _agregar_libro(self):
        try:
            libro = self._leer_form_libro(disponibles=None)
        except ValueError as error:
            messagebox.showerror("Datos inválidos", str(error))
            return
        try:
            self.libro_dao.insertar(libro)
        except Exception as error:
            messagebox.showerror("Error al guardar", f"No se pudo agregar el libro. "
                                                       f"Verifique que el ISBN no esté duplicado.\n{error}")
            return
        messagebox.showinfo("Éxito", "Libro agregado correctamente.")
        self._limpiar_form_libro()
        self._refrescar_libros()
        self._refrescar_combobox_libros_prestamo()

    def _modificar_libro(self):
        if not self._id_libro_seleccionado:
            messagebox.showwarning("Atención", "Seleccione un libro de la lista para modificar.")
            return
        libro_actual = self.libro_dao.obtener_por_id(self._id_libro_seleccionado)
        if not libro_actual:
            messagebox.showerror("Error", "El libro seleccionado ya no existe.")
            return
        # Se conserva la cantidad de ejemplares actualmente prestados al recalcular
        # los disponibles según el nuevo stock ingresado.
        prestados = libro_actual.stock - libro_actual.disponibles
        try:
            nuevo_stock = int(self.var_libro_stock.get() or 0)
            libro = self._leer_form_libro(disponibles=max(0, nuevo_stock - prestados))
        except ValueError as error:
            messagebox.showerror("Datos inválidos", str(error))
            return
        try:
            self.libro_dao.actualizar(libro)
        except Exception as error:
            messagebox.showerror("Error al guardar", f"No se pudo modificar el libro.\n{error}")
            return
        messagebox.showinfo("Éxito", "Libro modificado correctamente.")
        self._limpiar_form_libro()
        self._refrescar_libros()
        self._refrescar_combobox_libros_prestamo()

    def _eliminar_libro(self):
        if not self._id_libro_seleccionado:
            messagebox.showwarning("Atención", "Seleccione un libro de la lista para eliminar.")
            return
        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            "¿Está seguro de eliminar este libro? Se eliminarán también sus registros de préstamo asociados.",
        )
        if not confirmar:
            return
        try:
            self.libro_dao.eliminar(self._id_libro_seleccionado)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo eliminar el libro.\n{error}")
            return
        messagebox.showinfo("Éxito", "Libro eliminado correctamente.")
        self._limpiar_form_libro()
        self._refrescar_libros()
        self._refrescar_combobox_libros_prestamo()

    def _seleccionar_libro(self, evento):
        seleccion = self.tabla_libros.selection()
        if not seleccion:
            return
        valores = self.tabla_libros.item(seleccion[0], "values")
        self._id_libro_seleccionado = int(valores[0])
        self.var_libro_titulo.set(valores[1])
        self.var_libro_autor.set(valores[2])
        self.var_libro_editorial.set(valores[3])
        self.var_libro_isbn.set(valores[4])
        self.var_libro_genero.set(valores[5])
        self.var_libro_edad.set(valores[6])
        self.var_libro_ciclo.set(valores[7])
        self.var_libro_stock.set(valores[8])

    def _refrescar_libros(self):
        for fila in self.tabla_libros.get_children():
            self.tabla_libros.delete(fila)
        for libro in self.libro_dao.obtener_todos():
            self.tabla_libros.insert("", "end", values=(
                libro.id_libro, libro.titulo, libro.autor, libro.editorial, libro.isbn,
                libro.genero, libro.edad_recomendada, libro.ciclo, libro.stock, libro.disponibles,
            ))

    def _exportar_libros_pdf(self):
        self._exportar_treeview_pdf(self.tabla_libros, "Catálogo de libros",
                                     ("ID", "Título", "Autor", "Editorial", "ISBN",
                                      "Género", "Edad", "Ciclo", "Stock", "Disp."))

    # ==================================================================
    # TAB ESTUDIANTES
    # ==================================================================
    def _construir_tab_estudiantes(self):
        contenedor = self.tab_estudiantes
        panel_form = ttk.LabelFrame(contenedor, text="Datos del estudiante")
        panel_form.pack(fill="x", padx=8, pady=8)

        self.var_est_nombre = tk.StringVar()
        self.var_est_apellido = tk.StringVar()
        self.var_est_grado = tk.StringVar()
        self.var_est_dni = tk.StringVar()
        self._id_estudiante_seleccionado = None

        grados = [f"{n}° grado" for n in range(1, 8)]

        ttk.Label(panel_form, text="Nombre*").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(panel_form, textvariable=self.var_est_nombre, width=20).grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(panel_form, text="Apellido*").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        ttk.Entry(panel_form, textvariable=self.var_est_apellido, width=20).grid(row=0, column=3, padx=4, pady=4)

        ttk.Label(panel_form, text="Grado*").grid(row=0, column=4, sticky="w", padx=4, pady=4)
        ttk.Combobox(panel_form, textvariable=self.var_est_grado, values=grados,
                     state="readonly", width=14).grid(row=0, column=5, padx=4, pady=4)

        ttk.Label(panel_form, text="DNI*").grid(row=0, column=6, sticky="w", padx=4, pady=4)
        ttk.Entry(panel_form, textvariable=self.var_est_dni, width=14).grid(row=0, column=7, padx=4, pady=4)

        panel_botones = ttk.Frame(contenedor)
        panel_botones.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(panel_botones, text="Agregar", command=self._agregar_estudiante).pack(side="left", padx=4)
        ttk.Button(panel_botones, text="Modificar", command=self._modificar_estudiante).pack(side="left", padx=4)
        ttk.Button(panel_botones, text="Eliminar", command=self._eliminar_estudiante).pack(side="left", padx=4)
        ttk.Button(panel_botones, text="Limpiar", command=self._limpiar_form_estudiante).pack(side="left", padx=4)

        columnas = ("id", "apellido", "nombre", "grado", "dni")
        encabezados = ("ID", "Apellido", "Nombre", "Grado", "DNI")
        self.tabla_estudiantes = ttk.Treeview(contenedor, columns=columnas, show="headings", height=14)
        for col, enc in zip(columnas, encabezados):
            self.tabla_estudiantes.heading(col, text=enc)
            self.tabla_estudiantes.column(col, width=130, anchor="center")
        self.tabla_estudiantes.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.tabla_estudiantes.bind("<<TreeviewSelect>>", self._seleccionar_estudiante)

    def _limpiar_form_estudiante(self):
        self._id_estudiante_seleccionado = None
        for var in (self.var_est_nombre, self.var_est_apellido, self.var_est_grado, self.var_est_dni):
            var.set("")
        self.tabla_estudiantes.selection_remove(self.tabla_estudiantes.selection())

    def _agregar_estudiante(self):
        try:
            estudiante = Estudiante(nombre=self.var_est_nombre.get(), apellido=self.var_est_apellido.get(),
                                     grado=self.var_est_grado.get(), dni=self.var_est_dni.get())
            self.estudiante_dao.insertar(estudiante)
        except ValueError as error:
            messagebox.showerror("Datos inválidos", str(error))
            return
        except Exception as error:
            messagebox.showerror("Error al guardar", f"No se pudo agregar el estudiante. "
                                                       f"Verifique que el DNI no esté duplicado.\n{error}")
            return
        messagebox.showinfo("Éxito", "Estudiante agregado correctamente.")
        self._limpiar_form_estudiante()
        self._refrescar_estudiantes()
        self._refrescar_combobox_solicitantes()

    def _modificar_estudiante(self):
        if not self._id_estudiante_seleccionado:
            messagebox.showwarning("Atención", "Seleccione un estudiante de la lista para modificar.")
            return
        try:
            estudiante = Estudiante(id_estudiante=self._id_estudiante_seleccionado,
                                     nombre=self.var_est_nombre.get(), apellido=self.var_est_apellido.get(),
                                     grado=self.var_est_grado.get(), dni=self.var_est_dni.get())
            self.estudiante_dao.actualizar(estudiante)
        except ValueError as error:
            messagebox.showerror("Datos inválidos", str(error))
            return
        except Exception as error:
            messagebox.showerror("Error al guardar", f"No se pudo modificar el estudiante.\n{error}")
            return
        messagebox.showinfo("Éxito", "Estudiante modificado correctamente.")
        self._limpiar_form_estudiante()
        self._refrescar_estudiantes()
        self._refrescar_combobox_solicitantes()

    def _eliminar_estudiante(self):
        if not self._id_estudiante_seleccionado:
            messagebox.showwarning("Atención", "Seleccione un estudiante de la lista para eliminar.")
            return
        confirmar = messagebox.askyesno("Confirmar eliminación", "¿Está seguro de eliminar este estudiante?")
        if not confirmar:
            return
        try:
            self.estudiante_dao.eliminar(self._id_estudiante_seleccionado)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo eliminar el estudiante.\n{error}")
            return
        messagebox.showinfo("Éxito", "Estudiante eliminado correctamente.")
        self._limpiar_form_estudiante()
        self._refrescar_estudiantes()
        self._refrescar_combobox_solicitantes()

    def _seleccionar_estudiante(self, evento):
        seleccion = self.tabla_estudiantes.selection()
        if not seleccion:
            return
        valores = self.tabla_estudiantes.item(seleccion[0], "values")
        self._id_estudiante_seleccionado = int(valores[0])
        self.var_est_apellido.set(valores[1])
        self.var_est_nombre.set(valores[2])
        self.var_est_grado.set(valores[3])
        self.var_est_dni.set(valores[4])

    def _refrescar_estudiantes(self):
        for fila in self.tabla_estudiantes.get_children():
            self.tabla_estudiantes.delete(fila)
        for estudiante in self.estudiante_dao.obtener_todos():
            self.tabla_estudiantes.insert("", "end", values=(
                estudiante.id_estudiante, estudiante.apellido, estudiante.nombre,
                estudiante.grado, estudiante.dni,
            ))

    # ==================================================================
    # TAB DOCENTES
    # ==================================================================
    def _construir_tab_docentes(self):
        contenedor = self.tab_docentes
        panel_form = ttk.LabelFrame(contenedor, text="Datos del docente")
        panel_form.pack(fill="x", padx=8, pady=8)

        self.var_doc_nombre = tk.StringVar()
        self.var_doc_apellido = tk.StringVar()
        self.var_doc_area = tk.StringVar()
        self.var_doc_dni = tk.StringVar()
        self._id_docente_seleccionado = None

        ttk.Label(panel_form, text="Nombre*").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(panel_form, textvariable=self.var_doc_nombre, width=20).grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(panel_form, text="Apellido*").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        ttk.Entry(panel_form, textvariable=self.var_doc_apellido, width=20).grid(row=0, column=3, padx=4, pady=4)

        ttk.Label(panel_form, text="Área").grid(row=0, column=4, sticky="w", padx=4, pady=4)
        ttk.Entry(panel_form, textvariable=self.var_doc_area, width=18).grid(row=0, column=5, padx=4, pady=4)

        ttk.Label(panel_form, text="DNI*").grid(row=0, column=6, sticky="w", padx=4, pady=4)
        ttk.Entry(panel_form, textvariable=self.var_doc_dni, width=14).grid(row=0, column=7, padx=4, pady=4)

        panel_botones = ttk.Frame(contenedor)
        panel_botones.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(panel_botones, text="Agregar", command=self._agregar_docente).pack(side="left", padx=4)
        ttk.Button(panel_botones, text="Modificar", command=self._modificar_docente).pack(side="left", padx=4)
        ttk.Button(panel_botones, text="Eliminar", command=self._eliminar_docente).pack(side="left", padx=4)
        ttk.Button(panel_botones, text="Limpiar", command=self._limpiar_form_docente).pack(side="left", padx=4)

        columnas = ("id", "apellido", "nombre", "area", "dni")
        encabezados = ("ID", "Apellido", "Nombre", "Área", "DNI")
        self.tabla_docentes = ttk.Treeview(contenedor, columns=columnas, show="headings", height=14)
        for col, enc in zip(columnas, encabezados):
            self.tabla_docentes.heading(col, text=enc)
            self.tabla_docentes.column(col, width=130, anchor="center")
        self.tabla_docentes.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.tabla_docentes.bind("<<TreeviewSelect>>", self._seleccionar_docente)

    def _limpiar_form_docente(self):
        self._id_docente_seleccionado = None
        for var in (self.var_doc_nombre, self.var_doc_apellido, self.var_doc_area, self.var_doc_dni):
            var.set("")
        self.tabla_docentes.selection_remove(self.tabla_docentes.selection())

    def _agregar_docente(self):
        try:
            docente = Docente(nombre=self.var_doc_nombre.get(), apellido=self.var_doc_apellido.get(),
                               area=self.var_doc_area.get(), dni=self.var_doc_dni.get())
            self.docente_dao.insertar(docente)
        except ValueError as error:
            messagebox.showerror("Datos inválidos", str(error))
            return
        except Exception as error:
            messagebox.showerror("Error al guardar", f"No se pudo agregar el docente. "
                                                       f"Verifique que el DNI no esté duplicado.\n{error}")
            return
        messagebox.showinfo("Éxito", "Docente agregado correctamente.")
        self._limpiar_form_docente()
        self._refrescar_docentes()
        self._refrescar_combobox_solicitantes()

    def _modificar_docente(self):
        if not self._id_docente_seleccionado:
            messagebox.showwarning("Atención", "Seleccione un docente de la lista para modificar.")
            return
        try:
            docente = Docente(id_docente=self._id_docente_seleccionado,
                               nombre=self.var_doc_nombre.get(), apellido=self.var_doc_apellido.get(),
                               area=self.var_doc_area.get(), dni=self.var_doc_dni.get())
            self.docente_dao.actualizar(docente)
        except ValueError as error:
            messagebox.showerror("Datos inválidos", str(error))
            return
        except Exception as error:
            messagebox.showerror("Error al guardar", f"No se pudo modificar el docente.\n{error}")
            return
        messagebox.showinfo("Éxito", "Docente modificado correctamente.")
        self._limpiar_form_docente()
        self._refrescar_docentes()
        self._refrescar_combobox_solicitantes()

    def _eliminar_docente(self):
        if not self._id_docente_seleccionado:
            messagebox.showwarning("Atención", "Seleccione un docente de la lista para eliminar.")
            return
        confirmar = messagebox.askyesno("Confirmar eliminación", "¿Está seguro de eliminar este docente?")
        if not confirmar:
            return
        try:
            self.docente_dao.eliminar(self._id_docente_seleccionado)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo eliminar el docente.\n{error}")
            return
        messagebox.showinfo("Éxito", "Docente eliminado correctamente.")
        self._limpiar_form_docente()
        self._refrescar_docentes()
        self._refrescar_combobox_solicitantes()

    def _seleccionar_docente(self, evento):
        seleccion = self.tabla_docentes.selection()
        if not seleccion:
            return
        valores = self.tabla_docentes.item(seleccion[0], "values")
        self._id_docente_seleccionado = int(valores[0])
        self.var_doc_apellido.set(valores[1])
        self.var_doc_nombre.set(valores[2])
        self.var_doc_area.set(valores[3])
        self.var_doc_dni.set(valores[4])

    def _refrescar_docentes(self):
        for fila in self.tabla_docentes.get_children():
            self.tabla_docentes.delete(fila)
        for docente in self.docente_dao.obtener_todos():
            self.tabla_docentes.insert("", "end", values=(
                docente.id_docente, docente.apellido, docente.nombre,
                docente.area, docente.dni,
            ))

    # ==================================================================
    # TAB PRÉSTAMOS
    # ==================================================================
    def _construir_tab_prestamos(self):
        contenedor = self.tab_prestamos
        panel_form = ttk.LabelFrame(contenedor, text="Registrar préstamo")
        panel_form.pack(fill="x", padx=8, pady=8)

        self.var_prestamo_libro = tk.StringVar()
        self.var_prestamo_tipo = tk.StringVar(value=TIPOS_SOLICITANTE[0])
        self.var_prestamo_solicitante = tk.StringVar()
        self.var_prestamo_fecha = tk.StringVar(value=datetime.now().strftime(FORMATO_FECHA))
        self.var_prestamo_fecha_est = tk.StringVar(
            value=(datetime.now() + timedelta(days=14)).strftime(FORMATO_FECHA))

        self._mapa_libros = {}        # "título (disp: n)" -> id_libro
        self._mapa_solicitantes = {}  # "Apellido, Nombre" -> id

        ttk.Label(panel_form, text="Libro*").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.combo_prestamo_libro = ttk.Combobox(panel_form, textvariable=self.var_prestamo_libro,
                                                  state="readonly", width=32)
        self.combo_prestamo_libro.grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(panel_form, text="Tipo de solicitante*").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        combo_tipo = ttk.Combobox(panel_form, textvariable=self.var_prestamo_tipo,
                                   values=TIPOS_SOLICITANTE, state="readonly", width=12)
        combo_tipo.grid(row=0, column=3, padx=4, pady=4)
        combo_tipo.bind("<<ComboboxSelected>>", lambda e: self._refrescar_combobox_solicitantes())

        ttk.Label(panel_form, text="Solicitante*").grid(row=0, column=4, sticky="w", padx=4, pady=4)
        self.combo_prestamo_solicitante = ttk.Combobox(panel_form, textvariable=self.var_prestamo_solicitante,
                                                        state="readonly", width=24)
        self.combo_prestamo_solicitante.grid(row=0, column=5, padx=4, pady=4)

        ttk.Label(panel_form, text="Fecha préstamo*").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(panel_form, textvariable=self.var_prestamo_fecha, width=12).grid(
            row=1, column=1, sticky="w", padx=4, pady=4)

        ttk.Label(panel_form, text="Fecha dev. estimada*").grid(row=1, column=2, sticky="w", padx=4, pady=4)
        ttk.Entry(panel_form, textvariable=self.var_prestamo_fecha_est, width=12).grid(
            row=1, column=3, sticky="w", padx=4, pady=4)
        ttk.Label(panel_form, text="(formato DD/MM/AAAA)").grid(row=1, column=4, columnspan=2, sticky="w", padx=4, pady=4)

        panel_botones = ttk.Frame(contenedor)
        panel_botones.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(panel_botones, text="Registrar préstamo", command=self._registrar_prestamo).pack(side="left", padx=4)
        ttk.Button(panel_botones, text="Registrar devolución", command=self._registrar_devolucion).pack(side="left", padx=4)
        ttk.Button(panel_botones, text="Eliminar registro", command=self._eliminar_prestamo).pack(side="left", padx=4)
        ttk.Button(panel_botones, text="Exportar listado a PDF", command=self._exportar_prestamos_pdf).pack(side="right", padx=4)

        columnas = ("id", "libro", "solicitante", "tipo", "f_prestamo", "f_est", "f_real", "estado")
        encabezados = ("ID", "Libro", "Solicitante", "Tipo", "F. Préstamo", "F. Dev. Estimada", "F. Dev. Real", "Estado")
        self.tabla_prestamos = ttk.Treeview(contenedor, columns=columnas, show="headings", height=13)
        for col, enc in zip(columnas, encabezados):
            self.tabla_prestamos.heading(col, text=enc)
            self.tabla_prestamos.column(col, width=110, anchor="center")
        self.tabla_prestamos.column("libro", width=170, anchor="w")
        self.tabla_prestamos.column("solicitante", width=150, anchor="w")
        self.tabla_prestamos.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._refrescar_combobox_libros_prestamo()
        self._refrescar_combobox_solicitantes()

    def _refrescar_combobox_libros_prestamo(self):
        self._mapa_libros = {}
        opciones = []
        for libro in self.libro_dao.obtener_todos():
            etiqueta = f"{libro.titulo} (disp: {libro.disponibles})"
            self._mapa_libros[etiqueta] = libro.id_libro
            opciones.append(etiqueta)
        if hasattr(self, "combo_prestamo_libro"):
            self.combo_prestamo_libro["values"] = opciones
            self.var_prestamo_libro.set("")

    def _refrescar_combobox_solicitantes(self):
        self._mapa_solicitantes = {}
        opciones = []
        if self.var_prestamo_tipo.get() == "Estudiante":
            for est in self.estudiante_dao.obtener_todos():
                etiqueta = f"{est.apellido}, {est.nombre} ({est.grado})"
                self._mapa_solicitantes[etiqueta] = est.id_estudiante
                opciones.append(etiqueta)
        else:
            for doc in self.docente_dao.obtener_todos():
                etiqueta = f"{doc.apellido}, {doc.nombre}"
                self._mapa_solicitantes[etiqueta] = doc.id_docente
                opciones.append(etiqueta)
        if hasattr(self, "combo_prestamo_solicitante"):
            self.combo_prestamo_solicitante["values"] = opciones
            self.var_prestamo_solicitante.set("")

    def _registrar_prestamo(self):
        etiqueta_libro = self.var_prestamo_libro.get()
        etiqueta_solicitante = self.var_prestamo_solicitante.get()

        if etiqueta_libro not in self._mapa_libros:
            messagebox.showwarning("Atención", "Seleccione un libro válido.")
            return
        if etiqueta_solicitante not in self._mapa_solicitantes:
            messagebox.showwarning("Atención", "Seleccione un solicitante válido.")
            return
        if not _validar_fecha(self.var_prestamo_fecha.get()) or not _validar_fecha(self.var_prestamo_fecha_est.get()):
            messagebox.showerror("Fecha inválida", "Las fechas deben tener formato DD/MM/AAAA.")
            return

        id_libro = self._mapa_libros[etiqueta_libro]
        libro = self.libro_dao.obtener_por_id(id_libro)
        if not libro or libro.disponibles <= 0:
            messagebox.showerror("Sin disponibilidad", "No hay ejemplares disponibles de este libro.")
            return

        try:
            prestamo = Prestamo(
                id_libro=id_libro,
                tipo_solicitante=self.var_prestamo_tipo.get(),
                id_solicitante=self._mapa_solicitantes[etiqueta_solicitante],
                fecha_prestamo=self.var_prestamo_fecha.get().strip(),
                fecha_devolucion_estimada=self.var_prestamo_fecha_est.get().strip(),
                estado="Prestado",
            )
            self.prestamo_dao.insertar(prestamo)
            self.libro_dao.actualizar_disponibles(id_libro, -1)
        except ValueError as error:
            messagebox.showerror("Datos inválidos", str(error))
            return
        except Exception as error:
            messagebox.showerror("Error al guardar", f"No se pudo registrar el préstamo.\n{error}")
            return

        messagebox.showinfo("Éxito", "Préstamo registrado correctamente.")
        self._refrescar_prestamos()
        self._refrescar_libros()
        self._refrescar_combobox_libros_prestamo()

    def _registrar_devolucion(self):
        seleccion = self.tabla_prestamos.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un préstamo de la lista.")
            return
        valores = self.tabla_prestamos.item(seleccion[0], "values")
        id_prestamo, estado_actual = int(valores[0]), valores[7]
        if estado_actual == "Devuelto":
            messagebox.showinfo("Información", "Este préstamo ya fue devuelto.")
            return
        confirmar = messagebox.askyesno("Confirmar devolución", "¿Confirma la devolución de este libro?")
        if not confirmar:
            return
        try:
            prestamo = self.prestamo_dao.obtener_por_id(id_prestamo)
            self.prestamo_dao.registrar_devolucion(id_prestamo, datetime.now().strftime(FORMATO_FECHA))
            if prestamo:
                self.libro_dao.actualizar_disponibles(prestamo.id_libro, 1)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo registrar la devolución.\n{error}")
            return
        messagebox.showinfo("Éxito", "Devolución registrada correctamente.")
        self._refrescar_prestamos()
        self._refrescar_libros()
        self._refrescar_combobox_libros_prestamo()

    def _eliminar_prestamo(self):
        seleccion = self.tabla_prestamos.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un préstamo de la lista para eliminar.")
            return
        valores = self.tabla_prestamos.item(seleccion[0], "values")
        id_prestamo, estado = int(valores[0]), valores[7]
        confirmar = messagebox.askyesno("Confirmar eliminación", "¿Está seguro de eliminar este registro de préstamo?")
        if not confirmar:
            return
        try:
            prestamo = self.prestamo_dao.obtener_por_id(id_prestamo)
            self.prestamo_dao.eliminar(id_prestamo)
            if estado == "Prestado" and prestamo:
                self.libro_dao.actualizar_disponibles(prestamo.id_libro, 1)
        except Exception as error:
            messagebox.showerror("Error", f"No se pudo eliminar el préstamo.\n{error}")
            return
        messagebox.showinfo("Éxito", "Registro eliminado correctamente.")
        self._refrescar_prestamos()
        self._refrescar_libros()
        self._refrescar_combobox_libros_prestamo()

    def _refrescar_prestamos(self):
        for fila in self.tabla_prestamos.get_children():
            self.tabla_prestamos.delete(fila)
        for p in self.prestamo_dao.obtener_todos_detallado():
            self.tabla_prestamos.insert("", "end", values=(
                p["id_prestamo"], p["titulo_libro"], p["solicitante"], p["tipo_solicitante"],
                p["fecha_prestamo"], p["fecha_devolucion_estimada"],
                p["fecha_devolucion_real"] or "-", p["estado"],
            ))

    def _exportar_prestamos_pdf(self):
        self._exportar_treeview_pdf(self.tabla_prestamos, "Listado de préstamos",
                                     ("ID", "Libro", "Solicitante", "Tipo", "F. Préstamo",
                                      "F. Dev. Estimada", "F. Dev. Real", "Estado"))

    # ==================================================================
    # TAB BÚSQUEDA AVANZADA
    # ==================================================================
    def _construir_tab_busqueda(self):
        contenedor = self.tab_busqueda
        panel_filtros = ttk.LabelFrame(contenedor, text="Filtros de búsqueda de libros")
        panel_filtros.pack(fill="x", padx=8, pady=8)

        self.var_busq_titulo = tk.StringVar()
        self.var_busq_autor = tk.StringVar()
        self.var_busq_genero = tk.StringVar(value="Todos")
        self.var_busq_ciclo = tk.StringVar(value="Todos")
        self.var_busq_edad = tk.StringVar(value="Todos")
        self.var_busq_disponibles = tk.BooleanVar(value=False)

        ttk.Label(panel_filtros, text="Título").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(panel_filtros, textvariable=self.var_busq_titulo, width=20).grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(panel_filtros, text="Autor").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        ttk.Entry(panel_filtros, textvariable=self.var_busq_autor, width=20).grid(row=0, column=3, padx=4, pady=4)

        ttk.Label(panel_filtros, text="Género").grid(row=0, column=4, sticky="w", padx=4, pady=4)
        ttk.Combobox(panel_filtros, textvariable=self.var_busq_genero, values=["Todos"] + GENEROS,
                     state="readonly", width=16).grid(row=0, column=5, padx=4, pady=4)

        ttk.Label(panel_filtros, text="Ciclo").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Combobox(panel_filtros, textvariable=self.var_busq_ciclo, values=["Todos"] + CICLOS,
                     state="readonly", width=16).grid(row=1, column=1, padx=4, pady=4)

        ttk.Label(panel_filtros, text="Edad recomendada").grid(row=1, column=2, sticky="w", padx=4, pady=4)
        ttk.Combobox(panel_filtros, textvariable=self.var_busq_edad,
                     values=["Todos", "Sin especificar"] + EDADES_RECOMENDADAS,
                     state="readonly", width=16).grid(row=1, column=3, padx=4, pady=4)

        ttk.Checkbutton(panel_filtros, text="Sólo con ejemplares disponibles",
                         variable=self.var_busq_disponibles).grid(row=1, column=4, columnspan=2, sticky="w", padx=4, pady=4)

        panel_botones = ttk.Frame(contenedor)
        panel_botones.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(panel_botones, text="Buscar", command=self._ejecutar_busqueda).pack(side="left", padx=4)
        ttk.Button(panel_botones, text="Limpiar filtros", command=self._limpiar_busqueda).pack(side="left", padx=4)
        ttk.Button(panel_botones, text="Exportar resultados a PDF",
                   command=self._exportar_busqueda_pdf).pack(side="right", padx=4)

        columnas = ("id", "titulo", "autor", "editorial", "isbn", "genero", "edad", "ciclo", "stock", "disponibles")
        encabezados = ("ID", "Título", "Autor", "Editorial", "ISBN", "Género", "Edad", "Ciclo", "Stock", "Disp.")
        self.tabla_busqueda = ttk.Treeview(contenedor, columns=columnas, show="headings", height=13)
        for col, enc in zip(columnas, encabezados):
            self.tabla_busqueda.heading(col, text=enc)
            self.tabla_busqueda.column(col, width=100, anchor="center")
        self.tabla_busqueda.column("titulo", width=180, anchor="w")
        self.tabla_busqueda.column("autor", width=140, anchor="w")
        self.tabla_busqueda.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _limpiar_busqueda(self):
        self.var_busq_titulo.set("")
        self.var_busq_autor.set("")
        self.var_busq_genero.set("Todos")
        self.var_busq_ciclo.set("Todos")
        self.var_busq_edad.set("Todos")
        self.var_busq_disponibles.set(False)
        for fila in self.tabla_busqueda.get_children():
            self.tabla_busqueda.delete(fila)

    def _ejecutar_busqueda(self):
        resultados = self.libro_dao.busqueda_avanzada(
            titulo=self.var_busq_titulo.get().strip(),
            autor=self.var_busq_autor.get().strip(),
            genero=self.var_busq_genero.get(),
            ciclo=self.var_busq_ciclo.get(),
            edad=self.var_busq_edad.get(),
            solo_disponibles=self.var_busq_disponibles.get(),
        )
        for fila in self.tabla_busqueda.get_children():
            self.tabla_busqueda.delete(fila)
        for libro in resultados:
            self.tabla_busqueda.insert("", "end", values=(
                libro.id_libro, libro.titulo, libro.autor, libro.editorial, libro.isbn,
                libro.genero, libro.edad_recomendada, libro.ciclo, libro.stock, libro.disponibles,
            ))
        if not resultados:
            messagebox.showinfo("Búsqueda", "No se encontraron libros con esos criterios.")

    def _exportar_busqueda_pdf(self):
        self._exportar_treeview_pdf(self.tabla_busqueda, "Resultados de búsqueda avanzada",
                                     ("ID", "Título", "Autor", "Editorial", "ISBN",
                                      "Género", "Edad", "Ciclo", "Stock", "Disp."))

    # ==================================================================
    # Exportación a PDF (genérica, a partir de cualquier Treeview)
    # ==================================================================
    def _exportar_treeview_pdf(self, treeview, titulo_reporte, encabezados):
        filas = [treeview.item(item, "values") for item in treeview.get_children()]
        if not filas:
            messagebox.showwarning("Sin datos", "No hay registros para exportar.")
            return

        nombre_sugerido = titulo_reporte.lower().replace(" ", "_") + ".pdf"
        destino = filedialog.asksaveasfilename(
            title="Guardar PDF", defaultextension=".pdf",
            initialfile=nombre_sugerido, filetypes=[("Archivo PDF", "*.pdf")],
        )
        if not destino:
            return
        try:
            ExportadorPDF.exportar(destino, titulo_reporte, list(encabezados), filas)
        except Exception as error:
            messagebox.showerror("Error al exportar", f"No se pudo generar el PDF.\n{error}")
            return
        messagebox.showinfo("Exportación completa", f"PDF generado correctamente en:\n{destino}")
