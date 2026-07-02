# Project Workflow

The project follows an end-to-end AI-driven pipeline for automated **Log Anomaly Detection** and **Root Cause Analysis (RCA)**. The workflow is illustrated below:


## Workflow Overview

1. **Data Preprocessing**
   - Parse and clean raw system logs.
   - Extract structured attributes such as timestamps, components, severity levels, authentication status, and error flags.

2. **Feature Engineering**
   - Generate meaningful numerical and categorical features for anomaly detection.

3. **Exploratory Data Analysis**
   - Understand log characteristics through statistical analysis and visualizations.

4. **Log Representation**
   - Convert textual log messages into contextual embeddings using **LogBERT**.

5. **Unsupervised Anomaly Detection**
   - Train an **AutoEncoder** exclusively on normal log patterns.
   - Compute reconstruction errors to assign anomaly scores.

6. **Context-Aware Analysis**
   - Extract surrounding log events for every detected anomaly to preserve execution context.

7. **LLM-Based Root Cause Analysis**
   - Use **Llama 3.3 70B (Groq API)** to perform intelligent incident investigation.
   - Generate comprehensive RCA reports including probable causes, impact assessment, troubleshooting steps, long-term fixes, and preventive recommendations.

8. **Final Output**
   - Produce structured JSON/CSV reports along with an AI-generated incident investigation summary suitable for Site Reliability Engineers (SREs), DevOps teams, and Production Support Engineers.