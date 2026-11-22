"""
Descripcion: Genera el "Manual del cocinero" en formato Word (.docx).
Input: plan (lista de días de streamlit_app) y desglose (salida de calculate_shopping.main).
Output: bytes del documento .docx, listo para st.download_button.

El manual tiene:
  1. Quién es quién: tabla de dietas especiales con los nombres en blanco para rellenar.
  2. Cómo usar este manual.
  3. Normas de obligado cumplimiento (celíacos y sin lactosa), con nombres a rellenar.
  4. Un apartado por día con una tabla por comida: Base / Celíacos / Sin lactosa / TOTAL.
"""
from io import BytesIO

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Twips

# Colores y medidas del manual original
VERDE = "2E5E3A"
VERDE_OSCURO = "1F3D28"
VERDE_CLARO = "EAF2EC"
GRIS_BORDE = "BFBFBF"
FUENTE = "Calibri"
HUECO = "_________________________"

# Ingrediente | Base | Celíacos | Sin lactosa | TOTAL | Unidad  (suma 9360 twips = ancho útil)
ANCHOS = [2860, 1250, 1250, 1250, 1250, 1500]
DIETAS = ("Base", "Celíacos", "Lactosos")


# ---------- utilidades de formato ----------
def _num(x):
    """1.29 -> '1,29'; 21.0 -> '21'; None -> '?'."""
    if x is None:
        return "?"
    x = round(x, 2)
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def _shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def _bordes(table):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{lado}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), GRIS_BORDE)
        borders.append(b)
    tblPr.append(borders)


def _fila_cabecera(row):
    """Repite la cabecera si la tabla salta de página y evita partir filas."""
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:tblHeader"))


def _no_partir(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))


def _escribir(cell, texto, bold=False, color=None, align=None, size=10):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.space_before = Pt(1)
    if align:
        p.alignment = align
    run = p.add_run(texto)
    run.font.size = Pt(size)
    run.font.name = FUENTE
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def _tabla(doc, cabecera, filas, anchos, alinear_numeros=False, negrita_col=None, alto_fila=None):
    t = doc.add_table(rows=1, cols=len(cabecera))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    _bordes(t)
    for i, w in enumerate(anchos):
        t.columns[i].width = Twips(w)

    hdr = t.rows[0]
    _fila_cabecera(hdr)
    for i, texto in enumerate(cabecera):
        c = hdr.cells[i]
        c.width = Twips(anchos[i])
        _shade(c, VERDE)
        _escribir(c, texto, bold=True, color="FFFFFF")

    for n, fila in enumerate(filas):
        row = t.add_row()
        _no_partir(row)
        if alto_fila:
            row.height = alto_fila
            row.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
        for i, texto in enumerate(fila):
            c = row.cells[i]
            c.width = Twips(anchos[i])
            if n % 2 == 1:
                _shade(c, VERDE_CLARO)
            align = None
            if alinear_numeros and 0 < i < len(fila) - 1:
                align = WD_ALIGN_PARAGRAPH.RIGHT
            elif alinear_numeros and i == len(fila) - 1:
                align = WD_ALIGN_PARAGRAPH.CENTER
            _escribir(c, texto, bold=(i == negrita_col or (not alinear_numeros and i == 0)), align=align)
    # Mantener cada tabla entera en la misma página (todas las filas menos la última 'pegadas' a la siguiente)
    for row in t.rows[:-1]:
        for c in row.cells:
            for par in c.paragraphs:
                par.paragraph_format.keep_with_next = True
    return t


def _estilos(doc):
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Twips(11906), Twips(16838)  # A4
    sec.top_margin = sec.bottom_margin = Twips(1000)
    sec.left_margin = sec.right_margin = Twips(1100)

    def fuente(style, size, bold=False, color=None, before=0, after=0):
        f = style.font
        f.name = FUENTE
        f.size = Pt(size)
        f.bold = bold
        f.italic = False
        if color:
            f.color.rgb = RGBColor.from_string(color)
        rpr = style.element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is not None:  # quitar fuentes del tema (Calibri Light) para que mande Calibri
            for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
                rfonts.attrib.pop(qn(a), None)
            rfonts.set(qn("w:eastAsia"), FUENTE)
        pf = style.paragraph_format
        pf.space_before = Pt(before)
        pf.space_after = Pt(after)

    fuente(doc.styles["Normal"], 10.5, after=4)
    fuente(doc.styles["Title"], 20, bold=True, color=VERDE, after=6)
    # El estilo Title por defecto lleva una línea inferior: se quita
    ppr = doc.styles["Title"].element.get_or_add_pPr()
    for b in ppr.findall(qn("w:pBdr")):
        ppr.remove(b)
    fuente(doc.styles["Heading 1"], 14, bold=True, color=VERDE, before=8, after=5)
    fuente(doc.styles["Heading 2"], 11.5, bold=True, color=VERDE_OSCURO, before=7, after=3)
    for nombre in ("Heading 1", "Heading 2"):
        doc.styles[nombre].paragraph_format.keep_with_next = True


def _bullets(doc, textos):
    for t in textos:
        p = doc.add_paragraph(t, style="List Bullet")
        p.paragraph_format.space_after = Pt(2)


def _rango(valores):
    vals = sorted(set(valores))
    if not vals:
        return "0"
    return str(vals[0]) if len(vals) == 1 else f"{vals[0]}–{vals[-1]} según el día"


# ---------- documento ----------
def generar_manual(plan: list, desglose: dict) -> bytes:
    doc = Document()
    _estilos(doc)

    cel = [p.get("celiacos", 0) for p in plan]
    lac = [p.get("lactosos", 0) for p in plan]
    max_cel, max_lac = max(cel, default=0), max(lac, default=0)

    doc.add_paragraph("Manual del cocinero", style="Title")

    # 1. Quién es quién
    doc.add_heading("Quién es quién: dietas especiales con nombre", level=1)
    doc.add_paragraph(
        f"Los totales de las tablas (Celíacos = {_rango(cel)}, Sin lactosa = {_rango(lac)}) "
        "corresponden a estos chavales concretos. Tenedlos identificados en cocina para no "
        "confundir bandejas:"
    )
    _tabla(
        doc,
        ["Dieta", "Nombres", "Nota"],
        [
            [f"Celíacos ({max_cel})", "", "Usar SIEMPRE producto sin gluten y evitar contaminación cruzada"],
            [f"Sin lactosa ({max_lac})", "", "Usar producto sin lactosa cuando la tabla lo indique"],
            ["Caso individual", "", ""],
            ["Caso individual", "", ""],
            ["Caso individual", "", ""],
        ],
        [2960, 3200, 3200],
        alto_fila=Twips(620),
    )

    # 2. Cómo usar
    doc.add_heading("Cómo usar este manual", level=1)
    _bullets(doc, [
        "Cada día tiene una tabla por comida con el plato a cocinar y las cantidades exactas de cada ingrediente.",
        "Las columnas Base / Celíacos / Sin lactosa indican cuántos comensales (pax) hay de cada dieta y "
        "cuánto ingrediente les corresponde. La columna TOTAL suma las tres y es la cantidad total a preparar.",
        "Cuando un ingrediente aparece solo en la columna de Celíacos o Sin lactosa (por ejemplo «Galletas sin "
        "gluten y sin lactosa»), es el sustituto que reemplaza al ingrediente estándar para esa dieta: no se suma al de Base.",
        "Un guion (—) significa que ese ingrediente no se usa para esa dieta.",
    ])

    # 3. Normas
    doc.add_heading("Normas de obligado cumplimiento", level=1)
    p = doc.add_paragraph()
    p.add_run(f"Celíacos — {HUECO}:").bold = True
    _bullets(doc, [
        "Usar SIEMPRE los productos marcados «sin gluten»: pan, pasta/macarrones, galletas y sazonadores.",
        "Cocinar la pasta sin gluten en agua y cazuela aparte, con utensilios limpios. Nunca usar el mismo "
        "agua, aceite o pinzas que para el menú base.",
        "Emplatar sus raciones primero, en zona limpia, antes de manipular harina o pan normal.",
    ])
    p = doc.add_paragraph()
    p.add_run(f"Sin lactosa — {HUECO}:").bold = True
    _bullets(doc, [
        "Usar los productos marcados «sin lactosa» que indique la tabla: leche, queso, yogur y postres.",
        "Revisar la etiqueta de embutidos, rebozados y salsas: muchos llevan leche aunque no lo parezca.",
        "Servir sus raciones aparte y antes de añadir queso o nata al resto.",
    ])

    # 4. Días
    for dia_plan in plan:
        dia = dia_plan["dia"]
        filas_dia = desglose.get(dia, [])
        if not filas_dia:
            continue
        h = doc.add_heading(dia, level=1)
        h.paragraph_format.page_break_before = True

        # Agrupar por comida manteniendo el orden del plan
        comidas = {}
        for r in filas_dia:
            comidas.setdefault((r["Comida"], r["Plato"]), []).append(r)

        for (comida, plato), filas in comidas.items():
            doc.add_heading(f"{comida} — {plato}", level=2)

            pax = {d: 0 for d in DIETAS}
            ingredientes = {}  # (nombre, unidad) -> {dieta: cantidad}, en orden de aparición
            for r in filas:
                pax[r["Dieta"]] = r["Pax Final"]
                key = (r["Ingrediente"], r["Unidad"])
                ingredientes.setdefault(key, {})
                prev = ingredientes[key].get(r["Dieta"], 0)
                ingredientes[key][r["Dieta"]] = None if r["Cantidad"] is None else (prev or 0) + r["Cantidad"]

            cab = [
                "Ingrediente",
                f"Base ({pax['Base']} pax)",
                f"Celíacos ({pax['Celíacos']} pax)",
                f"Sin lactosa ({pax['Lactosos']} pax)",
                "TOTAL",
                "Unidad",
            ]
            filas_tabla = []
            for (nombre, unidad), cant in ingredientes.items():
                celdas = [_num(cant[d]) if d in cant else "—" for d in DIETAS]
                valores = [v for v in cant.values()]
                total = None if any(v is None for v in valores) else sum(valores)
                filas_tabla.append([nombre, *celdas, _num(total), unidad])
            _tabla(doc, cab, filas_tabla, ANCHOS, alinear_numeros=True, negrita_col=4)

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()
