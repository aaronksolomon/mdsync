# ADR: MDSync Proof of Concept Implementation Decisions

## 1. **Title**

MDSync Proof of Concept Implementation - Design Decisions

## 2. **Context**

Following the original ADR outlining the needs for a Markdown to Google Docs synchronization utility (MDSync), we needed to create a walking skeleton implementation that focuses on core functionality while making pragmatic design choices for rapid prototyping.

The implementation needed to satisfy key requirements:

- Bidirectional synchronization between local Markdown files and Google Docs
- Command-line interface for developer workflows
- Google Drive integration
- File format conversion

## 3. **Decision**

We implemented a single-file Python application that provides the core functionality outlined in the original ADR while prioritizing simplicity and rapid development for the proof of concept stage.

## 4. **Design Choices**

### 4.1. **Package Structure**

**Decision**: Single file implementation
**Rationale**: For a PoC, a single file reduces complexity and provides a clear overview of all components. This approach makes it easier to review, modify, and extend during the experimental phase.
**Alternatives considered**: Multi-file package structure with separate modules for Google Drive API, conversion logic, and CLI interface.

### 4.2. **CLI Framework**

**Decision**: Click framework
**Rationale**: Click provides a more declarative and user-friendly approach to CLI development compared to argparse. Its decorator pattern aligns better with Python idioms, and it offers built-in features like input validation, help text formatting, and progress bars with minimal additional code.
**Alternatives considered**: argparse (standard library), typer, fire.

### 4.3. **Configuration Storage**

**Decision**: JSON file (.mdsync_config.json)
**Rationale**: JSON provides a human-readable format that's easy to parse and modify. Storing in a local file avoids database dependencies while still allowing for persistent state management.
**Alternatives considered**: SQLite database, YAML configuration, INI file.

### 4.4. **Authentication Approach**

**Decision**: OAuth 2.0 with local credential storage
**Rationale**: OAuth 2.0 is the standard authentication method for Google APIs. Storing credentials locally in the user's home directory (`~/.mdsync/`) follows security best practices by isolating tokens per user.
**Alternatives considered**: Service account authentication, API key authentication.

### 4.5. **File Conversion Strategy**

**Decision**: Pandoc as external dependency
**Rationale**: Pandoc is the industry standard for document format conversion with excellent Markdown and DOCX support. Using subprocess calls to Pandoc leverages its capabilities without needing to implement conversion logic.
**Alternatives considered**: Python-based conversion libraries (python-docx + markdown), custom conversion logic.

### 4.6. **Synchronization Approach**

**Decision**: Timestamp-based synchronization
**Rationale**: Using modification timestamps provides a simple mechanism to determine which files need updating, avoiding unnecessary conversions and uploads/downloads.
**Alternatives considered**: Hash-based file comparison, full synchronization of all files on each run.

### 4.7. **Error Handling Strategy**

**Decision**: Basic error reporting with minimal recovery
**Rationale**: For a PoC, simple error messages with early returns keeps the code straightforward while still providing useful feedback to users.
**Alternatives considered**: Comprehensive exception handling with automatic retries and detailed logging.

### 4.8. **File Discovery**

**Decision**: Simple glob pattern for .md files in the root directory
**Rationale**: This approach focuses on the primary use case (synchronizing Markdown files in a single directory) without complicating the implementation.
**Alternatives considered**: Recursive directory traversal, configurable file inclusion/exclusion patterns.

### 4.9. **Conflict Resolution**

**Decision**: Last-write-wins strategy
**Rationale**: A simple timestamp-based approach avoids complex merge logic for the PoC, allowing us to demonstrate the basic workflow.
**Alternatives considered**: Interactive conflict resolution, Git-based three-way merges.

### 4.10. **Google Drive Integration**

**Decision**: Direct use of Google API Client Library
**Rationale**: Using the official client library ensures compatibility with Google's API changes and security practices.
**Alternatives considered**: Third-party wrappers like PyDrive2.

### 4.11. **User Feedback**

**Decision**: Progress bars for long-running operations
**Rationale**: Visual feedback for file uploads and downloads improves user experience by providing visibility into operation progress.
**Alternatives considered**: Simple console messages, silent operation with final summary.

## 5. **Consequences**

### 5.1. **Positive Consequences**

- Simplified development and maintenance during the PoC phase
- Clear demonstration of core functionality
- Easier onboarding for developers to understand the entire workflow
- Reduced dependencies and external requirements
- Quick implementation time

### 5.2. **Negative Consequences**

- Limited scalability for large numbers of files or complex directory structures
- Basic conflict resolution may lead to data loss in certain scenarios
- Single-file approach will require refactoring for production use
- No automated Git integration for version control of changes

## 6. **Open Questions**

- How should we handle nested directory structures?
- What is the best approach for tracking deletions across systems?
- Should we implement a more sophisticated conflict resolution strategy?
- How should we handle multiple users editing the same Google Doc?
- What metadata should be preserved during format conversion?

## 7. **Status**

✅ **Implemented** - PoC developed with design decisions as outlined above.

## 8. **Next Steps**

- Gather feedback on the PoC implementation
- Test with real-world document synchronization scenarios
- Evaluate which design decisions should be carried forward to the production implementation
- Plan refactoring into a proper package structure with separation of concerns
- Add test coverage for critical functionality

---
**Authors:** MDSync Development Team
**Date:** March 2025
