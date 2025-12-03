# you can use this file to add custom make targets and avoid conflicting with the main Pegasus makefile

your-cmd: ## A custom command
	@echo "Your custom command!"

sync-prod-db: ## Sync production database to local (uses .kamal/secrets for configuration)
	@./scripts/sync_prod_db.sh
