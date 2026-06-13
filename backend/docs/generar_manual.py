# -*- coding: utf-8 -*-
# docs/generar_manual.py
# Genera el MANUAL TÉCNICO de SIOL-SAVA en PDF (reportlab).
# Ejecutar:  python docs/generar_manual.py   ->  MANUAL_SIOL_SAVA.pdf
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Preformatted, ListFlowable, ListItem, HRFlowable, KeepTogether,
)

# ----------------------------------------------------------------------------
# Paleta y estilos
# ----------------------------------------------------------------------------
AZUL = colors.HexColor("#1F4E79")
AZUL2 = colors.HexColor("#2E75B6")
GRIS = colors.HexColor("#F2F2F2")
GRIS_BORDE = colors.HexColor("#CCCCCC")
VERDE = colors.HexColor("#2E7D32")
NARANJA = colors.HexColor("#E08A00")
ROJO = colors.HexColor("#C0392B")

METODO_COLOR = {"GET": VERDE, "POST": AZUL2, "PATCH": NARANJA, "DELETE": ROJO}

styles = getSampleStyleSheet()
S = {}
S["titulo"] = ParagraphStyle("titulo", parent=styles["Title"], fontSize=26, textColor=AZUL, spaceAfter=6, leading=30)
S["subtitulo"] = ParagraphStyle("subtitulo", parent=styles["Normal"], fontSize=13, textColor=colors.HexColor("#555555"), alignment=TA_CENTER, leading=18)
S["h1"] = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=17, textColor=colors.white, backColor=AZUL, borderPadding=(6, 8, 6, 8), spaceBefore=16, spaceAfter=10, leading=22)
S["h2"] = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, textColor=AZUL, spaceBefore=12, spaceAfter=6, leading=17)
S["body"] = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, alignment=TA_JUSTIFY, leading=14, spaceAfter=6)
S["small"] = ParagraphStyle("small", parent=styles["Normal"], fontSize=9, leading=12)
S["lbl"] = ParagraphStyle("lbl", parent=styles["Normal"], fontSize=9, textColor=AZUL, leading=12)
S["val"] = ParagraphStyle("val", parent=styles["Normal"], fontSize=9, leading=12)
S["code"] = ParagraphStyle("code", parent=styles["Code"], fontName="Courier", fontSize=8, leading=10, textColor=colors.HexColor("#1A1A1A"))
S["mblanco"] = ParagraphStyle("mblanco", parent=styles["Normal"], fontName="Courier-Bold", fontSize=10, textColor=colors.white, leading=13)
S["bblanco"] = ParagraphStyle("bblanco", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10, textColor=colors.white, alignment=TA_CENTER, leading=13)
S["cell"] = ParagraphStyle("cell", parent=styles["Normal"], fontSize=9, leading=12)
S["cellb"] = ParagraphStyle("cellb", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=AZUL)


def P(t, st="body"):
    return Paragraph(t, S[st])


def code(txt):
    return Preformatted(txt, S["code"])


def bullets(items):
    return ListFlowable(
        [ListItem(P(it, "small"), leftIndent=10, value="•") for it in items],
        bulletType="bullet", start="•", leftIndent=14,
    )


def tabla(data, anchos, header=True):
    t = Table(data, colWidths=anchos, repeatRows=1 if header else 0)
    estilo = [
        ("GRID", (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        estilo += [
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
        ]
    t.setStyle(TableStyle(estilo))
    return t


def endpoint(metodo, ruta, rol, proposito, entrada, salida, conexion):
    """Bloque visual de un endpoint."""
    color = METODO_COLOR.get(metodo, AZUL)
    barra = Table([[P(metodo, "bblanco"), P(ruta, "mblanco")]], colWidths=[2.3 * cm, 13.2 * cm])
    barra.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), color),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#33444F")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    entrada_flow = entrada if not isinstance(entrada, str) else P(entrada, "val")
    salida_flow = salida if not isinstance(salida, str) else P(salida, "val")
    attr = Table([
        [P("Rol requerido", "lbl"), P(rol, "val")],
        [P("Para qué sirve", "lbl"), P(proposito, "val")],
        [P("Entrada (inputs)", "lbl"), entrada_flow],
        [P("Respuesta", "lbl"), salida_flow],
        [P("Se conecta con", "lbl"), P(conexion, "val")],
    ], colWidths=[3.3 * cm, 12.2 * cm])
    attr.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("BACKGROUND", (0, 0), (0, -1), GRIS),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return KeepTogether([barra, attr, Spacer(1, 10)])


# ----------------------------------------------------------------------------
# Decoración de página (encabezado + pie con número)
# ----------------------------------------------------------------------------
def _decorar(canvas, doc):
    canvas.saveState()
    w, h = A4
    if doc.page > 1:
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawString(2 * cm, h - 1.2 * cm, "Manual Técnico — SIOL-SAVA Backend")
        canvas.setStrokeColor(GRIS_BORDE)
        canvas.line(2 * cm, h - 1.35 * cm, w - 2 * cm, h - 1.35 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.drawCentredString(w / 2, 1.1 * cm, f"Página {doc.page}")
    canvas.restoreState()


# ----------------------------------------------------------------------------
# Contenido
# ----------------------------------------------------------------------------
def build():
    story = []

    # ---- PORTADA ----
    story.append(Spacer(1, 4 * cm))
    story.append(P("Manual Técnico", "titulo"))
    story.append(P("SIOL-SAVA — Backend de Gestión y Trazabilidad de Entregas de Última Milla", "subtitulo"))
    story.append(Spacer(1, 0.6 * cm))
    story.append(HRFlowable(width="60%", thickness=2, color=AZUL2, spaceBefore=4, spaceAfter=20))
    story.append(Spacer(1, 1 * cm))
    port = tabla([
        [P("Proyecto", "cellb"), P("SIOL-SAVA (MVP de tesis)", "cell")],
        [P("Componente", "cellb"), P("API Backend (FastAPI)", "cell")],
        [P("Versión", "cellb"), P("1.0.0", "cell")],
        [P("Fecha", "cellb"), P("Junio 2026", "cell")],
        [P("Stack", "cellb"), P("Python 3.11 · FastAPI · PostgreSQL 15 · SQLAlchemy · Alembic · Docker", "cell")],
        [P("Arquitectura", "cellb"), P("Clean Architecture (api → service → repository → models)", "cell")],
    ], [4 * cm, 11.5 * cm], header=False)
    story.append(port)
    story.append(PageBreak())

    # ---- ÍNDICE ----
    story.append(P("Índice", "h1"))
    indice = [
        "1. Introducción y stack tecnológico",
        "2. Arquitectura limpia (cómo se conecta todo)",
        "3. Puesta en marcha (Docker, variables de entorno)",
        "4. Conceptos clave (códigos legibles, roles, estados)",
        "5. Autenticación: cómo obtener y usar el token",
        "6. Catálogo de APIs (módulo por módulo)",
        "7. Flujo completo de extremo a extremo",
        "8. Seguridad (OWASP, secretos, CI/CD)",
        "9. Apéndice: mapa de archivos del proyecto",
    ]
    story.append(bullets(indice))
    story.append(PageBreak())

    # ---- 1. INTRODUCCIÓN ----
    story.append(P("1. Introducción y stack tecnológico", "h1"))
    story.append(P(
        "SIOL-SAVA es un sistema de gestión y trazabilidad de entregas logísticas de última milla. "
        "Este backend expone una API REST que consumen dos clientes: el <b>panel web del administrador</b> "
        "(carga de pedidos, armado de rutas, monitoreo) y la <b>app móvil del conductor</b> "
        "(descarga de ruta, validación de paquetes, registro de entregas con evidencia).", "body"))
    story.append(P("El backend cubre 4 fases funcionales:", "body"))
    story.append(bullets([
        "<b>Fase 1 — Autenticación:</b> usuarios, roles y tokens JWT.",
        "<b>Fase 2 — Inbound y motor logístico:</b> carga de pedidos por Excel, geocodificación, zonas y armado/optimización de rutas (VRP).",
        "<b>Fase 3 — Operaciones de última milla:</b> endpoints de la app móvil del conductor.",
        "<b>Fase 4 — Trazabilidad y CI/CD:</b> dashboard, historial de paquetes y automatización.",
    ]))
    story.append(P("Tecnologías:", "h2"))
    story.append(tabla([
        [P("Componente", "cellb"), P("Tecnología", "cellb"), P("Para qué", "cellb")],
        [P("Lenguaje", "cell"), P("Python 3.11", "cell"), P("Lógica del servidor", "cell")],
        [P("Framework API", "cell"), P("FastAPI", "cell"), P("Endpoints REST + documentación Swagger automática", "cell")],
        [P("Base de datos", "cell"), P("PostgreSQL 15", "cell"), P("Almacenamiento de datos", "cell")],
        [P("ORM", "cell"), P("SQLAlchemy", "cell"), P("Acceso a datos sin SQL manual (evita inyección)", "cell")],
        [P("Migraciones", "cell"), P("Alembic", "cell"), P("Control de versiones del esquema de la BD", "cell")],
        [P("Geocodificación", "cell"), P("Geopy (Nominatim)", "cell"), P("Convertir direcciones en coordenadas", "cell")],
        [P("Excel", "cell"), P("Pandas + openpyxl", "cell"), P("Leer la carga masiva de pedidos", "cell")],
        [P("Contenedores", "cell"), P("Docker + Docker Compose", "cell"), P("Levantar API y BD con un comando", "cell")],
        [P("Seguridad", "cell"), P("JWT (python-jose) + Argon2 (passlib)", "cell"), P("Tokens y cifrado de contraseñas", "cell")],
    ], [3.3 * cm, 4.7 * cm, 7.5 * cm]))
    story.append(PageBreak())

    # ---- 2. ARQUITECTURA ----
    story.append(P("2. Arquitectura limpia (cómo se conecta todo)", "h1"))
    story.append(P(
        "El código está organizado en <b>capas</b>. Cada petición fluye de arriba hacia abajo, y cada capa "
        "solo habla con la siguiente. Esto mantiene el código ordenado, testeable y fácil de mantener.", "body"))
    story.append(tabla([
        [P("Capa", "cellb"), P("Carpeta", "cellb"), P("Responsabilidad", "cellb")],
        [P("API / Router", "cell"), P("app/api/", "cell"), P("Recibe la petición HTTP, valida permisos (rol) y delega. No tiene lógica.", "cell")],
        [P("Servicio", "cell"), P("app/services/", "cell"), P("La lógica de negocio (reglas, validaciones, orquestación).", "cell")],
        [P("Repositorio", "cell"), P("app/repositories/", "cell"), P("Único lugar que consulta/escribe en la base de datos.", "cell")],
        [P("Modelo", "cell"), P("app/models/", "cell"), P("Definición de las tablas (SQLAlchemy).", "cell")],
        [P("Schema", "cell"), P("app/schemas/", "cell"), P("Moldes de datos de entrada/salida (Pydantic) que validan tipos.", "cell")],
        [P("Core", "cell"), P("app/core/", "cell"), P("Seguridad (JWT, hash), configuración y códigos legibles.", "cell")],
        [P("DB", "cell"), P("app/db/", "cell"), P("Conexión y sesión de la base de datos.", "cell")],
    ], [2.8 * cm, 3.4 * cm, 9.3 * cm]))
    story.append(Spacer(1, 8))
    story.append(P("Flujo de una petición (ejemplo: consultar la ruta activa):", "h2"))
    story.append(code(
        "Cliente (Swagger / App)\n"
        "   |  GET /api/conductor/ruta-activa  (con token JWT)\n"
        "   v\n"
        "api/conductor.py      -> verifica rol 'conductor' (deps.py)\n"
        "   v\n"
        "services/ruta_service -> aplica la lógica de negocio\n"
        "   v\n"
        "repositories/ruta_repository -> consulta la BD\n"
        "   v\n"
        "models/ruta.py (tabla 'rutas')  -> PostgreSQL\n"
        "   ^  la respuesta sube por las mismas capas (validada por schemas)"
    ))
    story.append(PageBreak())

    # ---- 3. PUESTA EN MARCHA ----
    story.append(P("3. Puesta en marcha", "h1"))
    story.append(P("Requisitos: tener <b>Docker Desktop</b> instalado y corriendo.", "body"))
    story.append(P("Paso 1 — Variables de entorno:", "h2"))
    story.append(P("Copia la plantilla y ajusta los valores (la clave secreta, credenciales, etc.):", "body"))
    story.append(code("copy .env.example .env     (Windows)\ncp .env.example .env       (Linux/Mac)"))
    story.append(P("Paso 2 — Levantar todo (API + base de datos):", "h2"))
    story.append(code("docker compose down -v && docker compose up --build"))
    story.append(P("El <b>-v</b> recrea la base de datos desde cero (necesario tras cambios de esquema). "
                   "Al arrancar se crean las tablas y un <b>admin inicial</b> automáticamente.", "small"))
    story.append(P("Paso 3 — Abrir la documentación interactiva (Swagger):", "h2"))
    story.append(code("http://localhost:8000/docs"))
    story.append(P("Desde Swagger puedes probar TODOS los endpoints con el botón «Try it out». "
                   "El endpoint de salud <b>GET /</b> confirma que el backend está vivo.", "small"))
    story.append(PageBreak())

    # ---- 4. CONCEPTOS CLAVE ----
    story.append(P("4. Conceptos clave", "h1"))
    story.append(P("Códigos legibles", "h2"))
    story.append(P("Cada registro tiene un <b>id</b> numérico interno (para las relaciones) y un <b>codigo</b> "
                   "legible para identificarlo a simple vista:", "body"))
    story.append(tabla([
        [P("Tabla", "cellb"), P("Código", "cellb"), P("Ejemplo", "cellb")],
        [P("usuarios (admin)", "cell"), P("AD-NNN", "cell"), P("AD-001", "cell")],
        [P("usuarios (conductor)", "cell"), P("CO-NNN", "cell"), P("CO-002", "cell")],
        [P("clientes_corporativos", "cell"), P("CL-NNN", "cell"), P("CL-001", "cell")],
        [P("vehiculos", "cell"), P("VE-NNN", "cell"), P("VE-001", "cell")],
        [P("pedidos", "cell"), P("PD-NNN", "cell"), P("PD-001 (es el tracking / lo que va en el QR)", "cell")],
        [P("rutas", "cell"), P("RT-NNN", "cell"), P("RT-001", "cell")],
        [P("ruta_detalles", "cell"), P("RD-NNN", "cell"), P("RD-001", "cell")],
        [P("historial_pedidos", "cell"), P("HP-NNN", "cell"), P("HP-001", "cell")],
    ], [5 * cm, 3.5 * cm, 7 * cm]))
    story.append(Spacer(1, 6))
    story.append(P("Roles de usuario", "h2"))
    story.append(bullets([
        "<b>admin</b>: panel web. Gestiona clientes, vehículos, pedidos, rutas y monitoreo.",
        "<b>conductor</b>: app móvil. Solo opera SU ruta del día.",
    ]))
    story.append(P("Estados (máquina de estados)", "h2"))
    story.append(tabla([
        [P("Entidad", "cellb"), P("Estados posibles", "cellb")],
        [P("Pedido", "cell"), P("PENDIENTE → ASIGNADO → EN_RUTA → ENTREGADO / FALLIDO (o GEOCODIFICACION_FALLIDA)", "cell")],
        [P("Ruta", "cell"), P("CREADA → EN_PROGRESO → FINALIZADA", "cell")],
        [P("Entrega (detalle)", "cell"), P("PENDIENTE → ENTREGADO / FALLIDO", "cell")],
    ], [3.5 * cm, 12 * cm]))
    story.append(PageBreak())

    # ---- 5. AUTENTICACIÓN ----
    story.append(P("5. Autenticación: cómo obtener y usar el token", "h1"))
    story.append(P(
        "Casi todos los endpoints están protegidos. Para usarlos necesitas un <b>token JWT</b>, que se obtiene "
        "iniciando sesión. El token se envía en la cabecera <font name='Courier'>Authorization: Bearer &lt;token&gt;</font>.", "body"))
    story.append(P("En Swagger es automático:", "h2"))
    story.append(bullets([
        "Pulsa el botón verde «Authorize» (arriba a la derecha).",
        "Escribe el correo en el campo «username» y la contraseña. Deja vacíos client_id/secret.",
        "A partir de ahí Swagger manda el token en cada petición. El candado pasa de abierto a cerrado.",
        "El token dura 8 horas; si caduca (error 401), vuelve a autorizar.",
        "Swagger guarda UN token: para cambiar de admin a conductor haz Logout y entra de nuevo.",
    ]))
    story.append(P("Admin inicial (para el primer ingreso):", "h2"))
    story.append(P("Al arrancar se crea automáticamente un administrador con las credenciales definidas en el "
                   "<font name='Courier'>.env</font> (por defecto <b>admin@siol.com / admin123</b>). "
                   "Con él inicias sesión y das de alta al resto de usuarios.", "small"))
    story.append(PageBreak())

    # ---- 6. CATÁLOGO DE APIs ----
    story.append(P("6. Catálogo de APIs (módulo por módulo)", "h1"))
    story.append(P("Para cada endpoint se indica: rol requerido, para qué sirve, los datos de entrada, "
                   "la respuesta y con qué partes del sistema se conecta.", "body"))

    # 6.1 Autenticación
    story.append(P("6.1 Autenticación  (/api/auth)", "h2"))
    story.append(endpoint(
        "POST", "/api/auth/login", "Público (sin token)",
        "Inicia sesión y entrega el token JWT que usarán el resto de endpoints.",
        code('Formulario (x-www-form-urlencoded):\n  username = correo\n  password = contraseña'),
        code('{\n  "access_token": "eyJhbGciOi...",\n  "token_type": "bearer"\n}'),
        "usuario_service → usuario_repository → tabla usuarios; core/security (verifica hash + firma JWT).",
    ))
    story.append(endpoint(
        "POST", "/api/auth/registro", "admin",
        "Da de alta un usuario (admin o conductor). Solo un admin puede hacerlo (evita escalada de privilegios).",
        code('{\n  "correo": "conductor@siol.com",\n  "contrasena": "clave123",\n  "rol": "conductor"\n}'),
        code('{\n  "id": 2, "codigo": "CO-002",\n  "correo": "conductor@siol.com",\n  "rol": "conductor", "estado": true\n}'),
        "usuario_service → usuario_repository; el rol se valida con un Enum (admin/conductor).",
    ))

    # 6.2 Clientes
    story.append(P("6.2 Clientes corporativos  (/api/clientes)", "h2"))
    story.append(endpoint(
        "GET", "/api/clientes/", "admin",
        "Lista las empresas cliente (las que envían los paquetes).",
        "Ninguno.",
        code('[ { "id": 1, "codigo": "CL-001",\n    "razon_social": "ACME SAC",\n    "identificador_unico": "20100000001",\n    "contacto": null } ]'),
        "cliente_service → cliente_repository → tabla clientes_corporativos.",
    ))
    story.append(endpoint(
        "POST", "/api/clientes/", "admin",
        "Registra una empresa cliente. (También se crean solas al cargar el Excel de pedidos.)",
        code('{\n  "razon_social": "ACME SAC",\n  "identificador_unico": "20100000001",\n  "contacto": "ventas@acme.com"\n}'),
        "El cliente creado (con su codigo CL-NNN).",
        "cliente_service (rechaza RUC duplicado) → cliente_repository.",
    ))

    # 6.3 Vehículos
    story.append(P("6.3 Flota de vehículos  (/api/vehiculos)", "h2"))
    story.append(endpoint(
        "GET", "/api/vehiculos/", "admin",
        "Lista la flota de vehículos.",
        "Ninguno.",
        code('[ { "id": 1, "codigo": "VE-001", "placa": "ABC-123",\n    "marca": "Toyota", "capacidad_volumetrica": 5.0,\n    "estado": "DISPONIBLE", "conductor_id": 2 } ]'),
        "vehiculo_service → vehiculo_repository → tabla vehiculos.",
    ))
    story.append(endpoint(
        "POST", "/api/vehiculos/", "admin",
        "Registra un vehículo. Si conductor_id es null, el vehículo es de la empresa; si no, es del conductor.",
        code('{\n  "placa": "ABC-123", "marca": "Toyota",\n  "capacidad_volumetrica": 5.0,\n  "estado": "DISPONIBLE", "conductor_id": 2\n}'),
        "El vehículo creado (con su codigo VE-NNN).",
        "vehiculo_service (rechaza placa duplicada) → vehiculo_repository; conductor_id → tabla usuarios.",
    ))

    # 6.4 Pedidos
    story.append(P("6.4 Gestión de pedidos / Inbound  (/api/pedidos)", "h2"))
    story.append(endpoint(
        "POST", "/api/pedidos/upload", "admin",
        "Carga masiva de pedidos desde un Excel (.xlsx). Crea/enlaza el cliente, guarda el destinatario, "
        "asigna el código PD-NNN y registra el primer evento de trazabilidad.",
        code('Archivo .xlsx (multipart). Columnas:\n'
             '  direccion_destino        (obligatoria)\n'
             '  razon_social_cliente     (obligatoria)\n'
             '  ruc_cliente              (opcional)\n'
             '  nombre_destinatario      (opcional)\n'
             '  telefono_destinatario    (opcional)\n'
             '  dni_destinatario         (opcional)\n'
             '  referencia_externa       (opcional, id del Excel)\n'
             '  peso_kg, volumen_m3      (opcional)'),
        code('{\n  "mensaje": "Carga masiva exitosa",\n  "pedidos_nuevos": 5,\n  "total_filas_leidas": 5\n}'),
        "pedido_service → pedido_repository + cliente_repository + historial_repository.",
    ))
    story.append(endpoint(
        "GET", "/api/pedidos/", "admin",
        "Lista los pedidos (paginado).",
        code('Query (opcional): skip=0 & limit=100'),
        "Lista de pedidos con todos sus campos (codigo PD-NNN, cliente, destinatario, estado, etc.).",
        "pedido_service → pedido_repository.",
    ))
    story.append(endpoint(
        "POST", "/api/pedidos/geocodificar", "admin",
        "Convierte las direcciones en coordenadas (lat/lng) y deduce el distrito. Tarda ~1 s por pedido.",
        "Ninguno (procesa los pedidos sin coordenadas).",
        code('{\n  "mensaje": "Proceso ... finalizado",\n  "pedidos_exitosos": 5,\n  "pedidos_fallidos": 0\n}'),
        "pedido_service → geocoder (Geopy/Nominatim) → pedido_repository.",
    ))
    story.append(endpoint(
        "GET", "/api/pedidos/zonas", "admin",
        "Agrupa los pedidos geocodificados por distrito (para decidir las rutas).",
        "Ninguno.",
        code('{ "zonas_operativas": [\n   { "distrito": "San Miguel", "total_pedidos": 3 },\n   { "distrito": "Miraflores", "total_pedidos": 2 } ] }'),
        "pedido_service → pedido_repository (agrupación SQL).",
    ))

    # 6.5 Rutas
    story.append(P("6.5 Enrutamiento  (/api/rutas)", "h2"))
    story.append(endpoint(
        "POST", "/api/rutas/asignar-bloque", "admin",
        "Crea una ruta para un conductor con TODOS los pedidos PENDIENTES de un distrito (CUS-18).",
        code('{\n  "nombre_ruta": "Ruta San Miguel - Mañana",\n  "distrito": "San Miguel",\n  "conductor_id": 2\n}'),
        code('{\n  "mensaje": "3 pedidos asignados...",\n  "ruta_id": 1, "codigo": "RT-001"\n}'),
        "ruta_service → ruta_repository + pedido_repository + historial_repository.",
    ))
    story.append(endpoint(
        "POST", "/api/rutas/conductor/optimizar", "conductor",
        "El conductor optimiza el ORDEN de entrega de SU ruta desde su posición actual (algoritmo del "
        "vecino más cercano). Verifica que la ruta sea suya.",
        code('{\n  "ruta_id": 1,\n  "latitud_actual_conductor": -12.077,\n  "longitud_actual_conductor": -77.083\n}'),
        code('{\n  "mensaje": "Ruta optimizada matemáticamente",\n  "total_paradas": 3\n}'),
        "ruta_service → services/router (VRP) → ruta_repository + historial_repository.",
    ))

    # 6.6 Conductor
    story.append(P("6.6 App móvil del conductor  (/api/conductor)", "h2"))
    story.append(P("Todos exigen rol <b>conductor</b>. El conductor se identifica por su token (nunca por parámetro), "
                   "así nunca puede ver la ruta de otro.", "small"))
    story.append(endpoint(
        "GET", "/api/conductor/ruta-activa", "conductor",
        "Devuelve el resumen de la ruta activa del conductor y su avance (CUS-21).",
        "Ninguno (se deduce del token).",
        code('{ "ruta_id": 1, "codigo": "RT-001", "nombre": "...",\n  "estado": "EN_PROGRESO", "total_paradas": 3,\n  "pendientes": 1, "entregadas": 2, "fallidas": 0 }'),
        "ruta_service → ruta_repository.",
    ))
    story.append(endpoint(
        "GET", "/api/conductor/ruta-activa/manifiesto", "conductor",
        "Lista detallada de paradas, ordenadas por secuencia, con datos del destinatario (CUS-24).",
        "Ninguno.",
        code('{ "ruta_id": 1, "codigo": "RT-001", "paradas": [\n  { "secuencia": 1, "codigo": "PD-001",\n    "cliente_origen": "ACME SAC",\n    "nombre_destinatario": "Juan Perez",\n    "direccion_destino": "...", "estado_entrega": "PENDIENTE" } ] }'),
        "ruta_service → ruta_repository.",
    ))
    story.append(endpoint(
        "GET", "/api/conductor/ruta-activa/navegacion", "conductor",
        "Waypoints (lat/lng) ordenados para alimentar el mapa de la app (CUS-25).",
        "Ninguno.",
        code('{ "ruta_id": 1, "total_paradas": 3, "paradas": [\n  { "secuencia": 1, "codigo": "PD-001",\n    "latitud": -12.07, "longitud": -77.08 } ] }'),
        "ruta_service → ruta_repository.",
    ))
    story.append(endpoint(
        "POST", "/api/conductor/almacen/validar-qr", "conductor",
        "Valida si el paquete escaneado (código PD-NNN del QR) pertenece a la ruta del conductor (CUS-22).",
        code('{ "codigo": "PD-001" }'),
        code('{ "pertenece": true,\n  "mensaje": "Paquete validado...",\n  "parada": { ... } }'),
        "ruta_service → ruta_repository (busca el pedido por su codigo).",
    ))
    story.append(endpoint(
        "PATCH", "/api/conductor/paradas/{pedido_id}/estado", "conductor",
        "Marca una entrega como ENTREGADO o FALLIDO. Si es FALLIDO, el motivo es obligatorio (CUS-26). "
        "Registra el evento en el historial.",
        code('Ruta: pedido_id en la URL\n{\n  "estado": "ENTREGADO"\n}\n// o:  { "estado": "FALLIDO",\n//        "motivo_fallo": "Cliente ausente" }'),
        code('{ "pedido_id": 1, "codigo": "PD-001",\n  "estado_entrega": "ENTREGADO",\n  "fecha_gestion": "2026-06-06T15:00:00",\n  "mensaje": "Pedido marcado como ENTREGADO" }'),
        "ruta_service → ruta_repository + historial_repository.",
    ))
    story.append(endpoint(
        "POST", "/api/conductor/paradas/{pedido_id}/evidencia", "conductor",
        "Sube la foto de prueba de entrega (POD). Solo acepta imágenes (CUS-29).",
        code('Archivo de imagen (.jpg/.png/.webp) en multipart (campo "file").'),
        code('{ "pedido_id": 1, "codigo": "PD-001",\n  "url_evidencia": "/media/evidencias/pod_1_1.jpg",\n  "mensaje": "Evidencia (POD) cargada correctamente" }'),
        "ruta_service guarda el archivo en uploads/evidencias y la URL en el detalle. Se sirve en /media.",
    ))
    story.append(endpoint(
        "POST", "/api/conductor/ruta-activa/finalizar", "conductor",
        "Da por finalizada la ruta del día (CUS-28). Devuelve el resumen de entregas.",
        "Ninguno.",
        code('{ "ruta_id": 1, "codigo": "RT-001",\n  "estado": "FINALIZADA",\n  "entregadas": 2, "fallidas": 1, "pendientes": 0,\n  "mensaje": "Ruta finalizada correctamente" }'),
        "ruta_service → ruta_repository.",
    ))

    # 6.7 Dashboard
    story.append(P("6.7 Dashboard y trazabilidad  (/api/dashboard)", "h2"))
    story.append(endpoint(
        "GET", "/api/dashboard/resumen", "admin",
        "KPIs globales: total de pedidos por estado y conteo de rutas (CUS-33).",
        "Ninguno.",
        code('{ "total_pedidos": 5,\n  "pedidos_por_estado": {"ENTREGADO": 2, "PENDIENTE": 3},\n  "total_rutas": 1, "rutas_activas": 1, "rutas_finalizadas": 0 }'),
        "dashboard_service → pedido_repository + ruta_repository.",
    ))
    story.append(endpoint(
        "GET", "/api/dashboard/flota", "admin",
        "Estado y avance (%) de todas las rutas, con el conductor asignado (CUS-33).",
        "Ninguno.",
        code('{ "total_rutas": 1, "rutas": [\n  { "ruta_id": 1, "nombre": "...", "estado": "EN_PROGRESO",\n    "conductor_correo": "c@siol.com", "total_paradas": 3,\n    "entregadas": 2, "avance_porcentaje": 66.7 } ] }'),
        "dashboard_service → ruta_repository + usuario_repository.",
    ))
    story.append(endpoint(
        "GET", "/api/dashboard/pedidos/{codigo}/historial", "admin",
        "Línea de tiempo COMPLETA de un paquete por su código PD-NNN (CUS-35): cada cambio de estado, "
        "cuándo y quién lo hizo.",
        code('Ruta: el codigo del pedido en la URL (ej. PD-001)'),
        code('{ "codigo": "PD-001", "estado_actual": "ENTREGADO",\n  "ruta_asignada": "RT-001",\n  "eventos": [\n   {"evento":"PENDIENTE","realizado_por":"admin@siol.com"},\n   {"evento":"ASIGNADO", ...},\n   {"evento":"EN_RUTA", "realizado_por":"c@siol.com"},\n   {"evento":"ENTREGADO", ...} ] }'),
        "dashboard_service → historial_repository (tabla historial_pedidos) + pedido/ruta.",
    ))
    story.append(PageBreak())

    # ---- 7. FLUJO END-TO-END ----
    story.append(P("7. Flujo completo de extremo a extremo", "h1"))
    story.append(P("Este es el orden correcto de uso. Los datos que se generan (códigos) se usan en los pasos siguientes.", "body"))
    story.append(P("Lado ADMIN (panel web):", "h2"))
    story.append(bullets([
        "Inicia sesión (admin) y autoriza en Swagger.",
        "(Opcional) Registra conductores y vehículos.",
        "POST /api/pedidos/upload — sube el Excel. Se crean clientes (CL-) y pedidos (PD-).",
        "POST /api/pedidos/geocodificar — calcula coordenadas y distritos.",
        "GET /api/pedidos/zonas — revisa cuántos pedidos hay por distrito.",
        "POST /api/rutas/asignar-bloque — crea la ruta (RT-) para un conductor.",
    ]))
    story.append(P("Lado CONDUCTOR (app móvil):", "h2"))
    story.append(bullets([
        "Inicia sesión (conductor) y autoriza.",
        "POST /api/rutas/conductor/optimizar — ordena su ruta.",
        "GET /api/conductor/ruta-activa, /manifiesto, /navegacion — descarga su trabajo.",
        "POST /api/conductor/almacen/validar-qr — valida cada paquete (PD-) en el almacén.",
        "PATCH /api/conductor/paradas/{id}/estado — marca ENTREGADO/FALLIDO.",
        "POST /api/conductor/paradas/{id}/evidencia — sube la foto POD.",
        "POST /api/conductor/ruta-activa/finalizar — cierra la ruta del día.",
    ]))
    story.append(P("Lado ADMIN (monitoreo, en cualquier momento):", "h2"))
    story.append(bullets([
        "GET /api/dashboard/resumen y /flota — ve el avance en vivo.",
        "GET /api/dashboard/pedidos/PD-001/historial — la trazabilidad completa de un paquete.",
    ]))
    story.append(PageBreak())

    # ---- 8. SEGURIDAD ----
    story.append(P("8. Seguridad", "h1"))
    story.append(P("El backend implementa medidas alineadas con OWASP Top 10 y buenas prácticas.", "body"))

    story.append(P("8.1 Autenticación y mínimo privilegio", "h2"))
    story.append(bullets([
        "<b>Contraseñas con Argon2</b> (hash moderno). Nunca se guardan en texto plano.",
        "<b>Token JWT</b> firmado (HS256), con expiración. Se envía como «Authorization: Bearer».",
        "<b>Control por rol</b>: cada endpoint exige admin o conductor (dependencias get_current_admin / get_current_conductor).",
        "<b>Verificación de propiedad</b>: un conductor solo accede a SU ruta, no a la de otros.",
        "<b>Registro cerrado</b>: solo un admin puede crear usuarios; el rol se valida con un Enum. Esto evita la escalada de privilegios (que cualquiera se cree admin).",
    ]))
    story.append(P("8.2 Gestión de secretos (sin credenciales en el código)", "h2"))
    story.append(bullets([
        "La clave del JWT, las credenciales de la BD y el CORS se leen de <b>variables de entorno</b> (módulo app/core/config.py).",
        "El archivo <font name='Courier'>.env</font> está en .gitignore (no se sube al repositorio). Hay una plantilla <font name='Courier'>.env.example</font>.",
    ]))
    story.append(P("8.3 Configuración y comunicación", "h2"))
    story.append(bullets([
        "<b>CORS configurable</b> por entorno (no abierto a todo en producción).",
        "<b>Sin inyección SQL</b>: todo el acceso a datos usa el ORM (consultas parametrizadas).",
        "<b>Validación de archivos</b>: el Excel valida extensión; la evidencia solo acepta imágenes.",
    ]))
    story.append(P("8.4 Trazabilidad / auditoría", "h2"))
    story.append(P("La tabla <b>historial_pedidos</b> registra cada cambio de estado con su fecha y el usuario que lo hizo. "
                   "Es un rastro de auditoría de todas las operaciones.", "small"))
    story.append(P("8.5 Gestión de vulnerabilidades y CI/CD", "h2"))
    story.append(bullets([
        "<b>Dependencias con versión fija</b> (requirements.txt) para poder rastrear CVEs.",
        "<b>GitHub Actions</b> (.github/workflows/ci.yml): en cada push corre pruebas (pytest), análisis estático de seguridad (bandit) y auditoría de dependencias (pip-audit).",
        "<b>Dependabot</b> (.github/dependabot.yml): abre PRs semanales con actualizaciones de seguridad.",
        "<b>Secret Scanning</b>: se activa en GitHub (Settings → Code security) para detectar secretos filtrados.",
    ]))
    story.append(P("8.6 Cumplimiento OWASP Top 10 (resumen)", "h2"))
    story.append(tabla([
        [P("Riesgo", "cellb"), P("Estado", "cellb"), P("Medida", "cellb")],
        [P("A01 Control de acceso", "cell"), P("Cubierto", "cell"), P("RBAC + propiedad + registro solo-admin", "cell")],
        [P("A02 Fallos criptográficos", "cell"), P("Cubierto", "cell"), P("Argon2 + secretos en entorno", "cell")],
        [P("A03 Inyección", "cell"), P("Cubierto", "cell"), P("ORM parametrizado", "cell")],
        [P("A05 Mala configuración", "cell"), P("Parcial", "cell"), P("CORS por entorno (faltan headers/TLS en despliegue)", "cell")],
        [P("A06 Componentes vulnerables", "cell"), P("Cubierto", "cell"), P("Pin + Dependabot + pip-audit", "cell")],
        [P("A07 Fallos de autenticación", "cell"), P("Parcial", "cell"), P("JWT + Argon2 (falta rate-limit)", "cell")],
        [P("A09 Registro y monitoreo", "cell"), P("Parcial", "cell"), P("historial_pedidos como auditoría", "cell")],
    ], [4.5 * cm, 2.5 * cm, 8.5 * cm]))
    story.append(Spacer(1, 6))
    story.append(P("Pendiente para producción", "h2"))
    story.append(bullets([
        "Proteger las fotos /media tras autenticación (hoy públicas, para simplificar el frontend).",
        "Rate-limiting en el login (anti fuerza bruta) y límite de tamaño de archivos.",
        "Cabeceras de seguridad (HSTS, etc.) y HTTPS/TLS en el despliegue.",
        "Política de contraseñas y refresh tokens.",
    ]))
    story.append(PageBreak())

    # ---- 9. APÉNDICE ----
    story.append(P("9. Apéndice: mapa de archivos del proyecto", "h1"))
    story.append(code(
        "app/\n"
        "  main.py                 # arranque: crea app, tablas, admin inicial, routers\n"
        "  core/\n"
        "    config.py             # configuración desde variables de entorno (secretos)\n"
        "    security.py           # hash de contraseñas (Argon2) + JWT\n"
        "    codigos.py            # generación de códigos legibles (PD-001...)\n"
        "  db/database.py          # conexión y sesión de PostgreSQL\n"
        "  api/                    # routers (entrada HTTP)\n"
        "    auth, clientes, vehiculos, pedidos, rutas, conductor, dashboard, deps\n"
        "  services/               # lógica de negocio\n"
        "  repositories/           # acceso a datos (queries)\n"
        "  models/                 # tablas SQLAlchemy\n"
        "  schemas/                # moldes Pydantic (validación de entrada/salida)\n"
        "alembic/                  # migraciones de la base de datos\n"
        ".github/workflows/ci.yml  # CI/CD (pruebas + seguridad)\n"
        ".github/dependabot.yml    # actualizaciones de dependencias\n"
        "tests/                    # pruebas automáticas (pytest)\n"
        "docker-compose.yml        # API + base de datos\n"
        ".env.example              # plantilla de variables de entorno\n"
        "SEGURIDAD.md              # detalle de seguridad\n"
        "GUIA_PRUEBAS.md           # guía paso a paso para probar"
    ))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=GRIS_BORDE))
    story.append(Spacer(1, 6))
    story.append(P("<i>Fin del manual — SIOL-SAVA Backend v1.0.0</i>", "small"))
    return story


def main():
    salida = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "MANUAL_SIOL_SAVA.pdf")
    doc = SimpleDocTemplate(
        salida, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=1.8 * cm,
        title="Manual Técnico - SIOL-SAVA Backend", author="Equipo SIOL-SAVA",
    )
    doc.build(build(), onFirstPage=_decorar, onLaterPages=_decorar)
    print(f"PDF generado: {salida}")


if __name__ == "__main__":
    main()
