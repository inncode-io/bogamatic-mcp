#!/usr/bin/env bash
# Bogamatic SAC installer for macOS
# Usage: bash install.sh <SAC_USERNAME> <SAC_PASSWORD>
set -euo pipefail

SAC_USERNAME="${1:-}"
SAC_PASSWORD="${2:-}"

if [ -z "$SAC_USERNAME" ] || [ -z "$SAC_PASSWORD" ]; then
    echo ""
    echo "Uso: bash install.sh <MATRICULA> <PASSWORD>"
    echo "  Ejemplo: bash install.sh 1-36413 MiClave123"
    echo ""
    exit 1
fi

echo ""
echo "=== Bogamatic SAC - Instalador ==="
echo ""

# Step 1: Install uv if needed
if ! command -v uvx &>/dev/null; then
    echo "[1/3] Instalando uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v uvx &>/dev/null; then
        echo "ERROR: No se pudo instalar uv. Instalalo manualmente: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
else
    echo "[1/3] uv ya esta instalado"
fi

# Step 2: Detect Claude Desktop config path
echo "[2/3] Buscando Claude Desktop..."

CONFIG_DIR="$HOME/Library/Application Support/Claude"
if [ ! -d "$CONFIG_DIR" ]; then
    echo "ERROR: No se encontro Claude Desktop."
    echo "  Instala Claude Desktop, abrilo una vez, y volve a ejecutar este script."
    exit 1
fi

CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
echo "  Config: $CONFIG_FILE"

# Step 3: Write config
echo "[3/3] Configurando Claude Desktop..."

# Build the new server entry
NEW_CONFIG=$(cat <<EOF
{
  "mcpServers": {
    "bogamatic-sac": {
      "command": "uvx",
      "args": ["bogamatic-sac-mcp"],
      "env": {
        "SAC_USERNAME": "$SAC_USERNAME",
        "SAC_PASSWORD": "$SAC_PASSWORD"
      }
    }
  }
}
EOF
)

# If config exists and has other servers, try to preserve them
if [ -f "$CONFIG_FILE" ] && command -v python3 &>/dev/null; then
    python3 -c "
import json, sys

new_server = {
    'command': 'uvx',
    'args': ['bogamatic-sac-mcp'],
    'env': {
        'SAC_USERNAME': sys.argv[1],
        'SAC_PASSWORD': sys.argv[2],
    }
}

try:
    with open(sys.argv[3]) as f:
        config = json.load(f)
except Exception:
    config = {}

config.setdefault('mcpServers', {})
config['mcpServers']['bogamatic-sac'] = new_server

with open(sys.argv[3], 'w') as f:
    json.dump(config, f, indent=2)

print('  OK: Config actualizado (servidores existentes preservados)')
" "$SAC_USERNAME" "$SAC_PASSWORD" "$CONFIG_FILE" 2>/dev/null || echo "$NEW_CONFIG" > "$CONFIG_FILE"
else
    echo "$NEW_CONFIG" > "$CONFIG_FILE"
    echo "  OK: Config escrito"
fi

echo ""
echo "=== Instalacion completa ==="
echo ""
echo "  Reinicia Claude Desktop para activar Bogamatic SAC."
echo ""
