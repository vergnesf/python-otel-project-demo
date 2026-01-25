SHELL := /usr/bin/env bash
VBASE := /srv/podman/python-otel-project-demo
ROOT := $(shell pwd)

IMAGES := \
	confluentinc/cp-kafka:8.1.0 \
	tchiotludo/akhq:0.26.0 \
	grafana/grafana:12.2 \
	otel/opentelemetry-collector-contrib:0.139.0 \
	grafana/loki:3.5.8 \
	grafana/tempo:2.9.0 \
	grafana/mimir:3.0.0 \
	postgres:18 \
	adminer:5.4.1

LOCAL_SERVICES := customer order supplier stock ordercheck suppliercheck ordermanagement agent-orchestrator agent-logs agent-metrics agent-traces agent-ui

.PHONY: help setup-dirs pull-images build-local build-all deploy teardown status logs

help:
	@echo "Available targets: setup-dirs pull-images build-local build-all deploy teardown status logs"

setup-dirs:
	@echo "Creating host volume directories under $(VBASE)"
	@mkdir -p $(VBASE)/kafka-data $(VBASE)/kafka-secrets $(VBASE)/grafana-data $(VBASE)/loki-data $(VBASE)/tempo-data $(VBASE)/mimir-data $(VBASE)/postgres-data

pull-images:
	@echo "Pulling upstream images..."
	@for img in $(IMAGES); do \
		podman pull $$img; \
	done

build-local:
	@echo "Building local images for services: $(LOCAL_SERVICES)"
	@for s in $(LOCAL_SERVICES); do \
		echo "-> building $$s"; \
		podman build -t project/$$s:local -f $$s/Dockerfile . || exit 1; \
	done

build-all: build-local

deploy: setup-dirs pull-images
	@echo "Deploying pods via podman play kube"
	@podman play kube $(ROOT)/podman/kube/kafka-pod.yaml
	@podman play kube $(ROOT)/podman/kube/observability-pod.yaml
	@podman play kube $(ROOT)/podman/kube/db-pod.yaml
	@podman play kube $(ROOT)/podman/kube/agents-pod.yaml
	@podman play kube $(ROOT)/podman/kube/apps-pod.yaml

teardown:
	@echo "Removing pods if present"
	@for p in kafka-pod observability-pod db-pod agents-pod apps-pod; do \
		if podman pod exists $$p; then podman pod rm -f $$p; fi; \
	done

status:
	@podman pod ps
	@podman ps -a

logs:
	@if [ -z "$(POD)" ]; then echo "Usage: make logs POD=<container>"; exit 1; fi
	@podman logs -f $(POD)
