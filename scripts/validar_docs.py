"""Validación automática de la documentación y de las reglas de arquitectura.

Lo ejecuta el job «Validación de la documentación» del CI. Falla (código 1) si:

1. Un enlace relativo de un Markdown apunta a un archivo que no existe, o a
   una sección (#ancla) que no existe en el Markdown de destino.
2. Un ADR no sigue la convención `NNNN-titulo-en-kebab-case.md`, no tiene
   línea de estado, o dice «Reemplazado por» sin enlazar al ADR que lo
   reemplaza.
3. Falta una de las vistas C4 de los niveles 1 a 3, o alguna no tiene un
   diagrama Mermaid.
4. El dominio o la aplicación del frontend importan infraestructura o
   interfaz (la regla hexagonal que `backend/tests/test_architecture.py`
   comprueba para el backend).

El render de los diagramas Mermaid lo comprueba el mismo job con
`mermaid-cli`, sobre los archivos que lista `--archivos-mermaid`.

Uso, desde la raíz del repositorio:

    python scripts/validar_docs.py
    python scripts/validar_docs.py --archivos-mermaid
"""

import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EXCLUIDOS = {"node_modules", ".git", ".next", ".venv", "venv"}

ENLACE = re.compile(r"\]\(([^)\s]+)\)")
ENCABEZADO = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
ANCLA_HTML = re.compile(r'<a\s+(?:id|name)="([^"]+)"')
BLOQUE_CODIGO = re.compile(r"^(```|~~~)")
ADR_NOMBRE = re.compile(r"^[0-9]{4}-[a-z0-9]+(-[a-z0-9]+)*\.md$")
IMPORT_JS = re.compile(r"""(?:import\s[^'"]*from\s*|import\s*\(\s*|require\(\s*)['"]([^'"]+)['"]""")

VISTAS_C4 = ("contexto.md", "contenedores.md", "componentes.md")


def markdowns():
    for ruta in sorted(RAIZ.rglob("*.md")):
        if not EXCLUIDOS.intersection(ruta.relative_to(RAIZ).parts):
            yield ruta


def lineas_fuera_de_codigo(texto):
    dentro = False
    for linea in texto.splitlines():
        if BLOQUE_CODIGO.match(linea.strip()):
            dentro = not dentro
            continue
        if not dentro:
            yield linea


def slug_github(titulo):
    """Ancla que GitHub genera para un encabezado."""

    texto = re.sub(r"`([^`]*)`", r"\1", titulo)
    texto = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", texto)
    texto = re.sub(r"<[^>]+>", "", texto)
    texto = texto.strip().lower()
    resultado = []
    for caracter in texto:
        categoria = unicodedata.category(caracter)
        if caracter in " -":
            resultado.append("-" if caracter == " " else caracter)
        elif caracter == "_" or categoria[0] in ("L", "N") or categoria == "Mn":
            resultado.append(caracter)
    return "".join(resultado)


_anclas = {}


def anclas_de(ruta):
    if ruta not in _anclas:
        texto = ruta.read_text(encoding="utf-8", errors="replace")
        vistas = {}
        anclas = set(ANCLA_HTML.findall(texto))
        for linea in lineas_fuera_de_codigo(texto):
            encabezado = ENCABEZADO.match(linea)
            if not encabezado:
                continue
            base = slug_github(encabezado.group(2))
            repeticion = vistas.get(base, 0)
            vistas[base] = repeticion + 1
            anclas.add(base if repeticion == 0 else f"{base}-{repeticion}")
        _anclas[ruta] = anclas
    return _anclas[ruta]


def revisar_enlaces():
    errores = []
    total = 0
    for md in markdowns():
        texto = md.read_text(encoding="utf-8", errors="replace")
        for numero, linea in enumerate(texto.splitlines(), start=1):
            for destino in ENLACE.findall(linea):
                if re.match(r"^[a-z][a-z0-9+.-]*:", destino, re.I):
                    continue
                total += 1
                ruta, _, ancla = destino.partition("#")
                objetivo = (md.parent / ruta).resolve() if ruta else md
                sitio = f"{md.relative_to(RAIZ)}:{numero}"
                if not objetivo.exists():
                    errores.append(f"{sitio}: enlace roto -> {destino}")
                elif ancla and objetivo.suffix == ".md" and ancla.lower() not in anclas_de(objetivo):
                    errores.append(f"{sitio}: la sección #{ancla} no existe en {ruta or md.name}")
    return errores, total


def revisar_adr():
    errores = []
    carpeta = RAIZ / "docs" / "adr"
    archivos = sorted(carpeta.glob("*.md"))
    for adr in archivos:
        if not ADR_NOMBRE.match(adr.name):
            errores.append(f"docs/adr/{adr.name}: no sigue NNNN-titulo-en-kebab-case.md")
            continue
        cabecera = adr.read_text(encoding="utf-8", errors="replace").splitlines()[:12]
        estado = next((l for l in cabecera if re.search(r"\*\*Estado:?\*\*", l)), None)
        if estado is None:
            errores.append(f"docs/adr/{adr.name}: sin línea «**Estado:**» en la cabecera")
            continue
        if re.search(r"reemplazad[oa]", estado, re.I):
            enlaces = re.findall(r"\((\d{4}-[a-z0-9-]+\.md)\)", estado)
            if not enlaces:
                errores.append(f"docs/adr/{adr.name}: dice «Reemplazado» sin enlazar al ADR que lo reemplaza")
            for enlace in enlaces:
                if not (carpeta / enlace).exists():
                    errores.append(f"docs/adr/{adr.name}: el ADR que lo reemplaza no existe ({enlace})")
    numeros = [int(a.name[:4]) for a in archivos if ADR_NOMBRE.match(a.name)]
    if numeros != list(range(1, len(numeros) + 1)):
        errores.append(f"docs/adr: la numeración no es consecutiva desde 0001 ({numeros})")
    return errores, len(archivos)


def revisar_c4():
    errores = []
    for vista in VISTAS_C4:
        ruta = RAIZ / "docs" / "c4" / vista
        if not ruta.exists():
            errores.append(f"docs/c4/{vista}: falta la vista")
        elif "```mermaid" not in ruta.read_text(encoding="utf-8"):
            errores.append(f"docs/c4/{vista}: no tiene un diagrama Mermaid")
    return errores


def revisar_frontend():
    errores = []
    reglas = {
        "domain": ("application", "infrastructure", "ui", "app"),
        "application": ("infrastructure", "ui", "app"),
    }
    frontend = RAIZ / "frontend"
    for capa, prohibidas in reglas.items():
        for archivo in sorted((frontend / capa).rglob("*.js")):
            texto = archivo.read_text(encoding="utf-8", errors="replace")
            for modulo in IMPORT_JS.findall(texto):
                if not modulo.startswith("."):
                    continue
                destino = (archivo.parent / modulo).resolve()
                try:
                    primera = destino.relative_to(frontend).parts[0]
                except ValueError:
                    continue
                if primera in prohibidas:
                    errores.append(
                        f"{archivo.relative_to(RAIZ)}: la capa {capa} no puede importar {primera} ({modulo})"
                    )
    return errores


def archivos_mermaid():
    for md in markdowns():
        if "```mermaid" in md.read_text(encoding="utf-8", errors="replace"):
            print(md.relative_to(RAIZ).as_posix())


def main(argumentos):
    if "--archivos-mermaid" in argumentos:
        archivos_mermaid()
        return 0

    errores_enlaces, enlaces = revisar_enlaces()
    errores_adr, adrs = revisar_adr()
    errores = errores_enlaces + errores_adr + revisar_c4() + revisar_frontend()

    for error in errores:
        print(f"ERROR {error}")
    print(
        f"{enlaces} enlaces relativos, {adrs} ADR, {len(VISTAS_C4)} vistas C4 y la regla "
        f"de dependencias del frontend revisados: {len(errores)} errores."
    )
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
