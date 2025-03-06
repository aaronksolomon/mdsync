# ADR Update: MDSync Local Google Drive Integration

## 1. **Title**

Revision to MDSync: Local Google Drive Integration Instead of API

## 2. **Context**

The original MDSync design relied on the Google Drive API for file synchronization, which requires significant setup including:

- Creating a Google Cloud project
- Enabling APIs and setting up OAuth consent
- Generating and managing credentials
- Handling OAuth authentication flows

This creates a high barrier to entry for users who simply want to synchronize Markdown files with Google Docs. Since many users already have Google Drive installed locally on their computers, we can leverage this existing infrastructure for a simpler approach.

## 3. **Decision**

We will revise the MDSync implementation to work directly with locally installed Google Drive folders instead of using the Google Drive API. This will significantly simplify the user experience and reduce setup complexity.

## 4. **Design Choices**

### 4.1. **Synchronization Mechanism**

**Decision**: Use local file system operations instead of API calls
**Rationale**: Working directly with the local Google Drive folder removes API complexity and leverages Google's sync engine.
**Alternatives considered**: Continuing with API approach but simplifying authentication, using a hybrid approach.

### 4.2. **Google Drive Path Specification**

**Decision**: Require explicit specification of Google Drive folder path during initialization
**Rationale**: Simplifies implementation by removing the need for platform-specific detection logic. Users know where their Google Drive is mounted on their system.
**Alternatives considered**: Auto-detection of common Google Drive paths, scanning the file system.

### 4.3. **Configuration Storage**

**Decision**: Maintain the JSON configuration file approach (.mdsync_config.json)
**Rationale**: The configuration needs remain similar - we still need to track which local Markdown files correspond to which Google Docs files.
**Alternatives considered**: Simplified tracking with filename-only mapping.

### 4.4. **File Path Management**

**Decision**: Store relative paths in configuration file
**Rationale**: Using relative paths makes the configuration more portable between systems.
**Alternatives considered**: Absolute paths with reconfiguration options.

### 4.5. **Format Conversion Strategy**

**Decision**: Continue using Pandoc for bidirectional conversion
**Rationale**: Pandoc remains the best tool for high-quality conversion between Markdown and DOCX formats.
**Alternatives considered**: Unchanged from original design.

### 4.6. **Synchronization Workflow**

**Decision**: Two-step process - (1) sync from MD to DOCX in Drive folder, (2) sync from DOCX in Drive folder to MD
**Rationale**: This maintains a clear directional flow and allows explicit control of synchronization timing.
**Alternatives considered**: Continuous file system watching, triggered syncs on file changes.

### 4.7. **File Naming Convention**

**Decision**: Maintain the same base filename with different extensions
**Rationale**: Simple 1:1 mapping between file.md and file.docx makes the relationship clear to users.
**Alternatives considered**: Configurable naming patterns, metadata-based mapping.

## 5. **Consequences**

### 5.1. **Positive Consequences**

- Dramatically reduced setup complexity for users
- No need for Google Cloud project or API credentials
- Works with existing Google Drive installations
- Simpler codebase with fewer dependencies
- Works offline (changes sync when connection is restored)
- Leverage's Google's robust sync engine

### 5.2. **Negative Consequences**

- Requires Google Drive to be installed locally
- Limited support on Linux (where Google Drive may not have official desktop client)
- Less programmatic control over the sync process
- Dependent on Google Drive's folder structure and sync behavior
- Potential conflicts with Google Drive's own sync mechanisms
- No access to Google Drive's version history via API

## 6. **Updated Implementation Plan**

### **Step 1: Basic CLI Prototype**

A single Python script providing the following:

1. **Initialize sync (`mdsync init <local-md-path> <google-drive-path>`)**
   - Links a **local folder** with markdown files to a user-specified **Google Drive folder** for DOCX versions
   - Creates a `.mdsync_config.json` tracking the mapping and last sync state
   - Verification that both paths exist and are accessible

2. **Sync changes (`mdsync update <optional path>`)**
   - Convert local `.md` files to `.docx` and copy to Google Drive folder
   - Check for updated `.docx` files in Google Drive folder, convert to `.md` and update local files
   - Track modification timestamps to determine which files need updating
   - Maintain `.mdsync_config.json` state

### **Step 2: Enhanced Testing and Validation**

- Implement file change detection based on modification times
- Add progress indicators for conversion operations
- Add validation of file paths and conversion success

### **Step 3: Conflict Resolution**

- Implement basic conflict detection
- Provide options for conflict resolution strategies
- Add support for Git integration to version control changes

## 7. **Open Questions**

- How should we handle platforms where Google Drive is not available as a local application?
- Should we support other cloud storage providers with local folders (OneDrive, Dropbox)?
- How do we handle the case where Google Drive sync is pending/incomplete?
- What's the best approach for handling file name collisions or special characters?

## 8. **Status**

🔄 **Design Revision** – Updating the PoC to work with local Google Drive installation for testing and evaluation purposes.

## 9. **Short-term Next Steps**

- Update the PoC implementation to work with user-specified local and Google Drive folders
- Test the basic file conversion and synchronization workflow
- Simplify the codebase by removing Google API dependencies
- Add basic validation and error handling for common failure cases

## 10. **Long-term Direction**

While the local Google Drive approach provides a simpler path for the proof of concept and initial testing, the long-term production implementation would likely return to using the Google Drive API but with a web-based interface that streamlines the authorization process:

- **Web Application**: Develop a web interface for MDSync that handles the OAuth flow in the browser
- **Simplified Authentication**: Users would simply click "Connect with Google Drive" and approve access through Google's standard OAuth consent screen
- **Server-side Processing**: Handle file conversions and synchronization on the server side
- **No Local Installation**: Eliminate the need for local Google Drive installation or desktop clients
- **Cross-platform Compatibility**: Work seamlessly across all operating systems and devices
- **Enhanced Features**: Leverage the full Google Drive API for advanced features like sharing, permissions, and version history

This approach would provide the ideal balance of simplicity for users while maintaining the power and flexibility of the API-based approach. The current local-first implementation serves as an important stepping stone for validating core functionality and gathering user feedback before investing in web infrastructure.

---
**Authors:** MDSync Development Team
**Date:** March 2025
