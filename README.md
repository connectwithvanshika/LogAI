                     RAW LOG FILES
                           │
                           ▼
                 Log Parsing & Cleaning
                           │
                           ▼
               Feature Engineering
        (Extract meaningful log attributes)
                           │
                           ▼
          Exploratory Data Analysis (EDA)
      • Severity Distribution
      • Component Distribution
      • Error Frequency
      • Authentication Analysis
      • Time-based Patterns
                           │
                           ▼
        Text Embedding using LogBERT
     (Convert logs into dense vectors)
                           │
                           ▼
          AutoEncoder Training
 (Learn normal log behaviour in an unsupervised manner)
                           │
                           ▼
         Reconstruction Error Calculation
                           │
                           ▼
        Anomaly Score Generation
                           │
                           ▼
         Detect Abnormal Log Entries
                           │
                           ▼
      Extract Context Around Anomalies
 (Previous logs + Current log + Next logs)
                           │
                           ▼
        Save anomaly_context.json
                           │
                           ▼
      AI-Powered Root Cause Analysis
             (Groq + Llama 3.3 70B)
                           │
                           ▼
      Analyze Top-K Highest Anomalies
   (Selected based on anomaly score to
    optimize API usage and cost)
                           │
                           ▼
      Large Language Model Generates
      • Root Cause
      • Reason
      • Severity
      • Business Impact
      • Recommendations
      • Confidence Score
                           │
                           ▼
       Structured RCA Report (JSON/CSV)
                           │
                           ▼
        AI Incident Investigation Report