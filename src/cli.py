"""
Interfaz de línea de comandos para el sistema de recomendación.

Este módulo proporciona una CLI para interactuar con el sistema
de recomendación inmobiliaria usando lenguaje natural.
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from typing import Optional
import json
import os

from .recommendation_engine import RecommendationEngine
from .llm_integration import LLMIntegration, LLMConfig

app = typer.Typer(help="Sistema de Recomendación Inmobiliaria para Citrino")
console = Console()


def cargar_propiedades_desde_json(ruta: str) -> list:
    """Carga propiedades desde un archivo JSON."""
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        console.print(f"[red]Error: No se encontró el archivo {ruta}[/red]")
        return []
    except json.JSONDecodeError:
        console.print(f"[red]Error: El archivo {ruta} no tiene formato JSON válido[/red]")
        return []


@app.command()
def recomendar(
    perfil: str = typer.Option(..., help="Perfil del prospecto (ruta a archivo JSON o descripción en texto)"),
    limite: int = typer.Option(5, help="Número máximo de recomendaciones"),
    formato: str = typer.Option("tabla", help="Formato de salida (tabla, json, detallado)"),
    usar_llm: bool = typer.Option(True, help="Usar LLM para procesamiento de lenguaje natural")
):
    """
    Genera recomendaciones de propiedades basadas en el perfil del prospecto.
    """
    # Inicializar motor de recomendación
    engine = RecommendationEngine()

    # Inicializar LLM integration si está habilitado
    llm_integration = None
    if usar_llm:
        try:
            llm_integration = LLMIntegration()
            if llm_integration.validar_configuracion():
                config_info = llm_integration.obtener_info_configuracion()
                console.print(f"[green]LLM configurado: {config_info['provider']} - {config_info['model']}[/green]")
            else:
                console.print("[yellow]LLM no configurado, usando procesamiento básico[/yellow]")
                llm_integration = None
        except Exception as e:
            console.print(f"[yellow]Error inicializando LLM ({e}), usando procesamiento básico[/yellow]")
            llm_integration = None

    # Cargar propiedades
    ruta_propiedades = "data/propiedades.json"
    if os.path.exists(ruta_propiedades):
        propiedades = cargar_propiedades_desde_json(ruta_propiedades)
        engine.cargar_propiedades(propiedades)
        console.print(f"[green]Cargadas {len(propiedades)} propiedades[/green]")
    else:
        console.print("[yellow]No se encontraron propiedades. Usando datos de ejemplo.[/yellow]")
        # Aquí podríamos cargar datos de ejemplo

    # Cargar perfil
    if os.path.exists(perfil):
        try:
            with open(perfil, 'r', encoding='utf-8') as f:
                perfil_data = json.load(f)
            console.print(f"[green]Perfil cargado desde {perfil}[/green]")
        except Exception as e:
            console.print(f"[red]Error cargando perfil: {e}[/red]")
            return
    else:
        # Si no es un archivo, asumir que es una descripción en texto
        console.print("[blue]Analizando perfil desde descripción...[/blue]")
        perfil_data = _parsear_perfil_desde_texto(perfil, llm_integration)

    # Generar recomendaciones
    console.print("\n[bold blue]Generando recomendaciones...[/bold blue]")
    recomendaciones = engine.generar_recomendaciones(perfil_data, limite)

    # Mostrar resultados
    if not recomendaciones:
        console.print("[yellow]No se encontraron propiedades que coincidan con el perfil.[/yellow]")
        return

    if formato == "tabla":
        _mostrar_recomendaciones_tabla(recomendaciones)
    elif formato == "json":
        _mostrar_recomendaciones_json(recomendaciones)
    elif formato == "detallado":
        _mostrar_recomendaciones_detalladas(recomendaciones)


def _parsear_perfil_desde_texto(texto: str, llm_integration: Optional[LLMIntegration] = None) -> dict:
    """
    Parsea una descripción en lenguaje natural a un perfil estructurado.
    Utiliza LLM cuando está disponible, con fallback a procesamiento básico.
    """
    # Intentar usar LLM si está configurado
    if llm_integration and llm_integration.validar_configuracion():
        try:
            console.print("[blue]Analizando con LLM...[/blue]")
            perfil = llm_integration.parsear_perfil_desde_texto(texto)
            console.print("[green]Perfil generado con LLM[/green]")
            return perfil
        except Exception as e:
            console.print(f"[yellow]Error con LLM ({e}), usando procesamiento básico[/yellow]")

    # Fallback a procesamiento básico sin LLM
    console.print("[yellow]Usando procesamiento básico (LLM no disponible)[/yellow]")
    return _parsear_perfil_basico(texto)


def _parsear_perfil_basico(texto: str) -> dict:
    """
    Genera un perfil básico usando reglas simples.
    """
    texto_lower = texto.lower()

    # Análisis simple de composición familiar
    adultos = 2  # valor por defecto
    ninos = []
    adultos_mayores = 0

    if "solo" in texto_lower or "individual" in texto_lower:
        adultos = 1
    elif "pareja" in texto_lower or "matrimonio" in texto_lower:
        adultos = 2
    elif "familia" in texto_lower:
        adultos = 2
        if "hijo" in texto_lower or "niño" in texto_lower:
            ninos = [{"edad": 8}]  # edad estimada

    # Análisis simple de presupuesto
    presupuesto_min = None
    presupuesto_max = None

    # Buscar números en el texto
    import re
    numeros = re.findall(r'\b(\d+(?:\.\d+)?)\s*[kK]?\b', texto)
    if numeros:
        # Convertir a números y asumir que son miles si tienen 'k' o son < 1000
        valores = []
        for num in numeros:
            valor = float(num)
            if valor < 1000:
                valor *= 1000  # asumir miles
            valores.append(valor)

        if valores:
            presupuesto_min = min(valores) * 0.8  # 20% menos como mínimo
            presupuesto_max = max(valores) * 1.2  # 20% más como máximo

    # Necesidades básicas según palabras clave
    necesidades = []
    if "escuela" in texto_lower or "colegio" in texto_lower:
        necesidades.append("escuela_primaria")
    if "universidad" in texto_lower:
        necesidades.append("universidad")
    if "supermercado" in texto_lower or "mercado" in texto_lower:
        necesidades.append("supermercado")
    if "hospital" in texto_lower or "clinica" in texto_lower:
        necesidades.append("hospital")

    # Preferencias de ubicación
    ubicacion = None
    if "norte" in texto_lower:
        ubicacion = "norte"
    elif "sur" in texto_lower:
        ubicacion = "sur"
    elif "centro" in texto_lower:
        ubicacion = "centro"

    return {
        "composicion_familiar": {
            "adultos": adultos,
            "ninos": ninos,
            "adultos_mayores": adultos_mayores
        },
        "presupuesto": {
            "min": presupuesto_min,
            "max": presupuesto_max,
            "tipo": "compra"
        },
        "necesidades": necesidades,
        "preferencias": {
            "ubicacion": ubicacion,
            "seguridad": "alta",
            "caracteristicas_deseadas": []
        }
    }


def _mostrar_recomendaciones_tabla(recomendaciones: list):
    """Muestra las recomendaciones en formato de tabla."""
    table = Table(title="Propiedades Recomendadas")
    table.add_column("#", style="cyan", no_wrap=True)
    table.add_column("Propiedad", style="magenta")
    table.add_column("Precio", style="green")
    table.add_column("Habitaciones", style="blue")
    table.add_column("Ubicación", style="yellow")
    table.add_column("Compatibilidad", style="red")

    for i, rec in enumerate(recomendaciones, 1):
        prop = rec['propiedad']
        caract = prop.get('caracteristicas', {})
        ubic = prop.get('ubicacion', {})

        table.add_row(
            str(i),
            f"Propiedad {i}",
            f"${caract.get('precio', 0):,.0f}",
            str(caract.get('habitaciones', 0)),
            ubic.get('barrio', 'N/A'),
            f"{rec['compatibilidad']}%"
        )

    console.print(table)


def _mostrar_recomendaciones_json(recomendaciones: list):
    """Muestra las recomendaciones en formato JSON."""
    console.print(json.dumps(recomendaciones, indent=2, ensure_ascii=False))


def _mostrar_recomendaciones_detalladas(recomendaciones: list):
    """Muestra las recomendaciones en formato detallado."""
    for i, rec in enumerate(recomendaciones, 1):
        prop = rec['propiedad']
        caract = prop.get('caracteristicas', {})
        ubic = prop.get('ubicacion', {})

        panel_content = f"""
[b]Propiedad {i}[/b]
Ubicación: {ubic.get('barrio', 'N/A')}
Precio: ${caract.get('precio', 0):,.0f}
Habitaciones: {caract.get('habitaciones', 0)}
Baños: {caract.get('banos', 0)}
Compatibilidad: [green]{rec['compatibilidad']}%[/green]

Justificación:
{rec['justificacion']}
        """

        panel = Panel(panel_content.strip(), title=f"Recomendación #{i}")
        console.print(panel)
        console.print()


@app.command()
def listar_propiedades():
    """Lista todas las propiedades disponibles en el sistema."""
    ruta_propiedades = "data/propiedades.json"

    if not os.path.exists(ruta_propiedades):
        console.print("[yellow]No hay propiedades cargadas en el sistema.[/yellow]")
        return

    propiedades = cargar_propiedades_desde_json(ruta_propiedades)

    if not propiedades:
        console.print("[yellow]No se encontraron propiedades.[/yellow]")
        return

    table = Table(title="Propiedades Disponibles")
    table.add_column("ID", style="cyan")
    table.add_column("Ubicación", style="magenta")
    table.add_column("Precio", style="green")
    table.add_column("Habitaciones", style="blue")
    table.add_column("Baños", style="yellow")

    for prop in propiedades:
        caract = prop.get('caracteristicas', {})
        ubic = prop.get('ubicacion', {})

        table.add_row(
            prop.get('id', 'N/A'),
            ubic.get('barrio', 'N/A'),
            f"${caract.get('precio', 0):,.0f}",
            str(caract.get('habitaciones', 0)),
            str(caract.get('banos', 0))
        )

    console.print(table)


@app.command()
def ayuda():
    """Muestra información de ayuda y ejemplos de uso."""
    ayuda_texto = """
[bold blue]Sistema de Recomendación Inmobiliaria - Citrino[/bold blue]

Ejemplos de uso:

[green]1. Recomendar con perfil de archivo:[/green]
  python -m src.cli recomendar --perfil data/perfil_familia.json

[green]2. Recomendar con descripción en texto:[/green]
  python -m src.cli recomendar --perfil "familia con 2 hijos, presupuesto 250-300K"

[green]3. Listar propiedades disponibles:[/green]
  python -m src.cli listar-propiedades

[green]4. Cambiar formato de salida:[/green]
  python -m src.cli recomendar --perfil perfil.json --formato json
  python -m src.cli recomendar --perfil perfil.json --formato detallado

[bold]Opciones de formato:[/bold]
  • [cyan]tabla[/cyan]: Formato de tabla compacta (por defecto)
  • [cyan]json[/cyan]: Formato JSON para integración
  • [cyan]detallado[/cyan]: Vista completa con justificaciones

[bold]Tip:[/bold] Puedes usar descripciones en lenguaje natural como:
  "pareja joven sin hijos, presupuesto 200K, cerca de universidades"
  "familia con niños, necesita escuela cercana, zona segura"
    """

    console.print(Panel(ayuda_texto.strip(), title="Ayuda del Sistema"))


if __name__ == "__main__":
    app()