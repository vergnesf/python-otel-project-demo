#!/usr/bin/env bash
set -euo pipefail

echo "==> Setting up Python OTel Demo dev environment..."

# S'assurer que uv est dans le PATH
export PATH="$HOME/.local/bin:$PATH"

# Installer powerlevel10k comme thème zsh
if [ -d "$HOME/.oh-my-zsh" ] && [ ! -d "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k" ]; then
  echo "  -> Installation de powerlevel10k..."
  git clone --depth=1 https://github.com/romkatv/powerlevel10k.git \
    "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k"
  # Activer le thème dans .zshrc
  sed -i 's/ZSH_THEME="devcontainers"/ZSH_THEME="powerlevel10k\/powerlevel10k"/' ~/.zshrc
  echo "  -> powerlevel10k installé (lance 'p10k configure' pour le personnaliser)"
fi

# Persister la config p10k dans le named volume ~/.zsh-config
# Le volume survit aux rebuilds, ~/.p10k.zsh est un symlink vers ce volume.
mkdir -p "$HOME/.zsh-config"
if [ ! -f "$HOME/.zsh-config/.p10k.zsh" ]; then
  # Fichier vide pour éviter les warnings zsh au premier démarrage
  touch "$HOME/.zsh-config/.p10k.zsh"
fi
# Remplacer ~/.p10k.zsh par un symlink (sauf si c'est déjà le bon symlink)
if [ ! -L "$HOME/.p10k.zsh" ] || [ "$(readlink "$HOME/.p10k.zsh")" != "$HOME/.zsh-config/.p10k.zsh" ]; then
  [ -f "$HOME/.p10k.zsh" ] && mv "$HOME/.p10k.zsh" "$HOME/.zsh-config/.p10k.zsh"
  ln -sf "$HOME/.zsh-config/.p10k.zsh" "$HOME/.p10k.zsh"
  echo "  -> ~/.p10k.zsh → ~/.zsh-config/.p10k.zsh (volume persistant)"
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
