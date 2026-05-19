"""Bogamatic SAC MCP thin client — proxies all calls to the Bogamatic API."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Annotated, Literal, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from bogamatic_mcp import api

mcp = FastMCP("bogamatic-sac")


def _sanitize(value: str) -> str:
    return re.sub(r"[\s]+", "_", re.sub(r"[^\w\s.-]", "", value)).strip("_")


# ── Cedulas ──


@mcp.tool(
    name="get_novedades_cedulas",
    description=(
        "Get the list of electronic cedula notifications (novedades). Each cedula is marked as 'NEW' "
        "or 'SEEN'. New cedulas are those not previously fetched. All fetched cedulas are stored "
        "to avoid duplicate notifications."
    ),
)
def get_novedades_cedulas(
    pageIndex: Annotated[int, Field(description="Page index (0-based)")] = 0,
    pageSize: Annotated[int, Field(description="Number of results per page")] = 20,
    sortColumn: Annotated[str, Field(description="Column to sort by")] = "Fecha",
    sortDirection: Annotated[Literal["asc", "desc"], Field(description="Sort direction")] = "asc",
) -> dict:
    return api.post("/sac/cedulas/novedades", {
        "pageIndex": pageIndex,
        "pageSize": pageSize,
        "sortColumn": sortColumn,
        "sortDirection": sortDirection,
    })


@mcp.tool(
    name="get_detalle_cedula",
    description=(
        "Get the full detail of a specific cedula notification. Returns: matricula, destinatario, "
        "dependencia, numeroExpediente, caratula, fecha (dd/MM/yyyy), tipoOperacion, idOperacion, "
        "textoOperacion (converted to Markdown), protocolo, and adjuntos[] (each with idFichero, nombre, datosExtra)."
    ),
)
def get_detalle_cedula(
    idCedula: Annotated[str, Field(description="The cedula ID (idCedulaDestinatario from get_novedades_cedulas)")]
) -> dict:
    return api.post("/sac/cedulas/detalle", {"idCedula": idCedula})


@mcp.tool(
    name="get_resumen_cedula",
    description=(
        "Get a complete summary of a cedula in a single call. Combines get_detalle_cedula + "
        "calcular_plazo into one response. Returns: destinatario, numeroExpediente, caratula, "
        "dependencia, fecha, tipoOperacion, idOperacion, textoOperacion (Markdown), adjuntos[] "
        "(each with idFichero, nombre, datosExtra), protocolo, and plazo (with fechaInicio, "
        "fechaPlazo, diasHabilesContados, diasSaltados). "
        "Use this instead of calling get_detalle_cedula and calcular_plazo separately."
    ),
)
def get_resumen_cedula(
    idCedula: Annotated[str, Field(description="The cedula ID (field 'idCedulaDestinatario' from get_novedades_cedulas)")],
) -> dict:
    return api.post("/sac/cedulas/resumen", {"idCedula": idCedula})


# ── Expedientes ──


@mcp.tool(
    name="get_expedientes",
    description=(
        "Search legal expedientes (cases/files) belonging to the authenticated lawyer. "
        "Supports fuzzy search on 'caratula'. Partial names are valid. "
        "If the user provides an expediente number, prefer using 'numeroExpediente' "
        "as the primary filter because it uniquely identifies the expediente."
    ),
)
def get_expedientes(
    caratula: Annotated[Optional[str], Field(description="Search by case title (party name, company, etc.)")] = None,
    numeroExpediente: Annotated[Optional[str], Field(description="Search by case number")] = None,
    fechaDesde: Annotated[Optional[str], Field(description="Filter from date (YYYY-MM-DD)")] = None,
    fechaHasta: Annotated[Optional[str], Field(description="Filter to date (YYYY-MM-DD)")] = None,
    pageIndex: Annotated[int, Field(description="Page index (0-based)")] = 0,
    pageSize: Annotated[int, Field(description="Number of results per page")] = 10,
) -> list[dict]:
    return api.post("/sac/expedientes/search", {
        "caratula": caratula,
        "numeroExpediente": numeroExpediente,
        "fechaDesde": fechaDesde,
        "fechaHasta": fechaHasta,
        "pageIndex": pageIndex,
        "pageSize": pageSize,
    })


@mcp.tool(
    name="get_novedades_expedientes",
    description="Get expedientes (cases) that had activity in the last 7 days. Returns case number, title, court, status, and location.",
)
def get_novedades_expedientes(
    pageIndex: Annotated[Optional[int], Field(description="Page index (0-based), null for all")] = None,
    pageSize: Annotated[int, Field(description="Number of results per page")] = 20,
) -> list[dict]:
    return api.post("/sac/expedientes/novedades", {
        "pageIndex": pageIndex,
        "pageSize": pageSize,
    })


@mcp.tool(
    name="get_operaciones_expediente",
    description=(
        "Get all operations (movements) for a specific expediente. Each operation returns: "
        "fecha (dd/MM/yyyy), tipoOperacion, idOperacion, esEscrito (needed by get_texto_operacion_expediente), "
        "adjunto (boolean), firmada, presentadoPor, ubicacion, estado, and a flattened extras dict."
    ),
)
def get_operaciones_expediente(
    idExpediente: Annotated[str, Field(description="The expediente ID (from get_novedades_expedientes or get_expedientes)")],
    includeEspeciales: Annotated[bool, Field(description="Include special operations")] = False,
) -> list[dict]:
    return api.post("/sac/expedientes/operaciones", {
        "idExpediente": idExpediente,
        "includeEspeciales": includeEspeciales,
    })


@mcp.tool(
    name="get_adjuntos_expediente",
    description=(
        "Get all attachments for an expediente. Each item returns: idFichero, idOperacion, "
        "nombre (file name), fecha (normalized to dd/MM/yyyy), tipoOperacion, esEscrito, "
        "clasificacion, observaciones, and numeroExpediente (echoed back for convenience). "
        "Use idFichero, idOperacion, nombre, and numeroExpediente as inputs for download_adjunto."
    ),
)
def get_adjuntos_expediente(
    idExpediente: Annotated[str, Field(description="Expediente ID")],
    numeroExpediente: Annotated[str, Field(description="Case number — echoed back in each item for use with download_adjunto")] = "",
) -> list[dict]:
    return api.post("/sac/expedientes/adjuntos", {
        "idExpediente": idExpediente,
        "numeroExpediente": numeroExpediente,
    })


@mcp.tool(
    name="get_texto_operacion_expediente",
    description=(
        "Get the text content of a specific operation within an expediente, "
        "returned as Markdown. Use esEscrito (from get_operaciones_expediente) "
        "to select the correct endpoint."
    ),
)
def get_texto_operacion_expediente(
    idOperacion: Annotated[str, Field(description="The operation ID (from get_operaciones_expediente)")],
    esEscrito: Annotated[bool, Field(description="Whether the operation is an escrito")],
) -> str:
    result = api.post("/sac/expedientes/texto-operacion", {
        "idOperacion": idOperacion,
        "esEscrito": esEscrito,
    })
    return result.get("texto", "")


@mcp.tool(
    name="download_adjunto",
    description=(
        "Download an attachment to the local project folder. "
        "Works for both cedulas and expediente operations. "
        "The file is saved as numeroExpediente_fechaOperacion_nombreArchivo."
    ),
)
def download_adjunto(
    idAdjunto: Annotated[str, Field(description="Attachment ID (field 'idFichero')")],
    idOperacion: Annotated[str, Field(description="Operation ID (field 'idOperacion')")],
    numeroExpediente: Annotated[str, Field(description="Case number")],
    fechaOperacion: Annotated[str, Field(description="Operation date")],
    nombreArchivo: Annotated[str, Field(description="Original file name")],
) -> str:
    content, content_type, _ = api.download("/sac/expedientes/download-adjunto", {
        "idAdjunto": idAdjunto,
        "idOperacion": idOperacion,
        "nombreArchivo": nombreArchivo,
    })

    # Build safe filename
    nombre_path = Path(nombreArchivo)
    extension = nombre_path.suffix.lower()
    stem = nombre_path.stem
    safe_name = f"{_sanitize(numeroExpediente)}_{_sanitize(fechaOperacion)}_{_sanitize(stem)}{extension}".lower()

    download_dir = Path(os.getenv("CLAUDE_PROJECT_DIR", "."))
    download_dir.mkdir(parents=True, exist_ok=True)
    dest = download_dir / safe_name

    dest.write_bytes(content)
    return f"Downloaded to {dest} ({len(content)} bytes)"


# ── Plazo ──


@mcp.tool(
    name="calcular_plazo",
    description=(
        "Given a notification date (typically from a cedula), calculates the first day a procedural "
        "deadline begins to run. Cordoba's (Argentina) procedural law grants 3 grace days after "
        "notification before any deadline starts. This tool counts 3 business days forward (skipping "
        "weekends and court holidays) and returns the date when the deadline period actually begins."
    ),
)
def calcular_plazo(
    fecha: Annotated[str, Field(description="Starting date in dd/MM/yyyy format (e.g. '28/04/2026')")]
) -> dict:
    return api.post("/sac/plazo/calcular", {"fecha": fecha})


# ── WhatsApp ──


@mcp.tool(
    name="send_whatsapp_notification",
    description=(
        "Send a WhatsApp notification about a new cedula. The phone number is resolved "
        "automatically from the authenticated user's account. Most parameters come from "
        "get_novedades_cedulas, while destinatario comes from get_detalle_cedula."
    ),
)
def send_whatsapp_notification(
    destinatario: Annotated[str, Field(description="Recipient name")],
    fecha: Annotated[str, Field(description="Notification date")],
    tipoOperacion: Annotated[str, Field(description="Operation type")],
    expediente: Annotated[str, Field(description="Case number")],
    caratula: Annotated[str, Field(description="Case title")],
) -> str:
    result = api.post("/sac/whatsapp/notify", {
        "destinatario": destinatario,
        "fecha": fecha,
        "tipoOperacion": tipoOperacion,
        "expediente": expediente,
        "caratula": caratula,
    })
    return result.get("message", "Notification sent.")


def main():
    mcp.run()


if __name__ == "__main__":
    main()
