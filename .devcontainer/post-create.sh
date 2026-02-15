#!/usr/bin/env bash
set -euo pipefail

echo "==> Setting up Python OTel Demo dev environment..."

# Installer uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Installer promptfoo
echo "  -> Installation de promptfoo..."
npm install -g promptfoo

# Activer le thème agnoster dans .zshrc
if [ -d "$HOME/.oh-my-zsh" ]; then
  sed -i 's/ZSH_THEME="[^"]*"/ZSH_THEME="agnoster"/' ~/.zshrc
  echo "  -> Thème agnoster activé"
fi

# Vérification des outils
echo "  -> uv:        $(uv --version)"
echo "  -> python:    $(python --version)"
echo "  -> node:      $(node --version)"
echo "  -> promptfoo: $(promptfoo --version 2>/dev/null || echo 'not found')"
echo "  -> make:      $(make --version | head -1)"
echo "  -> docker:    $(docker --version 2>/dev/null || echo 'not available (check docker-outside-of-docker feature)')"

# Copier .env.example en .env si absent
if [ ! -f /workspace/.env ]; then
  echo "  -> Création du fichier .env depuis .env.example"
  cp /workspace/.env.example /workspace/.env
fi

# Installer les dépendances de chaque service avec uv
SERVICES=(
  "common-models"
  "common-ai"
  "order"
  "stock"
  "customer"
  "supplier"
  "ordercheck"
  "suppliercheck"
  "ordermanagement"
  "agent-orchestrator"
  "agent-logs"
  "agent-metrics"
  "agent-traces"
  "agent-traduction"
  "agent-ui"
)

for svc in "${SERVICES[@]}"; do
  svc_path="/workspace/$svc"
  if [ -f "$svc_path/pyproject.toml" ]; then
    echo "  -> Installation des dépendances : $svc"
    (cd "$svc_path" && uv sync --all-extras 2>&1 | tail -3)
  fi
done

echo ""
echo "==> Dev environment ready!"
echo ""
echo "  Commandes utiles :"
echo "    make compose-up        # Démarre toute la stack (depuis l'hôte Docker)"
echo "    make compose-down      # Arrête la stack"
echo "    make models-init       # Télécharge les modèles Ollama"
echo "    make tools-format      # Formate le code (black)"
echo ""
echo "  Tests promptfoo :"
echo "    cd agent-traduction && promptfoo eval -c tests/promptfoo/promptfooconfig.yaml"
echo "    promptfoo view                     # UI de résultats"
echo ""
echo "  Accès réseau depuis le devcontainer (via otel-network) :"
echo "    http://agent-traduction:8002       # direct container-to-container"
echo "    http://localhost:8002              # via port forward"
echo ""
echo "  Accès (via Traefik sur port 8081) :"
echo "    http://localhost:8081/grafana/     # Grafana"
echo "    http://localhost:8081/agents/ui/   # Agent UI"
echo "    http://localhost:8081/adminer/     # Adminer (DB)"
echo "    http://localhost:8081/akhq/        # AKHQ (Kafka)"
echo "    http://localhost:8082              # Traefik Dashboard"
echo ""
echo "  Note : si otel-network n'existe pas encore :"
echo "    docker network create otel-network   (ou make compose-up)"
