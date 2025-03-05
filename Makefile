SHELL := /bin/bash

.PHONY: api-install api-test api-run web-install web-run web-build infra-plan cluster-up

api-install:
	cd apps/api && poetry install --with dev,lint

api-test:
	cd apps/api && poetry run pytest

api-run:
	cd apps/api && poetry run uvicorn chatopsllm_api.main:app --host 0.0.0.0 --port 30000

web-install:
	cd apps/web && npm install

web-run:
	cd apps/web && npm start

web-build:
	cd apps/web && npm run build

infra-plan:
	cd iac/terraform && terraform init && terraform plan

cluster-up:
	bash scripts/cluster.sh
