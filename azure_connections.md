# Azure API Connections and Backend Communication

## Overview
This document explains how the Bankruptcy Application's backend (Python/Flask) communicates with various Azure services. The application uses three main Azure services:
1. Azure Key Vault (for secure credential storage)
2. Azure Blob Storage (for document storage)
3. Azure Document Intelligence (for document analysis)

## 1. Azure Key Vault Connection

### Purpose
Azure Key Vault is used to securely store sensitive credentials that the application needs to access other Azure services. This is more secure than storing credentials in code or environment variables.

### Code Implementation
```python
# Import required Azure libraries
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

# Set up Key Vault connection
vault_url = "https://bankruptcyappvault.vault.azure.net/"
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url, credential)

# Retrieve secrets
di_key = secret_client.get_secret("DIKey").value
blob_connection_string = secret_client.get_secret("BlobConnectionString").value
```

### How it Works
1. The application uses `DefaultAzureCredential()` to authenticate with Azure
2. It connects to the Key Vault using the vault URL
3. It retrieves two secrets:
   - `DIKey`: Used to authenticate with Azure Document Intelligence
   - `BlobConnectionString`: Used to connect to Azure Blob Storage

## 2. Azure Blob Storage Connection

### Purpose
Azure Blob Storage is used to store uploaded documents and processed results. It provides secure, scalable storage for files.

### Code Implementation
```python
# Import required Azure libraries
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

# Set up Blob Storage connection
blob_client = BlobServiceClient.from_connection_string(blob_connection_string)

# Create container clients
client_container = blob_client.get_container_client("client-uploads")
attorney_container = blob_client.get_container_client("attorney-processed")
```

### How it Works
1. The application connects to Blob Storage using the connection string from Key Vault
2. It creates two containers:
   - `client-uploads`: Stores documents uploaded by clients
   - `attorney-processed`: Stores processed document results

### File Upload Example
```python
# When a client uploads a file
blob_name = f"{client_id}/{file.filename}"
client_container.upload_blob(blob_name, file, overwrite=True)
```

### Secure File Access Example
```python
# Generate a secure URL for file access
sas_token = generate_blob_sas(
    blob_client.account_name,
    'client-uploads',
    file[0],
    blob_client.credential.account_key,
    permission=BlobSasPermissions(read=True),
    expiry=datetime.utcnow() + timedelta(hours=1)
)

# Create the full URL
sas_url = f"https://{blob_client.account_name}.blob.core.windows.net/client-uploads/{file[0]}?{sas_token}"
```

## 3. Azure Document Intelligence Connection

### Purpose
Azure Document Intelligence (formerly Form Recognizer) is used to analyze uploaded documents and extract information automatically.

### Code Implementation
```python
# Import required Azure libraries
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

# Set up Document Intelligence connection
di_client = DocumentAnalysisClient(
    "https://bankruptcyappdi.cognitiveservices.azure.com/",
    AzureKeyCredential(di_key)
)
```

### How it Works
1. The application connects to Document Intelligence using the key from Key Vault
2. It uses the prebuilt document model for analysis

### Document Processing Example
```python
# Process a document
blob_client_instance = client_container.get_blob_client(blob_name)
blob_data = blob_client_instance.download_blob().readall()

# Start document analysis
poller = di_client.begin_analyze_document("prebuilt-document", blob_data)
result = poller.result()

# Extract information
summary = {
    "text": result.content[:500],
    "key_values": {
        kv.key.content: kv.value.content 
        for kv in result.key_value_pairs 
        if kv.value
    }
}
```

## Security Considerations

### 1. Authentication
- Uses Azure's managed identity through `DefaultAzureCredential()`
- No hardcoded credentials in the code
- All sensitive information stored in Key Vault

### 2. File Access
- Uses SAS (Shared Access Signature) tokens for secure file access
- Tokens expire after 1 hour
- Read-only permissions for file viewing

### 3. Data Protection
- Files stored in separate containers for different purposes
- Processed results stored separately from original documents
- All communication uses HTTPS

## Error Handling

The application includes error handling for Azure operations:

```python
try:
    # Azure operation
    client_container.upload_blob(blob_name, file, overwrite=True)
except Exception as e:
    return f"Error uploading file: {str(e)}", 500
```

## Dependencies

Required Azure packages in `requirements.txt`:
```
azure-storage-blob==12.17.0
azure-ai-formrecognizer==3.2.1
azure-identity==1.13.0
azure-keyvault-secrets==4.7.0
```

## Best Practices

1. **Credential Management**
   - Never store credentials in code
   - Use Key Vault for all sensitive information
   - Rotate credentials regularly

2. **File Handling**
   - Use unique blob names to prevent conflicts
   - Implement proper error handling
   - Clean up temporary files

3. **Performance**
   - Use async operations for large files
   - Implement proper timeout handling
   - Monitor API usage and limits

## Troubleshooting

Common issues and solutions:

1. **Authentication Failures**
   - Check Key Vault access permissions
   - Verify managed identity is configured
   - Ensure credentials are not expired

2. **File Upload Issues**
   - Verify blob container exists
   - Check file size limits
   - Ensure proper permissions

3. **Document Processing Errors**
   - Verify Document Intelligence service is active
   - Check API quotas and limits
   - Validate document format 