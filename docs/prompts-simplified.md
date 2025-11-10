# Prompts Simplifiés - Services Business Only

## 🎯 Objectif

Les prompts ont été simplifiés pour **se concentrer UNIQUEMENT sur les services business** et **utiliser les champs standards** (sans préfixe `otel*`).

## 📋 Services Business

Les agents doivent analyser **UNIQUEMENT** ces services :

- `customer` - Service client
- `order` - Service commandes
- `ordercheck` - Vérification des commandes
- `ordermanagement` - Gestion des commandes
- `stock` - Service stock
- `supplier` - Service fournisseur
- `suppliercheck` - Vérification fournisseur

**❌ Exclus** : Les services agents (`agent-logs`, `agent-metrics`, `agent-orchestrator`, `agent-traces`)

## 🔒 Champs Standards vs Préfixés

**✅ UTILISER** (champs standards) :
- `trace_id` - Trace ID standard OpenTelemetry
- `span_id` - Span ID standard OpenTelemetry
- `service_name` - Nom du service

**❌ NE PAS UTILISER** (champs préfixés internes) :
- `otelTraceID` - Version préfixée (interne)
- `otelSpanID` - Version préfixée (interne)
- `otelTraceSampled` - Champ interne
- Tous les champs commençant par `otel*`

**Note** : Les deux versions existent dans les logs, mais on utilise **uniquement les versions sans préfixe** pour une API propre.

## 📝 LogQL (Logs)

### Labels Autorisés

- ✅ `service_name` - Nom du service business
- ✅ `trace_id` - Trace ID (32-char hex) pour filtrer par trace
- ✅ `span_id` - Span ID pour filtrer par span
- ✅ `severity_text` - Niveau de log (INFO, WARNING, ERROR, CRITICAL)

### Exemples de Requêtes

**Logs récents de tous les services business** :
```logql
{service_name=~"customer|order|stock|supplier|ordercheck|ordermanagement|suppliercheck"}
```

**Logs d'un service spécifique** :
```logql
{service_name="order"}
```

**Logs pour un trace_id spécifique** :
```logql
{trace_id="71bbc86ec66e292fa06d95ae2f8fba6d"}
```

**Logs d'un trace sur un service spécifique** :
```logql
{trace_id="71bbc86ec66e292fa06d95ae2f8fba6d", service_name="order"}
```

**Logs d'erreur** :
```logql
{service_name=~"customer|order|stock|supplier|ordercheck|ordermanagement|suppliercheck"} |= "error"
```

**Logs ERROR/CRITICAL uniquement** :
```logql
{service_name=~"customer|order|stock|supplier|ordercheck|ordermanagement|suppliercheck", severity_text=~"ERROR|CRITICAL"}
```

**Recherche de texte** :
```logql
{service_name="order"} |= "database"
```

**Logs d'un span spécifique** :
```logql
{span_id="4fb40b2f11010262"}
```

## 📊 PromQL (Metrics)

### Labels Autorisés

- ✅ `service_name` - Nom du service business
- ✅ `http_method` - Méthode HTTP (GET, POST, PUT, DELETE)
- ✅ `http_route` - Route HTTP
- ✅ `http_status_code` - Code HTTP (200, 404, 500, etc.)
- ✅ `error_type` - Type d'erreur

### Métriques Communes

- `http_server_duration_*` - Durée des requêtes HTTP
- `http_server_request_size_*` - Taille des requêtes
- `http_server_response_size_*` - Taille des réponses
- `db_client_connections_usage` - Connexions DB

### Exemples de Requêtes

**Taux de requêtes d'un service** :
```promql
rate(http_server_duration_count{service_name="order"}[5m])
```

**Taux d'erreur 5xx** :
```promql
rate(http_server_duration_count{service_name="order",http_status_code=~"5.."}[5m])
```

**Latence p95** :
```promql
histogram_quantile(0.95, rate(http_server_duration_bucket{service_name="order"}[5m]))
```

**Connexions DB** :
```promql
db_client_connections_usage{service_name="order"}
```

**Taux de requêtes par service** :
```promql
sum by(service_name) (rate(http_server_duration_count{service_name=~"customer|order|stock|supplier|ordercheck|ordermanagement|suppliercheck"}[5m]))
```

## 🔍 TraceQL (Traces)

### Attributs Autorisés

- ✅ `service.name` - Nom du service business
- ✅ `status` - Statut (ok, error)
- ✅ `duration` - Durée (e.g., > 500ms)

### Exemples de Requêtes

**Toutes les traces business** :
```traceql
{service.name=~"customer|order|stock|supplier|ordercheck|ordermanagement|suppliercheck"}
```

**Traces d'un service** :
```traceql
{service.name="order"}
```

**Traces en erreur** :
```traceql
{service.name=~"customer|order|stock|supplier|ordercheck|ordermanagement|suppliercheck" && status=error}
```

**Traces lentes (> 500ms)** :
```traceql
{service.name=~"customer|order|stock|supplier|ordercheck|ordermanagement|suppliercheck" && duration > 500ms}
```

**Erreurs lentes d'un service** :
```traceql
{service.name="order" && status=error && duration > 300ms}
```

## 🎯 Exemples d'Utilisation

### Cas 1 : Dernières lignes de logs

**Question** : "Les 5 dernières lignes de logs ?"

**Requête LogQL** :
```logql
{service_name=~"customer|order|stock|supplier|ordercheck|ordermanagement|suppliercheck"}
```

### Cas 2 : Logs pour un trace_id

**Question** : "Logs pour trace_id=71bbc86ec66e292fa06d95ae2f8fba6d"

**Requête LogQL** :
```logql
{trace_id="71bbc86ec66e292fa06d95ae2f8fba6d"}
```

### Cas 3 : Erreurs sur un service

**Question** : "Erreurs sur le service order dans la dernière heure"

**Requête LogQL** :
```logql
{service_name="order"} |= "error"
```

### Cas 4 : Analyse de performance

**Question** : "Latence p95 du service order"

**Requête PromQL** :
```promql
histogram_quantile(0.95, rate(http_server_duration_bucket{service_name="order"}[5m]))
```

## ✅ Validation

### Test avec trace_id
```bash
curl -X POST http://localhost:8002/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Logs pour trace_id 71bbc86ec66e292fa06d95ae2f8fba6d", "time_range": "1h"}'
```

### Test services business seulement
```bash
curl -X POST http://localhost:8002/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Erreurs sur tous les services", "time_range": "1h"}'
```

## 🎯 Résumé

| Catégorie | Autorisé | Interdit |
|-----------|----------|----------|
| **Services** | customer, order, stock, supplier, ordercheck, ordermanagement, suppliercheck | agent-* |
| **Champs Logs** | trace_id, span_id, service_name, severity_text | otel* |
| **Champs Metrics** | service_name, http_*, error_type, db_* | otel* |
| **Champs Traces** | service.name, status, duration | otel* |

## 📂 Fichiers mis à jour

- `agent-logs/agent_logs/prompts/build_logql.md` ✅
- `agent-metrics/agent_metrics/prompts/build_promql.md` ✅
- `agent-traces/agent_traces/prompts/build_traceql.md` ✅
- `docs/prompts-simplified.md` ✅

**Version** : 2.0 - Ajout de `trace_id` et `span_id` dans les exemples
