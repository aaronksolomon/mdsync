#!/usr/bin/env python3
"""
MDSync - Markdown to Google Docs Synchronization Utility
Local Google Drive implementation based on ADR03.
"""

import os
import json
import subprocess
import click
from datetime import datetime
from pathlib import Path
import shutil
import tempfile
import git
from typing import Dict, Optional, Any, List, Tuple

# Constants
CONFIG_FILENAME = ".mdsync_config.json"


# File conversion functions
def md_to_docx(md_path: Path, docx_path: Path) -> bool:
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

def docx_to_md(docx_path: Path, md_path: Path) -> bool:
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


# Path and file management utilities
def get_relative_path(base_path: Path, target_path: Path) -> str:
    """Get the relative path from base_path to target_path."""
    return str(target_path.relative_to(base_path))


def validate_paths(md_path: Path, drive_path: Path) -> Tuple[bool, str]:
    """Validate that both paths exist and are directories."""
    if not md_path.exists() or not md_path.is_dir():
        return False, f"Error: {md_path} is not a valid directory"
    
    if not drive_path.exists() or not drive_path.is_dir():
        return False, f"Error: {drive_path} is not a valid directory. Please ensure your Google Drive is mounted and the specified path exists."
    
    return True, ""


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from file."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        click.echo(f"Error loading config: {e}", err=True)
        return {}


def save_config(config_path: Path, config: Dict[str, Any]) -> bool:
    """Save configuration to file."""
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        click.echo(f"Error saving config: {e}", err=True)
        return False


def init_git_repo(path: Path) -> bool:
    """Initialize a Git repository if it doesn't exist."""
    if not (path / ".git").exists():
        try:
            git.Repo.init(path)
            click.echo(f"Initialized Git repository in {path}")
            return True
        except Exception as e:
            click.echo(f"Error initializing Git repository: {e}", err=True)
            return False
    return True


# Synchronization functions
def sync_md_to_drive(
    local_md_path: Path, 
    drive_folder_path: Path, 
    temp_dir_path: Path, 
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Sync Markdown files to Google Drive as DOCX."""
    md_files = list(local_md_path.glob("*.md"))
    updated_config = config.copy()
    
    with click.progressbar(md_files, label="Converting MD to DOCX") as bar:
        for md_file in bar:
            file_name = md_file.name
            # Skip config file if it's a .md file
            if file_name == CONFIG_FILENAME:
                continue
                
            docx_name = f"{file_name[:-3]}.docx"
            temp_docx_path = temp_dir_path / docx_name
            drive_docx_path = drive_folder_path / docx_name
            
            # Get file modification times
            md_mtime = md_file.stat().st_mtime
            
            # Check if file needs to be updated
            file_info = updated_config["files"].get(file_name, {})
            last_upload = file_info.get("last_upload")
            
            if not last_upload or md_mtime > datetime.fromisoformat(last_upload).timestamp():
                # Convert MD to DOCX
                if md_to_docx(md_file, temp_docx_path):
                    # Copy DOCX to Google Drive folder
                    shutil.copy2(temp_docx_path, drive_docx_path)
                    
                    # Update config with new file mapping
                    updated_config["files"][file_name] = {
                        "drive_file_path": str(drive_docx_path.relative_to(drive_folder_path)),
                        "last_upload": datetime.now().isoformat(),
                        "md_mtime": md_mtime
                    }
    
    return updated_config

def sync_drive_to_md(
    local_md_path: Path, 
    drive_folder_path: Path, 
    temp_dir_path: Path, 
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Sync DOCX files from Google Drive to local Markdown files."""
    docx_files = list(drive_folder_path.glob("*.docx"))
    updated_config = config.copy()
    
    with click.progressbar(docx_files, label="Converting DOCX to MD") as bar:
        for docx_file in bar:
            docx_name = docx_file.name
            md_name = f"{docx_name[:-5]}.md"
            local_md_path_file = local_md_path / md_name
            temp_docx_path = temp_dir_path / docx_name
            
            # Get file modification times
            docx_mtime = docx_file.stat().st_mtime
            
            # Check if we need to download this file
            file_info = updated_config["files"].get(md_name, {})
            
            if not file_info or not file_info.get("last_upload"):
                needs_update = True
            else:
                # Compare timestamps to see if Drive version is newer
                last_upload_time = datetime.fromisoformat(file_info["last_upload"]).timestamp()
                needs_update = docx_mtime > last_upload_time
            
            if needs_update:
                # Copy the DOCX file to temp directory
                shutil.copy2(docx_file, temp_docx_path)
                
                # Convert DOCX to MD
                if docx_to_md(temp_docx_path, local_md_path_file):
                    click.echo(f"Updated {md_name} from Google Drive")
                    
                    # Update config
                    updated_config["files"][md_name] = {
                        "drive_file_path": str(docx_file.relative_to(drive_folder_path)),
                        "last_upload": datetime.now().isoformat(),
                        "md_mtime": local_md_path_file.stat().st_mtime
                    }
    
    return updated_config

# Main command functions
def init_command(md_path: str, drive_path: str, force: bool, init_git: bool) -> bool:
    """Initialize MDSync configuration for a directory."""
    local_md_path = Path(md_path).absolute()
    drive_folder_path = Path(drive_path).absolute()
    
    # Validate paths
    is_valid, error_msg = validate_paths(local_md_path, drive_folder_path)
    if not is_valid:
        click.echo(error_msg)
        return False
    
    config_path = local_md_path / CONFIG_FILENAME
    if config_path.exists() and not force:
        click.echo(f"Error: {config_path} already exists. Use --force to overwrite.")
        return False
    
    # Create initial configuration
    config = {
        "local_md_path": str(local_md_path),
        "drive_folder_path": str(drive_folder_path),
        "last_sync": None,
        "files": {}
    }
    
    # Write configuration
    if not save_config(config_path, config):
        return False
    
    click.echo(f"Initialized MDSync in {local_md_path}")
    click.echo(f"Connected to Google Drive folder: {drive_folder_path}")
    
    # Initialize Git repository if requested
    if init_git:
        init_git_repo(local_md_path)
    
    return True

def update_command(path: Optional[str] = None) -> bool:
    """Synchronize changes between local Markdown files and Google Drive folder."""
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
    config = load_config(config_path)
    if not config:
        return False
    
    local_md_path = Path(config["local_md_path"])
    drive_folder_path = Path(config["drive_folder_path"])
    
    # Verify paths still exist
    is_valid, error_msg = validate_paths(local_md_path, drive_folder_path)
    if not is_valid:
        click.echo(error_msg)
        return False
    
    # Create temporary directory for file conversions
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Step 1: Sync from MD to DOCX in Drive folder
        click.echo("Step 1: Syncing local Markdown files to Google Drive...")
        config = sync_md_to_drive(local_md_path, drive_folder_path, temp_dir_path, config)
        
        # Step 2: Sync from DOCX in Drive folder to MD
        click.echo("Step 2: Syncing Google Drive DOCX files to local Markdown...")
        config = sync_drive_to_md(local_md_path, drive_folder_path, temp_dir_path, config)
    
    # Update configuration with sync timestamp
    config["last_sync"] = datetime.now().isoformat()
    save_config(config_path, config)
    
    click.echo(f"Sync completed at {config['last_sync']}")
    return True


# CLI Command Group
@click.group()
def cli():
    """MDSync - Markdown to Google Docs Synchronization Utility (Local Drive Version)"""
    pass


@cli.command()
@click.argument("md_path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument("drive_path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--force", is_flag=True, help="Force overwrite of existing config")
@click.option("--init-git", is_flag=True, help="Initialize Git repository if not exists")
def init(md_path, drive_path, force, init_git):
    """Initialize MDSync in a directory with a local Google Drive folder path."""
    init_command(md_path, drive_path, force, init_git)


@cli.command()
@click.option("--path", type=click.Path(exists=True, file_okay=False, dir_okay=True), 
              help="Optional local directory path (defaults to current directory)")
def update(path):
    """Synchronize changes between local Markdown files and Google Drive folder."""
    update_command(path)


if __name__ == "__main__":
    cli()