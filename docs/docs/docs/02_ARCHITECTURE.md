# Marketing Intelligence Studio
# Software Architecture

**Version:** 1.0

**Status:** Living Document

**Last Updated:** August 2026

---

# Purpose

This document defines the software architecture for Marketing Intelligence Studio.

It explains:

- How the application is organized
- How components communicate
- Where new code belongs
- How data flows
- How AI is integrated
- How future features should be added

This document is the architectural source of truth.

---

# Architectural Philosophy

Marketing Intelligence Studio follows five guiding principles.

## 1. Modular First

Every feature should be isolated.

Features communicate through services rather than directly calling each other.

Good:

```
Research Service

↓

AI Service

↓

Export Service
```

Avoid:

```
Research directly calls Export

Research directly calls UI

Research directly edits database
```

---

## 2. Single Responsibility

Every module should have one purpose.

Examples

Client Service

Research Service

AI Service

Export Service

Knowledge Service

Settings Service

---

## 3. AI Is a Service

Claude is not part of the application logic.

Claude is a service used by the application.

Every AI request flows through one centralized AI Service.

No module should call Claude directly.

```
UI

↓

AI Service

↓

Prompt Builder

↓

Claude API

↓

Validation

↓

Results
```

---

## 4. Client-Centered Design

Everything belongs to a client.

Research belongs to a client.

Projects belong to a client.

Knowledge belongs to a client.

Content belongs to a client.

Exports belong to a client.

Nothing should exist without a client context.

---

## 5. Research Before Content

The application is designed around research.

Content generation should always be informed by:

Customer questions

Pain points

Competitors

Knowledge Base

Brand Profile

---

# High-Level Architecture

```text
Desktop Application
        │
        ▼
User Interface
        │
        ▼
Application Controller
        │
        ▼
Business Services
        │
        ├── Client Service
        ├── Research Service
        ├── Knowledge Service
        ├── AI Service
        ├── Export Service
        └── Settings Service
        │
        ▼
Database
        │
        ▼
SQLite
```

---

# Application Layers

## Presentation Layer

Responsible for:

User Interface

Navigation

Forms

Progress

Notifications

No business logic belongs here.

---

## Service Layer

The heart of the application.

Contains:

Research

Clients

AI

Exports

Knowledge

Settings

History

Every feature is implemented here.

---

## Data Layer

Responsible for:

SQLite

Repositories

Queries

Persistence

No UI logic.

No AI logic.

---

## External Services

Claude API

Reddit

Google News

RSS

Future APIs

All external communication goes through dedicated adapters.

---

# Folder Structure

```
marketing-intelligence-studio/

backend/
    ai/
    clients/
    database/
    exports/
    knowledge/
    reddit/
    research/
    services/
    settings/
    utils/

frontend/
    assets/
    components/
    css/
    js/

clients/

docs/

logs/

output/

tests/

app.py
```

---

# Service Responsibilities

## Client Service

Creates clients.

Updates clients.

Loads brand profiles.

Provides client context.

---

## Research Service

Coordinates research.

Starts Reddit searches.

Imports news.

Collects sources.

Stores research.

---

## Knowledge Service

Extracts reusable information.

Questions

Pain Points

Competitors

FAQs

Terminology

---

## AI Service

Centralized AI communication.

Responsibilities:

Prompt building

Claude requests

Retries

Streaming

Response parsing

Validation

Future provider support

---

## Export Service

Converts content into:

Markdown

HTML

DOCX

PDF

---

## Settings Service

Application settings.

Theme.

Claude model.

API Keys.

Export location.

Preferences.

---

# Data Flow

Research follows the same path every time.

```
Client

↓

Research

↓

Knowledge Extraction

↓

Prompt Builder

↓

Claude

↓

Validation

↓

Content

↓

Export

↓

History
```

This pipeline should remain consistent across every feature.

---

# Plugin Architecture

Future research sources should be plugins.

Examples:

Reddit

Google News

RSS

YouTube

Reviews

Forums

Each plugin should expose a common interface:

```
Search

Collect

Normalize

Return Sources
```

This allows new data sources to be added without changing the rest of the application.

---

# AI Architecture

AI is divided into four stages.

Prompt Builder

↓

Claude API

↓

Validation

↓

Formatting

Future AI providers should implement the same interface so the application is not tied to one vendor.

---

# UI Architecture

The UI should remain thin.

The interface sends requests to services.

Services perform work.

The UI displays results.

The UI should never:

Query SQLite directly.

Call Claude directly.

Run Reddit searches.

---

# Error Handling

Every service returns structured errors.

The UI displays friendly messages.

Errors are logged.

Unexpected exceptions are captured for debugging.

---

# Logging

All major operations should be logged.

Research

AI Requests

Exports

Errors

Performance

Application Startup

---

# Testing Strategy

Every service should have unit tests.

Critical workflows should have integration tests.

UI behavior should be tested separately.

---

# Performance Goals

Application launch:

< 3 seconds

Client loading:

Instant

Research progress:

Live updates

Large exports:

Background processing

AI requests:

Retry automatically when appropriate

---

# Security

API keys remain outside the database.

Sensitive data is encrypted when appropriate.

No unnecessary network traffic.

Only required information is sent to AI providers.

---

# Future Expansion

The architecture should support:

Cloud sync

Multiple AI providers

Plugins

Team collaboration

REST API

Workflow automation

Without requiring major redesign.

---

# Architectural Rules

Always separate UI from business logic.

Never duplicate client information.

Never call external APIs directly from the UI.

Keep modules small.

Favor composition over inheritance.

Document every public service.

Every feature must fit within the existing architecture.

---

# Definition of Success

The architecture succeeds when:

New features can be added without modifying existing modules.

The codebase remains easy to understand.

Services remain independent.

The UI remains simple.

Every workflow follows the same pipeline.

Future growth does not require rewriting the foundation.
