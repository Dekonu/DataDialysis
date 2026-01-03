# 🛡️ Clinical-Sieve: Self-Securing Data Ingestion Engine

A "Safety-First" data pipeline designed to ingest disparate clinical-style datasets. This engine integrates a **Static Analysis** layer to automatically redact PII (Personally Identifiable Information) and enforce schema strictness before data ever touches a persistent database.

## 🏗️ Architectural Decisions: Why Hexagonal?

This engine is built using the **Hexagonal (Ports and Adapters) Architecture**. In a clinical environment, requirements for data sources and storage change constantly, but the **rules for patient safety and PII redaction** remain a constant legal requirement.

[Image of Hexagonal Architecture pattern showing Core Logic surrounded by Adapters and Ports]

### 1. Decoupling the "Sieve" (Core Logic)
The "Sieve"—the PII redaction and validation layer—is a **Pure Python Domain**. It has zero dependencies on databases or external APIs. 
* **The Benefit:** High-stakes security logic can be unit-tested in milliseconds without external infrastructure.

### 2. Interchangeable Adapters
By defining strict **Ports**, infrastructure can be swapped without rewriting business logic:
* **Input Ports:** Easily switch from local `.json` files to streaming FHIR APIs.
* **Output Ports:** Currently uses **DuckDB** for local speed; can be swapped for HIPAA-compliant cloud storage by writing a new Adapter.

### 3. Security as a Middleware
Data *cannot* reach the database without passing through the **Safety Layer**. Security is not a "feature" added at the end; it is the gatekeeper of the entire system.

---

## 🛡️ The "Self-Securing" Philosophy
Unlike traditional pipelines that "Extract, Load, then Transform" (ELT), this engine follows a **Verify-Then-Load** pattern:
1.  **Static Analysis:** Pydantic enforces type safety and schema constraints at the boundary.
2.  **PII Sanitization:** The Sieve redacts sensitive identifiers in-memory.
3.  **Persistence:** Only "Sanitized" objects are permitted to touch the storage adapter.

## 🏗️ Architectural Decisions: Why Hexagonal?
This engine is built using the Hexagonal (Ports and Adapters) Architecture. In a clinical environment, requirements for data sources (XML, FHIR APIs) and storage (SQL, Cloud Buckets) change constantly, but the rules for patient safety and PII redaction remain a constant legal requirement.

### 1. Decoupling the "Sieve" (Core Logic)
The "Sieve"—my PII redaction and validation layer—is a Pure Python Domain. It has zero dependencies on databases or external APIs.

The Benefit: I can test the most high-stakes security logic in milliseconds without spinning up a database.

### 2. Interchangeable Adapters
By defining strict Ports, I can swap infrastructure without rewriting business logic:

Input Ports: Easily switch from a local .json file to a streaming Kafka queue or a hospital's SFTP server.

Output Ports: Currently uses DuckDB for local speed, but can be swapped for a HIPAA-compliant AWS RDS instance simply by writing a new Adapter.

### 3. Security as a Middleware
In this architecture, data cannot reach the database without passing through the Safety Layer. By placing the Sieve at the center of the Hexagon, security isn't a "feature" added at the end; it is the gatekeeper of the entire system.

## 🛡️ The "Self-Securing" Philosophy
Unlike traditional pipelines that "Extract, Load, then Transform" (ELT), this engine follows a Verify-Then-Load pattern.

Static Analysis: Pydantic enforces type safety and schema constraints at the boundary.

PII Sanitization: The Sieve redacts sensitive identifiers in-memory.

Persistence: Only "Sanitized" objects are ever permitted to touch the storage adapter.
