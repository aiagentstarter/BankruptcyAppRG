# Bankruptcy Application

A Flask-based web application for managing bankruptcy cases, with features for client document upload and attorney document processing using Azure services.

## Features

- Client portal for document upload
- Attorney dashboard for client management
- Document processing using Azure Document Intelligence
- Secure file storage using Azure Blob Storage
- Key Vault integration for secrets management
- SQLite database for client and file management

## Prerequisites

- Python 3.9 or higher
- Azure subscription with the following resources:
  - Key Vault (bankruptcyappvault)
  - Blob Storage (bankruptcyappstorage)
  - Document Intelligence (bankruptcyappdi)
  - App Service (bankruptcyapp)
  - App Service Plan (bankruptcyappplan)

## Local Setup

1. Install Python 3.9:
   - Windows: Download from [Python.org](https://www.python.org/downloads/)
   - macOS: `brew install python@3.9`
   - Ubuntu: `sudo apt-get install python3.9`

2. Install Azure CLI:
   - Windows: Download from [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-windows)
   - macOS: `brew install azure-cli`
   - Ubuntu: 
     ```bash
     curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
     ```

3. Log in to Azure:
   ```bash
   az login
   ```

4. Clone this repository and navigate to the project directory:
   ```bash
   git clone <repository-url>
   cd bankruptcyapp
   ```

5. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

6. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

7. Create a `.env` file with the following variables:
   ```
   ATTORNEY_PASS=password123
   CLIENT_PASS=clientpass
   ```

## Running the Application

1. Start the Flask development server:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to:
   - Client portal: http://localhost:5000/client
   - Attorney dashboard: http://localhost:5000/attorney

## Azure Deployment

The application is already configured for deployment to Azure App Service. The following resources are set up:

- Key Vault: bankruptcyappvault
- Blob Storage: bankruptcyappstorage
  - Containers: client-uploads, attorney-processed
- Document Intelligence: bankruptcyappdi
- App Service: bankruptcyapp
- App Service Plan: bankruptcyappplan

To deploy updates:

```bash
az webapp up --sku F1 --name bankruptcyapp --resource-group BankruptcyAppRG
```

## Testing

1. Client Upload Test:
   - Go to http://localhost:5000/client
   - Login with username: client, password: clientpass
   - Enter a case ID and upload a PDF file
   - Verify the upload success message

2. Attorney Dashboard Test:
   - Go to http://localhost:5000/attorney
   - Login with username: attorney, password: password123
   - Add a new client
   - View and process uploaded documents

## Security Notes

- The application uses Azure Key Vault for secure storage of sensitive information
- Blob Storage access is controlled through SAS tokens
- Simple password-based authentication is used for the prototype
- For production, implement proper authentication and authorization

## Future Improvements

1. Implement proper user authentication and authorization
2. Add database backup to Blob Storage
3. Move App Service to East US region for reduced latency
4. Migrate to Azure SQL Database for better scalability
5. Add more document processing features
6. Implement client email notifications
7. Add document version control
8. Implement audit logging

## Support

For issues or questions, please contact the development team. 