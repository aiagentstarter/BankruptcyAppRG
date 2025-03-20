from flask import Flask, request, render_template, redirect, url_for
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from datetime import datetime, timedelta
import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Key Vault setup
vault_url = "https://bankruptcyappvault.vault.azure.net/"
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url, credential)
di_key = secret_client.get_secret("DIKey").value
blob_connection_string = secret_client.get_secret("BlobConnectionString").value

# Azure clients
di_client = DocumentAnalysisClient(
    "https://bankruptcyappdi.cognitiveservices.azure.com/",
    AzureKeyCredential(di_key)
)
blob_client = BlobServiceClient.from_connection_string(blob_connection_string)
client_container = blob_client.get_container_client("client-uploads")
attorney_container = blob_client.get_container_client("attorney-processed")

# Simple authentication using environment variables
USERS = {
    "attorney": os.getenv("ATTORNEY_PASS", "password123"),
    "client": os.getenv("CLIENT_PASS", "clientpass")
}

# SQLite CRM setup
DB_FILE = "crm.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, 
                  case_id TEXT, 
                  email TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS files 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  client_id INTEGER, 
                  blob_name TEXT, 
                  upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(client_id) REFERENCES clients(id))''')
    conn.commit()
    conn.close()

if not os.path.exists(DB_FILE):
    init_db()

@app.route("/")
def home():
    return "Welcome to the Bankruptcy Portal. Use /client or /attorney to access your view."

@app.route("/client", methods=["GET", "POST"])
def client_view():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if USERS.get(username) != password or username != "client":
            return "Invalid credentials", 401
        
        file = request.files.get("file")
        client_id = request.form.get("client_id")
        if file and client_id:
            try:
                # Upload to blob storage
                blob_name = f"{client_id}/{file.filename}"
                client_container.upload_blob(blob_name, file, overwrite=True)
                
                # Update database
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO files (client_id, blob_name) VALUES (?, ?)", 
                         (client_id, blob_name))
                conn.commit()
                conn.close()
                return "File uploaded successfully!"
            except Exception as e:
                return f"Error uploading file: {str(e)}", 500
    return render_template("client_upload.html")

@app.route("/attorney", methods=["GET", "POST"])
def attorney_view():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if USERS.get(username) != password or username != "attorney":
            return "Invalid credentials", 401
        
        action = request.form.get("action")
        
        if action == "add_client":
            try:
                name = request.form.get("name")
                case_id = request.form.get("case_id")
                email = request.form.get("email")
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO clients (name, case_id, email) VALUES (?, ?, ?)", 
                         (name, case_id, email))
                conn.commit()
                conn.close()
                return redirect(url_for("attorney_view"))
            except Exception as e:
                return f"Error adding client: {str(e)}", 500
        
        elif action == "list_files":
            try:
                client_id = request.form.get("client_id")
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("SELECT blob_name FROM files WHERE client_id = ?", (client_id,))
                files = c.fetchall()
                conn.close()
                
                sas_urls = []
                for file in files:
                    sas_token = generate_blob_sas(
                        blob_client.account_name,
                        'client-uploads',
                        file[0],
                        blob_client.credential.account_key,
                        permission=BlobSasPermissions(read=True),
                        expiry=datetime.utcnow() + timedelta(hours=1)
                    )
                    sas_urls.append(
                        f"https://{blob_client.account_name}.blob.core.windows.net/client-uploads/{file[0]}?{sas_token}"
                    )
                return render_template("attorney_dashboard.html", 
                                    files=sas_urls, 
                                    summary=None, 
                                    client_id=client_id)
            except Exception as e:
                return f"Error listing files: {str(e)}", 500
        
        elif action == "process":
            try:
                client_id = request.form.get("client_id")
                blob_name = request.form.get("blob_name")
                blob_client_instance = client_container.get_blob_client(blob_name)
                blob_data = blob_client_instance.download_blob().readall()
                
                # Process with Document Intelligence
                poller = di_client.begin_analyze_document("prebuilt-document", blob_data)
                result = poller.result()
                
                # Extract summary
                summary = {
                    "text": result.content[:500],
                    "key_values": {
                        kv.key.content: kv.value.content 
                        for kv in result.key_value_pairs 
                        if kv.value
                    }
                }
                
                # Store processed results
                attorney_container.upload_blob(
                    f"processed/{client_id}/{blob_name.split('/')[-1]}", 
                    str(summary), 
                    overwrite=True
                )
                
                return render_template("attorney_dashboard.html", 
                                    files=[], 
                                    summary=summary, 
                                    client_id=client_id)
            except Exception as e:
                return f"Error processing file: {str(e)}", 500
    
    # Default: Show CRM dashboard
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, name, case_id, email FROM clients")
        clients = c.fetchall()
        conn.close()
        return render_template("attorney_dashboard.html", 
                            clients=clients, 
                            files=None, 
                            summary=None)
    except Exception as e:
        return f"Error loading dashboard: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True) 