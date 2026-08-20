"""
exportador_pdf.py
Módulo encargado de generar planillas en PDF a partir de los datos que se
están visualizando en la interfaz (catálogo de libros, listado de préstamos
o resultados de una búsqueda avanzada).

Utiliza la librería reportlab. Se mantiene separado de la lógica de negocio
y de persistencia: sólo recibe encabezados y filas de datos ya procesados
por la GUI.
"""

from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


class ExportadorPDF:
    """Genera reportes en PDF a partir de encabezados y filas de una tabla."""

    NOMBRE_INSTITUCION = "Biblioteca Escolar"

    @staticmethod
    def exportar(ruta_archivo, titulo_reporte, encabezados, filas):
        """
        Genera un PDF con una tabla.

        - ruta_archivo: ruta completa donde se guardará el PDF.
        - titulo_reporte: título que aparece en el encabezado del documento.
        - encabezados: lista de strings con los nombres de columna.
        - filas: lista de tuplas/listas con los datos de cada fila.
        """
        documento = SimpleDocTemplate(
            ruta_archivo, pagesize=landscape(A4),
            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        )
        estilos = getSampleStyleSheet()
        elementos = []

        elementos.append(Paragraph(ExportadorPDF.NOMBRE_INSTITUCION, estilos["Title"]))
        elementos.append(Paragraph(titulo_reporte, estilos["Heading2"]))
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        elementos.append(Paragraph(f"Generado el: {fecha_generacion}", estilos["Normal"]))
        elementos.append(Spacer(1, 0.5 * cm))

        datos_tabla = [list(encabezados)] + [list(fila) for fila in filas]

        tabla = Table(datos_tabla, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ]))
        elementos.append(tabla)

        elementos.append(Spacer(1, 0.5 * cm))
        elementos.append(Paragraph(f"Total de registros: {len(filas)}", estilos["Normal"]))

        documento.build(elementos)
