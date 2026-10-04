import requests
import json
import os
import webbrowser
import re
from datetime import datetime, timedelta
from html import escape


# ===========================================================================
# CONFIGURACIÓN
# ===========================================================================

NIT = "901532463"

BASE_URL = "https://wsmipres.sispro.gov.co/WSMIPRESNOPBS/api"

# Archivo de caché del Token
TOKEN_CACHE_FILE = ".mipres_token_cache.json"

# Carpeta donde se guardarán los resultados
RESULTADOS_DIR = "resultados_mipres"

# Tiempo de espera de las peticiones
REQUEST_TIMEOUT = 120


# ===========================================================================
# CREAR CARPETA DE RESULTADOS
# ===========================================================================

def crear_carpeta_resultados():

    if not os.path.exists(RESULTADOS_DIR):
        os.makedirs(RESULTADOS_DIR)


# ===========================================================================
# GESTIÓN DEL TOKEN
# ===========================================================================

def load_token_from_cache():

    if not os.path.exists(TOKEN_CACHE_FILE):
        return None

    try:

        with open(
            TOKEN_CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        expires_at = datetime.fromisoformat(
            data["expires_at"]
        )

        if datetime.now() < expires_at:
            return data["token"]

    except (
        json.JSONDecodeError,
        KeyError,
        ValueError
    ):
        pass

    return None


def save_token_to_cache(token):

    expires_at = (
        datetime.now()
        + timedelta(hours=24)
    )

    data = {
        "token": token,
        "expires_at": expires_at.isoformat()
    }

    with open(
        TOKEN_CACHE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


def clear_token_cache():

    if os.path.exists(TOKEN_CACHE_FILE):
        os.remove(TOKEN_CACHE_FILE)


def get_token_interactive():

    token = input(
        "\nIngresa el TOKEN de MIPRES: "
    ).strip()

    if token:
        save_token_to_cache(token)

    return token


def obtener_token():

    token = load_token_from_cache()

    if token is None:

        print(
            "\nNo se encontró un Token válido."
        )

        token = get_token_interactive()

    return token


def renovar_token():

    print(
        "\nEl Token es inválido o expiró."
    )

    clear_token_cache()

    return get_token_interactive()


# ===========================================================================
# DETECCIÓN DE TOKEN INVÁLIDO
# ===========================================================================

def respuesta_indica_token_invalido(data):

    if not isinstance(data, dict):
        return False

    message = str(
        data.get("Message", "")
    ).upper()

    palabras = [
        "TOKEN INVALID",
        "TOKEN INVÁLIDO",
        "TOKEN INVALIDO",
        "TOKEN EXPIR",
        "TOKEN NO VÁLIDO",
        "TOKEN NO VALIDO"
    ]

    return any(
        palabra in message
        for palabra in palabras
    )


# ===========================================================================
# PETICIONES GET
# ===========================================================================

def ejecutar_get(url):

    headers = {
        "Accept": "application/json"
    }

    try:

        print("\nConsultando MIPRES...")

        response = requests.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )

        print(
            f"HTTP {response.status_code}"
        )

        if response.status_code in (401, 403):

            return None, "TOKEN_INVALID"

        response.raise_for_status()

        try:

            data = response.json()

        except json.JSONDecodeError:

            print(
                "\nLa respuesta del servidor "
                "no tiene formato JSON."
            )

            print(
                response.text[:2000]
            )

            return None, "ERROR"

        if respuesta_indica_token_invalido(data):

            return None, "TOKEN_INVALID"

        return data, "OK"

    except requests.exceptions.Timeout:

        print(
            "\nLa solicitud superó el tiempo "
            "máximo de espera."
        )

        return None, "ERROR"

    except requests.exceptions.ConnectionError:

        print(
            "\nNo fue posible establecer conexión "
            "con el servidor MIPRES."
        )

        return None, "ERROR"

    except requests.exceptions.RequestException as e:

        print(
            f"\nError en la petición:\n{e}"
        )

        return None, "ERROR"


# ===========================================================================
# PETICIONES POST
# ===========================================================================

def ejecutar_post(url, body):

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:

        print("\nConsultando MIPRES...")

        response = requests.post(
            url,
            headers=headers,
            json=body,
            timeout=REQUEST_TIMEOUT
        )

        print(
            f"HTTP {response.status_code}"
        )

        if response.status_code in (401, 403):

            return None, "TOKEN_INVALID"

        response.raise_for_status()

        try:

            data = response.json()

        except json.JSONDecodeError:

            print(
                "\nLa respuesta del servidor "
                "no tiene formato JSON."
            )

            print(
                response.text[:2000]
            )

            return None, "ERROR"

        if respuesta_indica_token_invalido(data):

            return None, "TOKEN_INVALID"

        return data, "OK"

    except requests.exceptions.Timeout:

        print(
            "\nLa solicitud superó el tiempo "
            "máximo de espera."
        )

        return None, "ERROR"

    except requests.exceptions.ConnectionError:

        print(
            "\nNo fue posible establecer conexión "
            "con el servidor MIPRES."
        )

        return None, "ERROR"

    except requests.exceptions.RequestException as e:

        print(
            f"\nError en la petición:\n{e}"
        )

        return None, "ERROR"


# ===========================================================================
# 1. TODAS LAS PRESCRIPCIONES DE EPS/IPS POR FECHA
# ===========================================================================

def consultar_prescripciones_fecha(fecha):

    token = obtener_token()

    url = (
        f"{BASE_URL}/Prescripcion/"
        f"{NIT}/{fecha}/{token}"
    )

    resultado, estado = ejecutar_get(url)

    if estado == "TOKEN_INVALID":

        token = renovar_token()

        url = (
            f"{BASE_URL}/Prescripcion/"
            f"{NIT}/{fecha}/{token}"
        )

        resultado, estado = ejecutar_get(url)

    return resultado, estado


# ===========================================================================
# 2. PRESCRIPCIONES DE UN PACIENTE
# ===========================================================================

def consultar_prescripciones_paciente(
    fecha,
    tipo_documento,
    numero_documento
):

    token = obtener_token()

    url = (
        f"{BASE_URL}/PrescripcionPaciente/"
        f"{NIT}/{fecha}/{token}/"
        f"{tipo_documento}/{numero_documento}"
    )

    resultado, estado = ejecutar_get(url)

    if estado == "TOKEN_INVALID":

        token = renovar_token()

        url = (
            f"{BASE_URL}/PrescripcionPaciente/"
            f"{NIT}/{fecha}/{token}/"
            f"{tipo_documento}/{numero_documento}"
        )

        resultado, estado = ejecutar_get(url)

    return resultado, estado


# ===========================================================================
# 3. ANEXO TÉCNICO POR NÚMERO DE PRESCRIPCIÓN
# ===========================================================================

def consultar_prescripcion_numero(
    numero_prescripcion
):

    token = obtener_token()

    url = (
        f"{BASE_URL}/PrescripcionXNumero/"
        f"{NIT}/{token}/{numero_prescripcion}"
    )

    resultado, estado = ejecutar_get(url)

    if estado == "TOKEN_INVALID":

        token = renovar_token()

        url = (
            f"{BASE_URL}/PrescripcionXNumero/"
            f"{NIT}/{token}/{numero_prescripcion}"
        )

        resultado, estado = ejecutar_get(url)

    return resultado, estado


# ===========================================================================
# 4. TODAS LAS NOVEDADES DE EPS/IPS POR FECHA
# ===========================================================================

def consultar_novedades_fecha(fecha):

    token = obtener_token()

    url = (
        f"{BASE_URL}/NovedadesPrescripcion/"
        f"{NIT}/{fecha}/{token}"
    )

    resultado, estado = ejecutar_get(url)

    if estado == "TOKEN_INVALID":

        token = renovar_token()

        url = (
            f"{BASE_URL}/NovedadesPrescripcion/"
            f"{NIT}/{fecha}/{token}"
        )

        resultado, estado = ejecutar_get(url)

    return resultado, estado


# ===========================================================================
# 5. ANEXO TÉCNICO PARA VARIAS PRESCRIPCIONES
# ===========================================================================

def consultar_prescripciones_masivas(
    lista_prescripciones
):

    token = obtener_token()

    url = (
        f"{BASE_URL}/PrescripcionXMany/"
        f"{NIT}/{token}"
    )

    # MIPRES espera una colección de strings:
    #
    # [
    #     "123456789",
    #     "123456790",
    #     "123456791"
    # ]

    body = lista_prescripciones

    resultado, estado = ejecutar_post(
        url,
        body
    )

    if estado == "TOKEN_INVALID":

        token = renovar_token()

        url = (
            f"{BASE_URL}/PrescripcionXMany/"
            f"{NIT}/{token}"
        )

        resultado, estado = ejecutar_post(
            url,
            body
        )

    return resultado, estado


# ===========================================================================
# 6. NOVEDADES PARA VARIAS PRESCRIPCIONES
# ===========================================================================

def consultar_novedades_masivas(
    lista_prescripciones
):

    token = obtener_token()

    url = (
        f"{BASE_URL}/NovedadesPrescripcionXMany/"
        f"{NIT}/{token}"
    )

    # MIPRES espera una colección de strings:
    #
    # [
    #     "123456789",
    #     "123456790",
    #     "123456791"
    # ]

    body = lista_prescripciones

    resultado, estado = ejecutar_post(
        url,
        body
    )

    if estado == "TOKEN_INVALID":

        token = renovar_token()

        url = (
            f"{BASE_URL}/NovedadesPrescripcionXMany/"
            f"{NIT}/{token}"
        )

        resultado, estado = ejecutar_post(
            url,
            body
        )

    return resultado, estado


# ===========================================================================
# SOLICITAR FECHA
# ===========================================================================

def solicitar_fecha():

    while True:

        fecha = input(
            "\nFecha (AAAA-MM-DD): "
        ).strip()

        try:

            datetime.strptime(
                fecha,
                "%Y-%m-%d"
            )

            return fecha

        except ValueError:

            print(
                "Fecha inválida."
            )

            print(
                "Utilice el formato AAAA-MM-DD."
            )


# ===========================================================================
# SOLICITAR TIPO DE DOCUMENTO
# ===========================================================================

def solicitar_tipo_documento():

    print("\nTipos de documento habituales:")

    print(
        "CC = Cédula de ciudadanía"
    )

    print(
        "CE = Cédula de extranjería"
    )

    print(
        "TI = Tarjeta de identidad"
    )

    print(
        "RC = Registro civil"
    )

    print(
        "PA = Pasaporte"
    )

    print(
        "PE = Permiso especial de permanencia"
    )

    print(
        "PT = Permiso por protección temporal"
    )

    tipo = input(
        "\nTipo de documento: "
    ).strip().upper()

    return tipo


# ===========================================================================
# SOLICITAR LISTA DE PRESCRIPCIONES
# ===========================================================================

def solicitar_lista_prescripciones():

    print("\nIngrese los números de prescripción.")

    print(
        "Puede utilizar:"
    )

    print(
        "  - un número por línea"
    )

    print(
        "  - números separados por coma"
    )

    print(
        "  - números separados por punto y coma"
    )

    print(
        "  - números separados por espacios"
    )

    print(
        "\nPresione ENTER sobre una línea vacía "
        "para finalizar.\n"
    )

    numeros = []

    while True:

        linea = input("> ").strip()

        if not linea:
            break

        # Normalizar separadores
        linea = linea.replace(",", " ")
        linea = linea.replace(";", " ")
        linea = linea.replace("\t", " ")

        partes = linea.split()

        for numero in partes:

            numero = numero.strip()

            if not numero:
                continue

            # Evitar duplicados
            if numero not in numeros:
                numeros.append(numero)

    return numeros


# ===========================================================================
# APLANAR JSON
# ===========================================================================

def aplanar_json(
    data,
    prefijo="",
    nivel=0,
    filas=None
):

    if filas is None:
        filas = []

    # -----------------------------------------------------------------------
    # Diccionario
    # -----------------------------------------------------------------------

    if isinstance(data, dict):

        if not data:

            filas.append(
                (
                    prefijo or "(raíz)",
                    "{}",
                    nivel,
                    "valor"
                )
            )

            return filas

        for k, v in data.items():

            ruta = (
                f"{prefijo}.{k}"
                if prefijo
                else str(k)
            )

            if isinstance(v, dict):

                filas.append(
                    (
                        ruta,
                        f"objeto ({len(v)} campos)",
                        nivel,
                        "objeto"
                    )
                )

                aplanar_json(
                    v,
                    ruta,
                    nivel + 1,
                    filas
                )

            elif isinstance(v, list):

                filas.append(
                    (
                        ruta,
                        f"lista ({len(v)} elementos)",
                        nivel,
                        "lista"
                    )
                )

                aplanar_json(
                    v,
                    ruta,
                    nivel + 1,
                    filas
                )

            else:

                filas.append(
                    (
                        ruta,
                        formatear_valor(v),
                        nivel,
                        "valor"
                    )
                )

        return filas

    # -----------------------------------------------------------------------
    # Lista
    # -----------------------------------------------------------------------

    if isinstance(data, list):

        if not data:

            filas.append(
                (
                    prefijo or "(lista)",
                    "[]",
                    nivel,
                    "valor"
                )
            )

            return filas

        for i, item in enumerate(data):

            ruta = f"{prefijo}[{i}]"

            if isinstance(item, dict):

                filas.append(
                    (
                        ruta,
                        f"objeto ({len(item)} campos)",
                        nivel,
                        "objeto"
                    )
                )

                aplanar_json(
                    item,
                    ruta,
                    nivel + 1,
                    filas
                )

            elif isinstance(item, list):

                filas.append(
                    (
                        ruta,
                        f"lista ({len(item)} elementos)",
                        nivel,
                        "lista"
                    )
                )

                aplanar_json(
                    item,
                    ruta,
                    nivel + 1,
                    filas
                )

            else:

                filas.append(
                    (
                        ruta,
                        formatear_valor(item),
                        nivel,
                        "valor"
                    )
                )

        return filas

    # -----------------------------------------------------------------------
    # Valor simple
    # -----------------------------------------------------------------------

    filas.append(
        (
            prefijo or "(raíz)",
            formatear_valor(data),
            nivel,
            "valor"
        )
    )

    return filas


# ===========================================================================
# FORMATEAR VALORES PARA HTML
# ===========================================================================

def formatear_valor(valor):

    if valor is None:

        return (
            '<span class="v-null">'
            'null'
            '</span>'
        )

    if isinstance(valor, bool):

        return (
            '<span class="v-bool">'
            f'{str(valor).lower()}'
            '</span>'
        )

    if isinstance(valor, (int, float)):

        return (
            '<span class="v-num">'
            f'{valor}'
            '</span>'
        )

    if isinstance(valor, str):

        return (
            '<span class="v-str">'
            f'{escape(valor)}'
            '</span>'
        )

    return (
        '<span class="v-str">'
        f'{escape(str(valor))}'
        '</span>'
    )


# ===========================================================================
# GENERAR HTML
# ===========================================================================

def generar_html(
    resultado,
    titulo="Consulta MIPRES"
):

    fecha_consulta = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    filas = aplanar_json(resultado)

    filas_html = []

    for ruta, valor, nivel, tipo in filas:

        indent = (
            "&nbsp;&nbsp;&nbsp;&nbsp;"
            * nivel
        )

        icono = {
            "objeto": "📦",
            "lista": "📋",
            "valor": "•"
        }.get(tipo, "")

        clase_fila = (
            f"nivel-{min(nivel, 5)} "
            f"tipo-{tipo}"
        )

        ruta_esc = escape(ruta)

        filas_html.append(
            f'<tr class="{clase_fila}" '
            f'data-nivel="{nivel}" '
            f'data-ruta="{ruta_esc}">'

            f'<td class="col-ruta">'
            f'{indent}'
            f'<span class="icono">{icono}</span> '
            f'{ruta_esc}'
            f'</td>'

            f'<td class="col-valor">'
            f'{valor}'
            f'</td>'

            f'</tr>'
        )

    tabla_filas = "\n".join(
        filas_html
    )

    json_crudo = escape(
        json.dumps(
            resultado,
            indent=2,
            ensure_ascii=False
        )
    )

    html = f"""<!DOCTYPE html>

<html lang="es">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>{escape(titulo)}</title>

<style>

:root {{
    --primary: #0b5ed7;
    --primary-dark: #083b8a;
    --bg: #f4f6f9;
    --card: #ffffff;
    --text: #1f2937;
    --muted: #6b7280;
    --border: #e5e7eb;
    --hover: #eef4ff;
}}

* {{
    box-sizing: border-box;
}}

body {{
    font-family:
        "Segoe UI",
        Roboto,
        Arial,
        sans-serif;

    background: var(--bg);

    color: var(--text);

    margin: 0;

    padding: 24px;
}}

.container {{
    max-width: 1200px;

    margin: 0 auto;

    background: var(--card);

    border-radius: 12px;

    box-shadow:
        0 4px 16px
        rgba(0, 0, 0, 0.08);

    overflow: hidden;
}}

header {{
    background:
        linear-gradient(
            135deg,
            var(--primary),
            var(--primary-dark)
        );

    color: white;

    padding: 24px 32px;
}}

header h1 {{
    margin: 0 0 6px 0;

    font-size: 1.5rem;

    font-weight: 600;
}}

header p {{
    margin: 0;

    opacity: .9;
}}

.toolbar {{
    display: flex;

    gap: 10px;

    flex-wrap: wrap;

    align-items: center;

    padding: 16px 32px;

    background: #f9fafb;

    border-bottom:
        1px solid var(--border);
}}

.toolbar input {{
    flex: 1;

    min-width: 250px;

    padding: 9px 12px;

    border:
        1px solid var(--border);

    border-radius: 8px;

    font-size: .9rem;

    outline: none;
}}

.toolbar input:focus {{
    border-color:
        var(--primary);
}}

.toolbar button {{
    padding: 9px 14px;

    border:
        1px solid var(--border);

    background: white;

    border-radius: 8px;

    cursor: pointer;

    font-size: .85rem;
}}

.toolbar button:hover {{
    background: var(--hover);

    border-color:
        var(--primary);
}}

.contador {{
    color: var(--muted);

    font-size: .85rem;

    margin-left: auto;
}}

.content {{
    padding:
        0 32px 24px 32px;
}}

table.mipres {{
    width: 100%;

    border-collapse:
        collapse;

    font-size: .9rem;

    border:
        1px solid var(--border);

    margin-top: 16px;
}}

table.mipres thead {{
    background:
        var(--primary);

    color: white;

    position: sticky;

    top: 0;

    z-index: 2;
}}

table.mipres th {{
    padding: 10px 14px;

    text-align: left;

    font-weight: 600;

    font-size: .85rem;
}}

table.mipres td {{
    padding: 8px 14px;

    border-bottom:
        1px solid var(--border);

    vertical-align: top;

    font-family:
        "Consolas",
        "Monaco",
        monospace;

    font-size: .86rem;

    word-break: break-word;
}}

table.mipres tbody tr:hover {{
    background:
        var(--hover);
}}

table.mipres tbody tr.hidden {{
    display: none;
}}

.col-ruta {{
    width: 55%;
}}

.col-valor {{
    width: 45%;
}}

.icono {{
    display: inline-block;

    width: 20px;
}}

.v-null {{
    color: #9ca3af;

    font-style: italic;
}}

.v-num {{
    color: #b45309;

    font-weight: 600;
}}

.v-bool {{
    color: #047857;

    font-weight: 600;
}}

.tipo-objeto
.col-ruta {{
    font-weight: 600;

    color:
        var(--primary-dark);
}}

.tipo-lista
.col-ruta {{
    font-weight: 600;

    color: #7c3aed;
}}

.tipo-valor
.col-ruta {{
    color: var(--muted);
}}

.json-view {{
    display: none;

    margin-top: 16px;

    background: #1e1e1e;

    color: #d4d4d4;

    border-radius: 8px;

    padding: 16px;

    font-family:
        "Consolas",
        "Monaco",
        monospace;

    font-size: .82rem;

    overflow-x: auto;

    white-space: pre;

    max-height: 600px;

    overflow-y: auto;
}}

.json-view.visible {{
    display: block;
}}

footer {{
    padding: 16px 32px;

    background: #f9fafb;

    color: var(--muted);

    font-size: .82rem;

    border-top:
        1px solid var(--border);

    text-align: center;
}}

</style>

</head>

<body>

<div class="container">

<header>

<h1>
{escape(titulo)}
</h1>

<p>
Consulta generada el
{fecha_consulta}
</p>

</header>


<div class="toolbar">

<input
    type="search"
    id="buscador"
    placeholder="Buscar por ruta o valor..."
>

<button onclick="expandirTodo()">
    Expandir todo
</button>

<button onclick="contraerTodo()">
    Contraer todo
</button>

<button onclick="toggleJson()">
    Ver JSON original
</button>

<span
    class="contador"
    id="contador"
></span>

</div>


<div class="content">

<table
    class="mipres"
    id="tabla"
>

<thead>

<tr>

<th>
Ruta / campo
</th>

<th>
Valor
</th>

</tr>

</thead>


<tbody id="cuerpo">

{tabla_filas}

</tbody>

</table>


<pre
    class="json-view"
    id="jsonView"
>{json_crudo}</pre>

</div>


<footer>

NIT: {escape(NIT)}

</footer>

</div>


<script>

const buscador =
    document.getElementById(
        "buscador"
    );

const cuerpo =
    document.getElementById(
        "cuerpo"
    );

const contador =
    document.getElementById(
        "contador"
    );


function filtrar() {{

    const q =
        buscador.value
            .toLowerCase()
            .trim();

    const filas =
        cuerpo.querySelectorAll(
            "tr"
        );

    let visibles = 0;

    filas.forEach(fila => {{

        const texto =
            fila.textContent
                .toLowerCase();

        const coincide =
            !q ||
            texto.includes(q);

        fila.classList.toggle(
            "hidden",
            !coincide
        );

        if (coincide) {{
            visibles++;
        }}

    }});

    contador.textContent =
        visibles +
        " / " +
        filas.length +
        " filas visibles";
}}


buscador.addEventListener(
    "input",
    filtrar
);


function expandirTodo() {{

    buscador.value = "";

    const filas =
        cuerpo.querySelectorAll(
            "tr"
        );

    filas.forEach(fila => {{
        fila.classList.remove(
            "hidden"
        );
    }});

    filtrar();
}}


function contraerTodo() {{

    buscador.value = "";

    const filas =
        cuerpo.querySelectorAll(
            "tr"
        );

    filas.forEach(fila => {{

        const nivel =
            parseInt(
                fila.dataset.nivel,
                10
            );

        fila.classList.toggle(
            "hidden",
            nivel > 0
        );

    }});

    contador.textContent =
        "Vista contraída";
}}


function toggleJson() {{

    const jsonView =
        document.getElementById(
            "jsonView"
        );

    jsonView.classList.toggle(
        "visible"
    );

}}


filtrar();

</script>

</body>

</html>
"""

    return html


# ===========================================================================
# NOMBRE SEGURO PARA ARCHIVOS
# ===========================================================================

def nombre_seguro(texto):

    texto = str(texto)

    texto = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        texto
    )

    texto = texto.replace(
        " ",
        "_"
    )

    return texto


# ===========================================================================
# GUARDAR RESULTADO
# ===========================================================================

def guardar_resultado(
    resultado,
    titulo,
    identificador="resultado"
):

    crear_carpeta_resultados()

    marca_tiempo = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    identificador = nombre_seguro(
        identificador
    )

    base = (
        f"{marca_tiempo}_"
        f"{identificador}"
    )

    # -----------------------------------------------------------------------
    # JSON
    # -----------------------------------------------------------------------

    archivo_json = os.path.join(
        RESULTADOS_DIR,
        f"{base}.json"
    )

    with open(
        archivo_json,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            resultado,
            f,
            indent=2,
            ensure_ascii=False
        )

    # -----------------------------------------------------------------------
    # HTML
    # -----------------------------------------------------------------------

    archivo_html = os.path.join(
        RESULTADOS_DIR,
        f"{base}.html"
    )

    html = generar_html(
        resultado,
        titulo
    )

    with open(
        archivo_html,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html)

    ruta_html = os.path.abspath(
        archivo_html
    )

    ruta_json = os.path.abspath(
        archivo_json
    )

    print("\n" + "=" * 60)

    print(
        "RESULTADO GUARDADO"
    )

    print("=" * 60)

    print(
        f"\nHTML:\n{ruta_html}"
    )

    print(
        f"\nJSON:\n{ruta_json}"
    )

    print("=" * 60)

    # Abrir HTML automáticamente
    webbrowser.open(
        f"file://{ruta_html}"
    )


# ===========================================================================
# MENÚ
# ===========================================================================

def mostrar_menu():

    print("\n")

    print("=" * 65)

    print(
        "                       CONSULTA MIPRES"
    )

    print("=" * 65)

    print(
        "1. Prescripciones de la IPS por fecha"
    )

    print(
        "2. Prescripciones de un paciente"
    )

    print(
        "3. Anexo técnico por número de prescripción"
    )

    print(
        "4. Novedades de la IPS por fecha"
    )

    print(
        "5. Anexo técnico para varias prescripciones"
    )

    print(
        "6. Novedades para varias prescripciones"
    )

    print(
        "0. Salir"
    )

    print("=" * 65)


# ===========================================================================
# EJECUCIÓN DE UNA OPCIÓN
# ===========================================================================

def ejecutar_opcion(opcion):

    # =======================================================================
    # OPCIÓN 1
    # =======================================================================

    if opcion == "1":

        fecha = solicitar_fecha()

        resultado, estado = \
            consultar_prescripciones_fecha(
                fecha
            )

        if estado == "OK":

            guardar_resultado(
                resultado,
                f"Prescripciones MIPRES - {fecha}",
                f"prescripciones_{fecha}"
            )

        else:

            print(
                "\nLa consulta falló."
            )

    # =======================================================================
    # OPCIÓN 2
    # =======================================================================

    elif opcion == "2":

        fecha = solicitar_fecha()

        tipo_documento = \
            solicitar_tipo_documento()

        numero_documento = input(
            "\nNúmero de documento: "
        ).strip()

        if not numero_documento:

            print(
                "\nDebe ingresar un número "
                "de documento."
            )

            return

        resultado, estado = \
            consultar_prescripciones_paciente(
                fecha,
                tipo_documento,
                numero_documento
            )

        if estado == "OK":

            identificador = (
                f"paciente_"
                f"{tipo_documento}_"
                f"{numero_documento}_"
                f"{fecha}"
            )

            guardar_resultado(
                resultado,
                "Prescripciones del paciente",
                identificador
            )

        else:

            print(
                "\nLa consulta falló."
            )

    # =======================================================================
    # OPCIÓN 3
    # =======================================================================

    elif opcion == "3":

        numero = input(
            "\nNúmero de prescripción: "
        ).strip()

        if not numero:

            print(
                "\nDebe ingresar un número "
                "de prescripción."
            )

            return

        resultado, estado = \
            consultar_prescripcion_numero(
                numero
            )

        if estado == "OK":

            guardar_resultado(
                resultado,
                f"Prescripción MIPRES {numero}",
                f"prescripcion_{numero}"
            )

        else:

            print(
                "\nLa consulta falló."
            )

    # =======================================================================
    # OPCIÓN 4
    # =======================================================================

    elif opcion == "4":

        fecha = solicitar_fecha()

        resultado, estado = \
            consultar_novedades_fecha(
                fecha
            )

        if estado == "OK":

            guardar_resultado(
                resultado,
                f"Novedades MIPRES - {fecha}",
                f"novedades_{fecha}"
            )

        else:

            print(
                "\nLa consulta falló."
            )

    # =======================================================================
    # OPCIÓN 5
    # =======================================================================

    elif opcion == "5":

        lista = \
            solicitar_lista_prescripciones()

        if not lista:

            print(
                "\nNo se ingresaron números "
                "de prescripción."
            )

            return

        print(
            f"\nSe consultarán "
            f"{len(lista)} prescripciones."
        )

        resultado, estado = \
            consultar_prescripciones_masivas(
                lista
            )

        if estado == "OK":

            guardar_resultado(
                resultado,
                "Anexo técnico MIPRES - Consulta masiva",
                f"prescripciones_masivas_{len(lista)}"
            )

        else:

            print(
                "\nLa consulta masiva falló."
            )

    # =======================================================================
    # OPCIÓN 6
    # =======================================================================

    elif opcion == "6":

        lista = \
            solicitar_lista_prescripciones()

        if not lista:

            print(
                "\nNo se ingresaron números "
                "de prescripción."
            )

            return

        print(
            f"\nSe consultarán novedades para "
            f"{len(lista)} prescripciones."
        )

        resultado, estado = \
            consultar_novedades_masivas(
                lista
            )

        if estado == "OK":

            guardar_resultado(
                resultado,
                "Novedades MIPRES - Consulta masiva",
                f"novedades_masivas_{len(lista)}"
            )

        else:

            print(
                "\nLa consulta masiva de "
                "novedades falló."
            )


# ===========================================================================
# PROGRAMA PRINCIPAL
# ===========================================================================

def main():

    crear_carpeta_resultados()

    print("\n")
    print("=" * 65)
    print(
        "             SISTEMA DE CONSULTA MIPRES"
    )
    print("=" * 65)

    print(
        f"NIT configurado: {NIT}"
    )

    print(
        f"Carpeta de resultados: "
        f"{os.path.abspath(RESULTADOS_DIR)}"
    )

    print("=" * 65)

    while True:

        mostrar_menu()

        opcion = input(
            "\nSeleccione una opción: "
        ).strip()

        if opcion == "0":

            print(
                "\nPrograma finalizado."
            )

            break

        if opcion not in {
            "1",
            "2",
            "3",
            "4",
            "5",
            "6"
        }:

            print(
                "\nOpción no válida."
            )

            continue

        try:

            ejecutar_opcion(
                opcion
            )

        except KeyboardInterrupt:

            print(
                "\n\nOperación cancelada "
                "por el usuario."
            )

        except Exception as e:

            print(
                "\nSe produjo un error "
                "inesperado:"
            )

            print(e)

        input(
            "\nPresione ENTER para "
            "volver al menú..."
        )


# ===========================================================================
# INICIO
# ===========================================================================

if __name__ == "__main__":

    main()
