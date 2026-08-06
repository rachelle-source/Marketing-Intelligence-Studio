# Product Vision

## Mission
Research once. Create everywhere.

## Goals
- Centralize client knowledge
- Research before writing
- Maintain brand consistency
- Generate reusable marketing assets

## MVP
- Client Manager
- Reddit Research
- Claude Integration
- AI Writer
- Export Center


# Roadmap

## v1.0
- Foundation
- Client Manager
- Reddit Research
- Claude Integration
- Exports

## v1.1
- Dashboard
- Saved Projects
- Prompt Library

## v2.0
- Multi-source research
- Campaign Builder
- Knowledge Base


# Architecture

## Layers
UI -> Controller -> Services -> Database/API

## Services
- Client
- Research
- AI
- Knowledge
- Export
- Settings

All AI requests flow through the AI Service.


# Database

SQLite

Core Tables:
- Clients
- BrandProfiles
- Projects
- ResearchSessions
- KnowledgeItems
- Content
- Exports
- Settings

Every record belongs to a client.


# Client Schema

Each client stores:
- Company
- Website
- Industry
- Products
- Competitors
- Brand Voice
- Tone
- SEO Keywords
- Avoid Words
- Prompt Templates


# AI Pipeline

Client -> Research -> Knowledge -> Prompt Builder -> Claude -> Validation -> Export -> History

Rules:
- Build prompts from client context.
- Validate every AI response.
- Save outputs for reuse.








