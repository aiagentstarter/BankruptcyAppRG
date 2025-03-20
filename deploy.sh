#!/bin/bash

# Deploy to Azure App Service
echo "Deploying to Azure App Service..."
az webapp up \
  --sku F1 \
  --name bankruptcyapp \
  --resource-group BankruptcyAppRG \
  --runtime "PYTHON:3.9"

# Set environment variables
echo "Setting environment variables..."
az webapp config appsettings set \
  --name bankruptcyapp \
  --resource-group BankruptcyAppRG \
  --settings \
    KEY_VAULT_NAME=bankruptcyappvault \
    ATTORNEY_PASS=password123 \
    CLIENT_PASS=clientpass

echo "Deployment complete!" 