---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'Reprise qualité projet python-otel-project-demo — micro-services Python avec OpenTelemetry'
session_goals: 'Revue de code, complétion documentation, ajout tests automatiques (périmètre: services KEEPER + ACTIVE)'
selected_approach: 'ai-recommended'
techniques_used: ['Question Storming', 'Morphological Analysis']
ideas_generated: [17]
context_file: ''
session_active: false
workflow_completed: true
---

# Brainstorming Session Results

**Facilitateur :** a-team
**Date :** 2026-02-28

---

## Session Overview

**Sujet :** Reprise qualité projet `python-otel-project-demo` — micro-services Python avec OpenTelemetry
**Objectifs :** Revue de code, complétion documentation, ajout tests automatiques
**Contrainte principale :** Rester simple — projet perso, pas de production

### Contexte clé découvert en session

Ce projet est un **laboratoire d'apprentissage évolutif** :
- Démarré pour tester Python
- Couche observabilité (OpenTelemetry) ajoutée ensuite
- Amélioration Docker + UV
- Actuellement : expérimentation de la partie agentic
- Demain : autre chose

**Architecture réelle du projet :**
- **Couche métier** (`customer`, `order`, `stock`, `supplier`...) = générateur d'activité et de données OTEL → doit être stable
- **Couche agents** (`agent-xx`) = consommateurs intelligents via MCP/Grafana → en évolution permanente
- **`benchmark`** = outil de test LLM (très utile, ouvert à l'amélioration)

**Vision future :** les `agent-xx` utiliseront via MCP Grafana les données d'observabilité générées par la couche métier.

---

## Classification des services

| Statut | Services | Priorité qualité |
|--------|----------|-----------------|
| **KEEPER** | `customer`, `order`, `ordercheck`, `ordermanagement`, `stock`, `supplier`, `suppliercheck`, `common-ai`, `common-models`, `config` | Stable, testé, documenté |
| **ACTIVE** | `agent-traduction`, `benchmark` | En bon état, évolutif |
| **DRAFT** | `agent-ui`, `agent-logs`, `agent-metrics`, `agent-orchestrator`, `agent-traces` | En cours, pas de maintenance requise |

---

## Sélection des techniques

**Approche :** Recommandations IA
**Techniques utilisées :** Question Storming → Morphological Analysis

---

## Insights clés de session

1. **Tests = filet anti-régression**, pas du TDD exhaustif — l'objectif est la *confiance*, pas la couverture
2. **Documentation = mémoire personnelle** — "pourquoi j'ai fait ça" plus que "comment ça marche"
3. **Simplicité = critère de sélection** — toute idée trop complexe à maintenir est une mauvaise idée
4. **Deux couches avec des besoins distincts** — couche métier stable vs couche agents en évolution
5. **DRAFT = permission explicite** de ne pas maintenir — libère de la culpabilité, clarifie les priorités

---

## Inventaire des idées — 17 idées, 4 thèmes

### Thème 1 — Cartographie et classification

**[Review #1] : Classification KEEPER / ACTIVE / DRAFT**
_Concept_ : Ajouter `## Status: KEEPER` (ou ACTIVE, DRAFT) en haut du README de chaque service.
_Nouveauté_ : Signal explicite du niveau de maintenance attendu. Évite de gaspiller du temps sur du code volontairement provisoire.

**[Review #5] : DRAFT comme permission de ne pas maintenir**
_Concept_ : Un label DRAFT dans le README = décision documentée que ce code n'a pas besoin d'être propre.
_Nouveauté_ : Élimine la culpabilité et clarifie les priorités sans supprimer le code.

**[Review #3] : Stabiliser la couche métier en priorité**
_Concept_ : Traiter `customer`, `order`, `stock`, `supplier` et leurs `check` en premier — ce sont les fondations dont les agents dépendent.
_Nouveauté_ : Investir la qualité là où l'effet de levier est maximal.

---

### Thème 2 — Mémoire et documentation légère

**[Doc #4] : Schéma d'architecture dans le README racine**
_Concept_ : Un diagramme Mermaid simple — "couche métier génère → OTEL collecte → Grafana stocke → agents lisent via MCP".
_Nouveauté_ : En 6 mois, vous vous rappelez immédiatement *pourquoi* ce projet existe.

**[Doc #5] : `EXPERIMENTS.md` — journal d'apprentissage**
_Concept_ : Bullet points datés à la racine — "2026-02 : testé agents MCP Grafana, 2025-11 : ajouté UV, etc."
_Nouveauté_ : Mémoire de votre parcours d'apprentissage, pas juste de l'état du projet.

**[Doc #1] : README 3 lignes par service**
_Concept_ : Pour chaque service KEEPER : "Ce service fait X. Il tourne avec Y. Je l'ai créé pour tester Z."
_Nouveauté_ : La ligne "créé pour tester Z" est celle qu'on oublie toujours et qui a le plus de valeur.

**[Doc #2] : `CHANGELOG.md` global informel**
_Concept_ : Bullet points datés — pas de versioning, pas de sémantique. Juste une mémoire de ce qui a changé.
_Nouveauté_ : Zéro contrainte de format, maximum de valeur comme aide-mémoire.

**[Doc #3] : Convention `# POURQUOI` dans le code**
_Concept_ : Tout commentaire expliquant l'*intention* (pas le fonctionnement) est préfixé `# POURQUOI`.
_Nouveauté_ : Retrouver instantanément son intention d'origine 6 mois plus tard.

---

### Thème 3 — Filet de sécurité (tests)

**[Tests #1] : Smoke test par service KEEPER**
_Concept_ : Un seul `test_smoke.py` par service — vérifie que ça boot et répond à un ping. 10 lignes max.
_Nouveauté_ : Pas de mock, pas de fixtures. Si ça boot et répond, c'est vert.

**[Tests #2] : `make test` global via Docker Compose**
_Concept_ : Une seule commande qui lance tous les services + vérifie qu'ils sont healthy.
_Nouveauté_ : Zéro config par service — c'est l'infra qui teste.

**[Tests #3] : Tester le chemin heureux seulement**
_Concept_ : Pour chaque service, tester uniquement le scénario principal qui fonctionne.
_Nouveauté_ : 80% de la valeur pour 20% de l'effort. Parfait pour un projet perso.

**[Tests #4] : Test de la pipeline OTEL complète**
_Concept_ : Un script qui génère de l'activité métier et vérifie que les traces/métriques apparaissent dans Grafana.
_Nouveauté_ : Valide que la plomberie dont les agents auront besoin fonctionne de bout en bout.

**[Tests #5] : Health-check MCP comme test d'intégration**
_Concept_ : Un test qui vérifie que la connexion MCP → Grafana répond avant de démarrer une session agent.
_Nouveauté_ : Un seul test qui valide toute la plomberie entre les deux couches.

---

### Thème 4 — Qualité du benchmark et infrastructure partagée

**[Benchmark #1] : Cas de test LLM nommés**
_Concept_ : Organiser en petits fichiers `test_[scenario].py` — `test_traduction.py`, `test_summarization.py`, etc.
_Nouveauté_ : Ajouter un nouveau LLM à tester sans toucher aux cas existants.

**[Benchmark #2] : `results/` versionné**
_Concept_ : Sauvegarder les outputs des runs LLM dans des fichiers datés pour comparer modèles sur les mêmes prompts.
_Nouveauté_ : Mémoire des évaluations LLM — pas besoin de tout rejouer pour comparer.

**[Review #2] : Linter `ruff` partagé**
_Concept_ : Un seul `pyproject.toml` à la racine avec `ruff` configuré — tous les services héritent du même style.
_Nouveauté_ : Une commande `make lint` pour tout le projet, zéro duplication de config.

**[Review #4] : `common-ai` / `common-models` documentés comme interface interne**
_Concept_ : Documenter ces deux modules comme une "API interne" — ce qu'ils exposent et pourquoi.
_Nouveauté_ : Quand un nouvel agent est créé, on sait exactement ce qui est disponible.

---

## Plan d'action priorisé

### Cette semaine — Quick wins (2-3h total)

| # | Action | Effort |
|---|--------|--------|
| 1 | Ajouter `## Status` dans chaque README — classification KEEPER/ACTIVE/DRAFT | 30 min |
| 2 | Créer `EXPERIMENTS.md` à la racine | 15 min |
| 3 | Schéma d'architecture Mermaid dans `README.md` racine | 30 min |
| 4 | Configurer `ruff` dans `pyproject.toml` racine + `make lint` | 30 min |

### Court terme — Fondations (1-2 sessions)

| # | Action | Effort |
|---|--------|--------|
| 5 | README 3 lignes pour chaque service KEEPER | 1h |
| 6 | Smoke tests sur services KEEPER + `make test` | 2-3h |
| 7 | Documenter `common-ai` / `common-models` | 1h |

### Moyen terme — Quand la couche agent avancera

| # | Action | Effort |
|---|--------|--------|
| 8 | Test pipeline OTEL complète (génère activité → vérifie Grafana) | 2h |
| 9 | Health-check MCP → Grafana | 1h |
| 10 | Structurer `benchmark/` en cas nommés + `results/` | 2h |

---

## Résumé de session

**17 idées générées** sur 4 thèmes cohérents avec la réalité du projet.

**Percée principale :** La classification KEEPER/ACTIVE/DRAFT est la clé de voûte — elle détermine où investir l'effort qualité et donne une permission explicite de ne pas tout maintenir.

**Prochaine étape recommandée :** Reprendre ce document après redémarrage de Claude Code (configuration MCP GitLab) pour créer les issues GitLab correspondantes au plan d'action.
