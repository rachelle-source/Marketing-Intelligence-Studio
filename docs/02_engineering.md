# Coding Standards

## Purpose
Ensure consistent, maintainable code across the project.

## Language
- Python 3.12+
- HTML5
- CSS3
- JavaScript (ES6+)

## General Rules
- Prefer readability over cleverness.
- Keep functions focused on one responsibility.
- Use descriptive names.
- Add type hints for new Python code.
- Write docstrings for public classes and functions.

## Project Rules
- UI contains no business logic.
- Business logic lives in services.
- AI requests only through AIService.
- No duplicated client data.


# Security

## Goals
Protect client data and API credentials.

## API Keys
- Store in .env or secure local settings.
- Never commit keys to Git.
- Never hardcode secrets.

## Client Data
- Store locally by default.
- Send only required context to AI providers.

## Network
- Use HTTPS for external requests.
- Validate responses before processing.

## Future
- Encrypted local settings
- Optional cloud sync
- Role-based permissions




## Logging
- Log major operations.
- Log warnings and errors with context.
- Never log API keys or sensitive information.


# Testing

## Philosophy
Every major feature should be testable.

## Test Types
- Unit tests
- Integration tests
- Manual UI testing

## Critical Workflows
- Create client
- Reddit search
- Claude request
- Export document

## Before Release
- No critical errors
- Documentation updated
- Manual smoke test completed


# Deployment

## Platforms
- Windows (.exe)
- macOS (.app)

## Packaging
- PyInstaller (initial)
- Future evaluation of Tauri

## Release Checklist
- Tests pass
- Documentation updated
- Version number updated
- Build installers
- Publish GitHub release

## Backup
Retain previous release artifacts.


# Changelog

## Version 1.0.0

### Added
- Foundation documentation
- Design documentation
- Initial architecture
- Project roadmap

### Planned
- Backend implementation
- Desktop UI
- AI integration

Use semantic versioning:
MAJOR.MINOR.PATCH



# Development Principles

## Primary Goal
Build maintainable software that marketers enjoy using.

## Principles
- Keep modules small.
- Favor composition over inheritance.
- Reuse services instead of duplicating logic.
- Documentation drives implementation.
- Client context should flow through every workflow.

## AI Guidelines
- Read relevant docs before implementing.
- If documentation conflicts with code, explain the conflict.
- Do not invent major features without approval.

## Definition of Done
- Feature implemented
- Tested
- Logged
- Documented
- Matches project documentation



