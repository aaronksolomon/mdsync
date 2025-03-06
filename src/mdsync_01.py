#!/usr/bin/env python3
"""
MDSync - Markdown to Google Docs Synchronization Utility
A walking skeleton implementation focusing on core functionality.
"""

import os
import json
import subprocess
import click
from datetime import datetime
from pathlib import Path
import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io
import git
import tempfile

# Constants
CONFIG_FILENAME = ".mdsync_config.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]

def get_drive_service():
    """Authenticate and create a Google Drive service object."""
    creds = None
    token_path = Path.home() / ".mdsync" / "token.json"
    
    # Create .mdsync directory if it doesn't exist
    os.makedirs(Path.home() / ".mdsync", exist_ok=True)
    
    # Check if token file exists
    if token_path.exists():
        creds = Credentials.from_authorized_user_info(
            json.loads(token_path.read_text()), SCOPES
        )
    
    # If credentials don't exist or are invalid, let user authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Load client secrets from the expected location
            client_secret_path = Path.home() / ".mdsync" / "credentials.json"
            if not client_secret_path.exists():
                click.echo(f"Please place your Google API credentials at {client_secret_path}", err=True)
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secret_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        token_path.write_text(json.dumps(json.loads(creds.to_json())))
    
    # Return authenticated Drive service
    return build("drive", "v3", credentials=creds)

def find_or_create_folder(service, folder_name, parent_id=None):
    """Find a folder in Google Drive or create it if it doesn't exist."""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    response = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
    folders = response.get("files", [])
    
    if folders:
        # Return the first matching folder
        return folders[0]
    else:
        # Create folder if it doesn't exist
        folder_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder"
        }
        if parent_id:
            folder_metadata["parents"] = [parent_id]
        
        folder = service.files().create(body=folder_metadata, fields="id").execute()
        click.echo(f"Created folder: {folder_name}")
        return folder

def md_to_docx(md_path, docx_path):
    """Convert Markdown to DOCX using Pandoc."""
    try:
        subprocess.run(
            ["pandoc", str(md_path), "-o", str(docx_path)],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        click.echo(f"Error converting {md_path} to DOCX: {e}", err=True)
        return False

def docx_to_md(docx_path, md_path):
    """Convert DOCX to Markdown using Pandoc."""
    try:
        subprocess.run(
            ["pandoc", str(docx_path), "-o", str(md_path)],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        click.echo(f"Error converting {docx_path} to MD: {e}", err=True)
        return False

def upload_file_to_drive(service, file_path, folder_id, mime_type):
    """Upload a file to Google Drive."""
    file_name = os.path.basename(file_path)
    
    # Check if file already exists
    query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
    response = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
    files = response.get("files", [])
    
    file_metadata = {"name": file_name, "parents": [folder_id]}
    media = MediaFileUpload(file_path, mimetype=mime_type)
    
    if files:
        # Update existing file
        file_id = files[0]["id"]
        updated_file = service.files().update(
            fileId=file_id,
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()
        return updated_file["id"]
    else:
        # Create new file
        created_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()
        return created_file["id"]

def download_file_from_drive(service, file_id, download_path):
    """Download a file from Google Drive."""
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(download_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    fh.close()
    return True

def get_drive_file_info(service, file_id):
    """Get metadata for a file in Google Drive."""
    return service.files().get(fileId=file_id, fields="modifiedTime").execute()

def init_command(path, drive_folder, force, init_git):
    """Initialize MDSync configuration for a directory."""
    local_path = Path(path).absolute()
    if not local_path.exists() or not local_path.is_dir():
        click.echo(f"Error: {local_path} is not a valid directory")
        return False
    
    config_path = local_path / CONFIG_FILENAME
    if config_path.exists() and not force:
        click.echo(f"Error: {config_path} already exists. Use --force to overwrite.")
        return False
    
    # Connect to Google Drive
    drive_service = get_drive_service()
    if not drive_service:
        return False
    
    # Find or create the folder in Google Drive
    drive_folder = find_or_create_folder(drive_service, drive_folder)
    
    # Create initial configuration
    config = {
        "local_path": str(local_path),
        "drive_folder_id": drive_folder["id"],
        "drive_folder_name": drive_folder["name"],
        "last_sync": None,
        "files": {}
    }
    
    # Write configuration
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    click.echo(f"Initialized MDSync in {local_path}")
    click.echo(f"Connected to Google Drive folder: {drive_folder['name']}")
    
    # Initialize Git repository if requested
    if init_git and not (local_path / ".git").exists():
        git.Repo.init(local_path)
        click.echo(f"Initialized Git repository in {local_path}")
    
    return True

def update_command(path):
    """Synchronize changes between local Markdown files and Google Drive."""
    # Determine the path to use
    if path:
        local_path = Path(path).absolute()
    else:
        local_path = Path.cwd().absolute()
    
    config_path = local_path / CONFIG_FILENAME
    if not config_path.exists():
        click.echo(f"Error: {config_path} not found. Run 'mdsync init' first.")
        return False
    
    # Load configuration
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Connect to Google Drive
    drive_service = get_drive_service()
    if not drive_service:
        return False
    
    # Create temporary directory for file conversions
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Process all Markdown files in the directory
        md_files = list(local_path.glob("*.md"))
        for md_file in md_files:
            file_name = md_file.name
            docx_name = f"{file_name[:-3]}.docx"
            temp_docx_path = temp_dir_path / docx_name
            
            # Convert MD to DOCX
            if md_to_docx(md_file, temp_docx_path):
                # Upload DOCX to Google Drive
                with click.progressbar(length=1, label=f"Uploading {file_name}") as bar:
                    file_id = upload_file_to_drive(
                        drive_service, 
                        temp_docx_path, 
                        config["drive_folder_id"],
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    bar.update(1)
                
                # Update config with new file mapping
                config["files"][file_name] = {
                    "drive_file_id": file_id,
                    "last_upload": datetime.now().isoformat(),
                }
        
        # Check for DOCX files in Google Drive that need to be downloaded
        query = f"'{config['drive_folder_id']}' in parents and mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document' and trashed=false"
        response = drive_service.files().list(q=query, spaces="drive", fields="files(id, name, modifiedTime)").execute()
        
        for drive_file in response.get("files", []):
            docx_name = drive_file["name"]
            md_name = f"{docx_name[:-5]}.md" if docx_name.endswith(".docx") else f"{docx_name}.md"
            local_md_path = local_path / md_name
            
            # Check if we need to download this file
            file_info = config["files"].get(md_name, {})
            drive_modified = drive_file.get("modifiedTime")
            
            if not file_info or not file_info.get("last_upload"):
                needs_download = True
            else:
                # Compare timestamps to see if Drive version is newer
                last_upload = datetime.fromisoformat(file_info["last_upload"])
                drive_modified_time = datetime.fromisoformat(drive_modified.replace("Z", "+00:00"))
                needs_download = drive_modified_time > last_upload
            
            if needs_download:
                # Download the DOCX file
                temp_docx_path = temp_dir_path / docx_name
                with click.progressbar(length=1, label=f"Downloading {docx_name}") as bar:
                    download_file_from_drive(drive_service, drive_file["id"], temp_docx_path)
                    bar.update(1)
                
                # Convert DOCX to MD
                if docx_to_md(temp_docx_path, local_md_path):
                    click.echo(f"Updated {md_name} from Google Drive")
                    
                    # Update config
                    config["files"][md_name] = {
                        "drive_file_id": drive_file["id"],
                        "last_upload": datetime.now().isoformat(),
                    }
    
    # Update configuration with sync timestamp
    config["last_sync"] = datetime.now().isoformat()
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    click.echo(f"Sync completed at {config['last_sync']}")
    return True

@click.group()
def cli():
    """MDSync - Markdown to Google Docs Synchronization Utility"""
    pass

@cli.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument("drive_folder")
@click.option("--force", is_flag=True, help="Force overwrite of existing config")
@click.option("--init-git", is_flag=True, help="Initialize Git repository if not exists")
def init(path, drive_folder, force, init_git):
    """Initialize MDSync in a directory."""
    init_command(path, drive_folder, force, init_git)

@cli.command()
@click.option("--path", type=click.Path(exists=True, file_okay=False, dir_okay=True), 
              help="Optional local directory path (defaults to current directory)")
def update(path):
    """Synchronize changes between local Markdown files and Google Drive."""
    update_command(path)

if __name__ == "__main__":
    cli()