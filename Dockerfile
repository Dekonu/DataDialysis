# Optimized single-stage build for Data-Dialysis Dashboard API
FROM python:3.13-slim

WORKDIR /app

# Install build dependencies (only if needed for Python packages that require compilation)
# Install runtime dependencies and build tools in one layer to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Copy requirements and install Python packages system-wide (more space-efficient)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    # Remove build dependencies after installation to save space
    apt-get purge -y gcc && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Ensure uvicorn and other scripts are in PATH (system-wide installation)
ENV PATH=/usr/local/bin:$PATH

# Copy application code
COPY src/ ./src/
COPY pyproject.toml .
COPY pytest.ini .

# Change ownership of app directory
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/health', timeout=5)" || exit 1

# Run application
CMD ["uvicorn", "src.dashboard.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

