# Project Overview
This document provides essential context about the Agro-Predict project for AI assistants working on this codebase. It outlines the architecture, key services, and development practices to ensure consistent and informed contributions.

# Project Summary
Agro-Predict is a microservices-based infrastructure designed to provide climate risk prediction services for agricultural operations. It focuses on forecasting frost risks and pest/disease risks to help farmers and agricultural businesses make informed decisions to protect their crops.

**Key Objectives**:

* Monitor agricultural operations using meteorological data and IoT sensor data

* Generate frost risk predictions using historical weather data and future forecasts

* Predict pest and disease risks using weather conditions and sensor data

* Produce detailed PDF reports with digital signatures for professional use

* Sensor data ingestion designed to be pluggable (no provider currently integrated; DTAgro support was removed)

**Technological Context**:

* Service-oriented architecture using microservices

* Deployed via Docker containers with orchestration support

* Designed to be scalable, maintainable, and deployable on cloud environments

# Architecture Overview
The system follows a microservices architecture with service independence and asynchronous communication patterns where appropriate.

## Core Services
**1. Data Service (data-service)**
* Technology: Python (Flask, SQLAlchemy, Celery)

* Purpose: Central data management and persistence layer

* Key Responsibilities:

    * Stores all climatic data, crop information, sensors data, and pest records

    * Exposes REST API (documented via Swagger)

    * Coordinates data ingestion from external sources (AEMET, SIAR, ITACyL)

    * Manages asynchronous tasks via Celery workers

    * Handles database migrations with Alembic

    * Implements security controls via Keycloak integration

**2. Weather Risk Predictor (climate_risks_predictor)**
* Technology: Python

* Purpose: Generates frost and pest risk predictions

* Key Responsibilities:

    * Calculates frost risk using historical and forecasted weather data

    * Evaluates crop-specific temperature thresholds and phenological stages

    * Distinguishes between white and black frost types

    * Tracks accumulated chill hours for different crop varieties

    * Generates PDF reports with recommendations and alerts

    * Provides JSON responses for API integration

**3. MCP-IA Service (mcp-ia-service)**
* Technology: Python (FastMCP)

* Purpose: AI integration layer using Model Context Protocol (MCP)

* Key Responsibilities:

    * Processes raw text responses from AEMET using generative AI

    * Extracts structured weather data from plain text forecasts

    * Uses qwen2.5 model via OLLAMA for text classification

    * Communicates asynchronously via RabbitMQ broker

    * Includes safety fallback to regex parser when AI is unavailable

**4. External Data Adapters**

**AEMET Service (Aemet)**
* Technology: Elixir (OTP)

* Purpose: Periodic meteorological data collection from Spanish State Meteorological Agency AEMET

* Features: Fault-tolerant, supervised process architecture, scheduled data ingestion

**SIAR Service (SiAR)**
* Technology: Java (Spring Boot)

* Purpose: Historical weather data from Agroclimatic Information System for Irrigation

* Features: REST API adapter, data normalization, authentication management

**ITACyL Service (ITACyL)**
* Technology: Java (Spring Boot)

* Purpose: Pest and disease calendar data from ITACyL (Sativum)

* Features: Query filtering by crop code/group, standardized API responses

**5. Orchestrator (agro-predict-orchestrator)**
* Technology: Docker Compose

* Purpose: System-wide orchestration and deployment management

* Features:

    * Two deployment variants: with GPU support (docker/) and without (no-gpu/)

    * Handles container lifecycle and inter-service dependencies

    * Automated environment configuration

# Data Flow
## Frost Prediction Flow
1. User requests frost prediction (observed or future)

2. Predictor service queries Data Service for weather data

3. Data Service checks database for stored data

4. If not available, triggers Ingesta Service to fetch from:

    *  Historical: SIAR (for current day predictions)

    *  Forecast: AEMET (for next-day predictions)

5. AEMET data requires AI processing via MCP-IA Service:

    * Raw text → RabbitMQ → MCP-IA Service → Structured JSON → Data Service

6. Data Service returns normalized data to Predictor

7. Predictor evaluates:

    * Temperature thresholds per crop variety

    * Phenological stage sensitivity

    * Chill hours accumulated

    * White vs. black frost conditions

8. Generates PDF report or JSON response

# Pest Prediction Flow
**Calculated Mode (Calendar-based):**

1. User requests annual pest risk prediction

2. Predictor queries Data Service for ITACyL calendar data

3. Data Service retrieves stored pest calendars

4. Predictor evaluates weekly risk levels per pest

5. Returns assessment with risk levels (PREVENTIVE, CRITICAL, NO RISK)

**Estimated Mode (Sensor-based):**

1. User requests dynamic pest risk prediction with time range

2. Predictor queries Data Service for:

    *  Sensor data from data-service stored measurements (optional; no sensor provider currently integrated)

    *  Historical weather data from SIAR

    *  Forecast data from AEMET

3. Data Service retrieves all data concurrently

4. Predictor evaluates conditions per pest:

    *  Daily conditions (temperature, humidity, etc.)

    * Accumulated conditions (GDD, consecutive days, etc.)

5. Returns risk assessment with detailed context

# Key Technical Concepts
## Data Models
**Agricultural Domain:**

* Crops and Varieties with phenological stages

* Temperature thresholds per stage (critical, high, moderate, low)

* Chill hour models (C7, C07, UF, PF - dynamic)

* Pest definitions with:

    * Required climate variables (recursos)

    * Evaluable conditions (conditional)
 
    * Temporal windows (consecutive days, GDD accumulation)

**Geographic Domain:**

* Provinces, Autonomous Communities, Localities

* Weather stations with altitude coordinates

**Sensor Domain:**

* Sensors, Devices (virtual/physical), Parcels

* Sensor measurements and data sources

**Asynchronous Communication**
* RabbitMQ: Message broker for async operations

* Celery: Distributed task queue for background processing

* Redis: Caching and temporary storage for task management

* Use case: Retrying failed historical data requests, AI processing tasks

**Security**
* Keycloak: Centralized authentication and authorization

* JWT Tokens: Used for API access control

* Security decorator: @token_required for protected endpoints

* Password/Secret management: Environment variables, Azure Key Vault (planned)

**Error Handling**
* Circuit Breaker Pattern: Prevents cascading failures

* Custom APIException: Consistent error responses

* Global Flask error handlers: Structured JSON error responses

* Request IDs: Traceable logging across services

**Report Generation**
* ReportLab: PDF generation with charts and tables

* pyHanko: Digital signatures using PKCS#12 certificates

* Context documentation: Transparent methodology explanations

# Infrastructure & Deployment
## Docker Deployment
* Each service has its own Dockerfile

* Unified orchestration via Docker Compose

* Two deployment modes:

    * Full: Includes AI services (GPU recommended)

    * Lightweight: Without AI services (uses regex parser fallback)

## DevOps Automation
*  GitHub Actions: CI/CD pipeline

* Continuous Integration:

    * Automated testing (pytest, flake8)

    * Code quality checks

    * Build verification on push/pull requests to main branch

* Continuous Deployment:

    * Automatic Docker image building and publishing

    * Image tagging (latest for main, commit hash for branches)

    * Orchestrator repository updates with version tracking

## Infrastructure as Code (IaC)
* Terraform: Infrastructure provisioning

* Azure deployment with:

    * Virtual Machine with Docker

    * Azure Key Vault for secrets

    * Azure Blob Storage for logs
 
* Automated VM initialization script:

    * Installs Docker dependencies
    * Clones orchestrator repository
    * Generates .env file
    * Deploys containers automaticall
## Monitoring
* Structured JSON logging: Decorator-based (@log)

* Request tracking: Unique request_id per transaction

* Log centralization: Blob storage integration (planned)

# Development Practices
## Code Organization
* Repository per service: Independent repositories for each microservice

* Branch strategy:

    * main: Production-ready code

* Feature branches: Development work (prefixed with issue/feature)

* Version control: Git with semantic versioning

## Testing
* Unit tests: Pytest for Python services

* Integration tests: Service-level testing

* Coverage threshold: Minimum 80% coverage required

* Test fixtures: Centralized conftest.py with MagicMock for mocking

## Code Quality
* Linting: Flake8 with configuration

* Complexity limits: Max complexity of 10

* Line length: Maximum 127 characters

* Documentation: OpenAPI/Swagger for API documentation

## Dependency Management
* Python: requirements.txt with pip

* Java: Maven pom.xml

* Elixir: Mix package manager

# Contributing Guidelines for AI Assistants
## When Modifying Code
1. Understand the service boundaries - Each service has distinct responsibilities

2. Maintain the microservices pattern - Keep services loosely coupled

3. Follow existing patterns - Use established decorators, error handlers, and logging

4. Update documentation - Reflect changes in OpenAPI specs and READMEs

5. Write tests - Ensure ≥80% coverage with pytest, also include the test files inside tests directories

6. Consider backward compatibility - API changes affect all consumers

## Key Files to Know
**Data Service:**

* app/: Core logic organized by domain (cultivos, forecast, historicos, ingesta)

* app/ingesta/: ETL coordination for data ingestion

* app/external_communica/: RabbitMQ async communication

* config/: Environment-specific configurations

* migrations/: Alembic database migrations

**Climate Risks Predictor:**

* app/: Prediction logic, threshold evaluation, alert generation

* config/: Service configuration and thresholds

* swagger/: OpenAPI specification

**MCP-IA Service:**

* mcp_ia_server/: FastMCP server implementation

* services/: Business logic for AI integration

## Common Tasks
**Adding a new pest:**

* Define pest JSON document using the DSL template in docs/dsl path.

* Ensure required resources match existing data models

* Specify evaluable conditions and temporal windows

* Test with both calculated and estimated prediction modes

**Adding a new crop variety:**

* Register crop via Data Service API

* Register variety with its phenological stages

* Assign temperature thresholds per stage

* Associate with chill hour model

**Adding a new data source:**

1. Implement external service adapter

2. Configure data ingestion in Data Service

3. Add necessary database models and migrations

4. Update documentation

# Environment Configuration
## Required Environment Variables
**Minimum required for deployment:**

* Database credentials (MariaDB)

* Redis configuration

* RabbitMQ credentials

* External API keys (AEMET, SIAR, ITACyL)

* Keycloak authentication details

## Security Notes
* Never hardcode credentials

* Use environment variables or secrets management

* Development and production use separate configurations

# Resources
* GitHub public repository: https://github.com/alvaromendoooo/agropredict

* infra/local path: Contains Docker Compose configurations

* API Documentation: Swagger/OpenAPI specs in each service

* Deployment Guide: See Anexo B in documentation

* User Manual: See Anexo C in documentation

# Common AI Interaction Patterns
## When Asked to Implement a Feature
0. Generate a Plan vision which will contains all the new and fixing code that you will introduce including WHY, then i will approve or not the changes.

1. Analyze the service scope - Which service should contain this logic?

2. Check data availability - Does Data Service already have required data?

3. Consider async/async - Should this be synchronous or asynchronous?

4. Plan error handling - What can go wrong and how to handle it?

5. Test thoroughly - Unit tests, integration tests, coverage

## When Asked to Debug an Issue
1. Check logs - Request IDs help trace flows across services

2. Verify data availability - Is data present in the database?

3. Check external service status - Are AEMET/SIAR/ITACyL responding?

4. Validate input format - Is the request properly structured? In root directory there is a backup.sql that contains current DB data.

5. Review recent changes - What changed in the codebase recently?