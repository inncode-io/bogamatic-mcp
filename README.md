# bogamatic-sac-mcp

MCP server for interacting with the Argentine judiciary system (SAC - Justicia Cordoba) via Claude Desktop.

## Installation

Requires [Claude Desktop](https://claude.ai/download) and [uv](https://docs.astral.sh/uv/getting-started/installation/).

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bogamatic-sac": {
      "command": "uvx",
      "args": ["bogamatic-sac-mcp"],
      "env": {
        "SAC_USERNAME": "your-matricula",
        "SAC_PASSWORD": "your-password"
      }
    }
  }
}
```

Restart Claude Desktop.

## Available tools

- `get_novedades_cedulas` — list cedula notifications (NEW/SEEN)
- `get_detalle_cedula` — full cedula details
- `get_resumen_cedula` — cedula details + deadline calculation
- `get_expedientes` — search cases
- `get_novedades_expedientes` — recent case activity
- `get_operaciones_expediente` — case operations/movements
- `get_adjuntos_expediente` — case attachments
- `get_texto_operacion_expediente` — operation text (Markdown)
- `download_adjunto` — download attachments locally
- `calcular_plazo` — calculate procedural deadlines
- `send_whatsapp_notification` — send WhatsApp alerts
