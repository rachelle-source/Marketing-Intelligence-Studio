# Marketing Intelligence Studio
# Database Design

**Version:** 1.0

**Status:** Living Document

**Last Updated:** August 2026

---

# Purpose

This document defines how Marketing Intelligence Studio stores information.

The database is designed around one principle:

> **Every piece of information should have a single source of truth.**

Client information should never be duplicated.

Research should never be lost.

AI outputs should remain connected to the research that generated them.

Every relationship should be traceable.

---

# Database Philosophy

The database is organized around five core concepts.

```
Clients

↓

Research

↓

Knowledge

↓

Content

↓

Exports
```

Everything in the application connects back to a client.

---

# Database Engine

Version 1.0 uses:

SQLite

Reasons:

- Fast
- Local
- Reliable
- No server required
- Cross-platform
- Easy backup
- Excellent Python support

Future versions may support PostgreSQL for team collaboration.

---

# Core Tables

The following tables form the foundation of the application.

---

## Clients

Purpose

Stores permanent information about every client.

Examples

KORE

KORR

8MSolar

CEI

McFie Insurance

Fields

Client ID

Company Name

Website

Industry

Description

Created Date

Updated Date

Status

Relationships

One client has many:

Projects

Research Sessions

Knowledge Items

Content Pieces

Exports

Settings

---

## Brand Profiles

Purpose

Stores brand-specific writing guidance.

Each client has one active profile.

Fields

Profile ID

Client ID

Brand Voice

Writing Style

Tone

Target Audience

Avoid Words

Preferred Calls To Action

Preferred Terminology

Competitors

SEO Keywords

Internal Notes

Future Support

Multiple versions

Seasonal campaigns

Product-specific messaging

---

## Projects

Purpose

Groups related work together.

Examples

August Blog Campaign

Powerwall Landing Page

KORE Reddit Research

Product Launch

Fields

Project ID

Client ID

Name

Description

Status

Created Date

Last Updated

Relationships

One project contains many:

Research Sessions

Content Pieces

Exports

Notes

---

## Research Sessions

Purpose

Represents one research activity.

Examples

Reddit Search

Google News Search

Competitor Research

Review Analysis

Fields

Research ID

Client ID

Project ID

Research Type

Search Query

Created Date

Status

AI Summary

Relationships

One research session contains many:

Sources

Knowledge Items

Generated Content

---

## Research Sources

Purpose

Stores every source collected during research.

Examples

Reddit Thread

News Article

YouTube Video

Review

Forum Discussion

Fields

Source ID

Research ID

Title

URL

Platform

Author

Date

Content

AI Summary

Relevance Score

---

## Knowledge Base

Purpose

Stores reusable marketing intelligence.

Unlike Research Sources, Knowledge Items are permanent insights.

Examples

Pain Point

Customer Question

Common Objection

Competitor Mention

Industry Trend

Frequently Asked Question

Fields

Knowledge ID

Client ID

Research ID

Category

Title

Description

Confidence Score

Source Count

Tags

Created Date

---

## Content

Purpose

Stores every AI-generated marketing asset.

Examples

Blog

Landing Page

LinkedIn Post

Facebook Post

FAQ

Email

Google Ad

Display Ad

Fields

Content ID

Client ID

Project ID

Research ID

Content Type

Title

Body

Version

Status

AI Model

Created Date

---

## Prompt Templates

Purpose

Stores reusable AI prompts.

Examples

Blog Prompt

SEO Prompt

LinkedIn Prompt

Email Prompt

Landing Page Prompt

Fields

Prompt ID

Name

Category

System Prompt

User Prompt

Version

Status

---

## Exports

Purpose

Tracks generated files.

Fields

Export ID

Content ID

Format

Location

Created Date

Version

Supported Formats

Markdown

HTML

DOCX

PDF

TXT

---

## Search History

Purpose

Stores all completed searches.

Fields

History ID

Client

Search Type

Query

Results

Created Date

Execution Time

Status

---

## Settings

Purpose

Application configuration.

Examples

Theme

Claude Model

Export Folder

API Keys

Language

Auto Save

Logging

---

## Activity Log

Purpose

Records important application events.

Examples

Client Created

Research Started

Export Generated

AI Request

Error

Settings Changed

Fields

Activity ID

Timestamp

Severity

Category

Message

---

# Relationships

```
Client

├── Brand Profile

├── Projects

│     ├── Research Sessions

│     │       ├── Sources

│     │       └── Knowledge

│     ├── Content

│     └── Exports

│

└── Settings
```

Every object ultimately belongs to a Client.

---

# Data Lifecycle

Research

↓

Knowledge Extraction

↓

Knowledge Base

↓

AI Content

↓

Export

↓

History

Nothing should be discarded unless the user deletes it.

---

# Data Retention

The application should retain:

Research

Knowledge

Generated Content

Prompt History

Exports

Logs

Deleting a client should require confirmation and clearly explain what related data will be removed.

---

# Search Strategy

All major entities should support search.

Clients

Projects

Research

Knowledge

Content

Exports

Prompt Templates

Future versions may support semantic search using AI-generated embeddings.

---

# Backup Strategy

Version 1.0

Manual backup

Database export

Automatic backup on application exit (optional)

Future Versions

Cloud synchronization

Version history

Point-in-time restore

---

# Security

Sensitive data includes:

Claude API Keys

Client Notes

Internal Research

Prompt Templates

Sensitive data should never be exposed unnecessarily.

API keys should never be stored directly in the SQLite database.

They should remain in encrypted local configuration or environment variables.

---

# Future Database Expansion

Planned future tables include:

Campaigns

Calendars

Tasks

Team Members

Permissions

Plugins

AI Conversations

Competitor Monitoring

SEO Audits

Analytics

Workflow Templates

---

# Database Design Principles

Every table should have:

A unique primary key.

Creation timestamp.

Last modified timestamp.

Relationships rather than duplicated information.

Clear ownership by a Client.

No unnecessary redundancy.

---

# Definition of Success

The database succeeds when:

Every client has one authoritative profile.

Research is reusable.

Content is traceable to its source.

Relationships are clear.

No information is duplicated.

The schema remains flexible enough to support future features without major redesign.
