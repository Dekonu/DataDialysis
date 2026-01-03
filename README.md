# 🛡️ Clinical-Sieve: Self-Securing Data Ingestion Engine

A "Safety-First" data pipeline designed to ingest disparate clinical-style datasets. This engine integrates a **Static Analysis** layer to automatically redact PII (Personally Identifiable Information) and enforce schema strictness before data ever touches a persistent database.

## 🏗️ Architectural Decisions: Why Hexagonal?

This engine is built using the **Hexagonal (Ports and Adapters) Architecture**. In a clinical environment, requirements for data sources and storage change constantly, but the **rules for patient safety and PII redaction** remain a constant legal requirement.



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



---

## 📍 Project Roadmap & Implementation Status

### **Phase 1: Architecture & Safety Layer (Weeks 1-2)**
*Goal: Establish the "Golden Record" and strict schema enforcement.*
- [x] Define Pydantic "Golden Record" schemas for clinical entities.
- [ ] Implement `defusedxml` safety wrappers to prevent XML-based attacks.
- [ ] Build the **JSON Adapter** (Input Port).
- [ ] **Milestone:** Block malformed records before they reach the core logic.

### **Phase 2: The Sieve - Static Analysis (Weeks 3-5)**
*Goal: Automated PII detection and data standardization.*
- [ ] Develop a **Regex-based Redactor** for SSNs, phone numbers, and IDs.
- [ ] Integrate **Pandas Vectorized Transformation** for batch cleaning.
- [ ] Implement a **Circuit Breaker**: Auto-kill ingestion if error rates exceed 10%.
- [ ] **Milestone:** Ingest "dirty" data and output "clean" standardized data.

### **Phase 3: Persistence & Observability (Weeks 6-8)**
*Goal: Clinical-grade audit trails and analytical storage.*
- [ ] Implement **DuckDB Adapter** (Output Port) for local analytical storage.
- [ ] Create an **Immutable Audit Log**: Track every redaction event with timestamps and hashes.
- [ ] Build a **Streaming XML Adapter** using `lxml.iterparse` for memory efficiency.
- [ ] **Milestone:** Process a 100MB+ file with a complete transformation history.

### **Phase 4: Refinement & Demo (Weeks 9-10)**
*Goal: Portfolio readiness and performance tuning.*
- [ ] Build a **CLI Interface** using `Typer` for easy engine execution.
- [ ] Implement a **Project Dashboard** (Streamlit) to visualize ingestion health.
- [ ] Document the **Threat Model** and Security Decisions.
- [ ] **Milestone:** MVP complete and ready for demonstration.

---

## 🚀 Future Enhancements
- **NLP Integration:** Use `SpaCy` for advanced Named Entity Recognition in unstructured clinical notes.
- **Containerization:** Dockerize the pipeline as a portable microservice.
- **FHIR Compatibility:** Mapping to HL7 FHIR R4 standards.

---

## 🛠️ Tech Stack
* **Language:** Python 3.11+
* **Validation:** Pydantic V2
* **Data Processing:** Pandas / PyArrow
* **Database:** DuckDB (In-process OLAP)
* **Security:** DefusedXML / Custom Regex Sieve
