# ADR: Markdown to Google Docs Synchronization Utility

## 1. **Title**

Markdown to Google Docs Synchronization Utility (MDSync)

## 2. **Context**

Markdown (`.md`) is commonly used for structured text in software development, documentation, and AI-generated content. However, for collaborative editing, especially with non-technical users, Google Docs is a more accessible format.

Currently, AI-generated `.md` files need to be converted to `.docx` and uploaded manually to Google Drive. After edits in Google Docs, the files must be manually downloaded, converted back to `.md`, and tracked in Git. This workflow is inefficient, making an automated tool desirable.

## 3. **Decision**

We propose building **MDSync**, a lightweight Python utility that automates bidirectional synchronization between Markdown files and Google Docs, leveraging:

- **Pandoc** for format conversion (`.md` ↔ `.docx`)
- **Google Drive API** for automated file transfers
- **GitPython** for version control integration
- **Command-line interface (CLI)** for ease of use
- **Automated branching and merging** to integrate changes seamlessly

## 4. **Options Considered**

### Option 1: Manual Workflow (Status Quo)

- ✅ No additional development effort.
- ❌ Prone to human error and inefficiencies.
- ❌ No version control for Google Docs edits.

### Option 2: Fully Automated Web Service

- ✅ Seamless real-time synchronization.
- ❌ Requires cloud hosting and security considerations.
- ❌ Increased complexity and maintenance burden.

### Option 3: Standalone CLI Utility (Chosen)

- ✅ Simple and local execution.
- ✅ Easy to integrate with GitHub repositories.
- ✅ Minimal dependencies and infrastructure.
- ❌ Requires periodic manual execution.

## 5. **Implementation Plan**

### **Step 1: Basic CLI Prototype**

A single Python script providing the following:

1. **Initialize sync (`mdsync init <path> <google-resource-name>`)**
   - Links a **local folder** to a **Google Drive folder**.
   - Creates a `.mdsync_config.json` tracking the mapping and last sync state.
   - Ensures the folder exists on Google Drive (creates it if necessary).

2. **Sync changes (`mdsync update <optional path>`)**
   - Checks for **changes** in both local `.md` files and remote Google Drive `.docx` files.
   - Converts `.docx` → `.md`, commits changes to Git.
   - Merges changes into `main`, allowing manual resolution of conflicts.
   - Converts finalized `.md` back to `.docx`, overwrites Google Drive files.
   - Ensures `.mdsync_config.json` is updated.

### **Step 2: Extend API Integrations**

- Implement **Google Drive API authentication**.
- Support **tracking file versioning** via metadata.

### **Step 3: GitHub Integration**

- Auto-commit `.md` updates from Google Docs.
- Enable branch-based synchronization.
- Use automated Git branching and merging for conflict resolution.

## 6. **Consequences**

- Simplifies document exchange between Markdown and Google Docs.
- Encourages **structured, versioned writing** workflows.
- Supports **collaborative editing with non-technical users**.
- Automates **directory-level synchronization** between local and Google Drive folders.
- Ensures `.md` remains the **source of truth**, preventing uncontrolled document drift.

## 7. **Open Questions**

- Should the tool track **Google Docs version history** and allow rollbacks?
- How should it handle **merge conflicts** between `.md` edits and Google Docs changes?
- Should deletions in one system be mirrored in the other?
- Should we allow **bi-directional synchronization** automatically or require user confirmation?

## 8. **Status**

🚧 **Prototype in Progress** – CLI-based prototype will be developed first before considering a GUI or web service.

## 9. **Next Steps**

- Implement **basic CLI commands** for `init` and `update`.
- Test integration with **Google Drive API** and **Pandoc**.
- Define **error handling and conflict resolution** strategies.
- Experiment with **automated Git branching & merging**.

---
**Authors:** Aaron Solomon
**Date:** March 2025
