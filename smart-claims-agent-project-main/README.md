# SmartClaims AI Agent
### AI-Powered Insurance Claims Assistant using Microsoft Foundry & Azure AI

SmartClaims is an **AI-powered insurance claims assistant** built using **Microsoft Foundry Agent Service, Azure OpenAI, and FastAPI**.

The system integrates multiple AI capabilities to automate insurance workflows such as **policy question answering, claims analytics, fraud detection, and regulatory information retrieval**.

---

# Project Architecture

The SmartClaims system combines multiple AI components:

- **Microsoft Foundry Agent Service** – AI agent orchestration
- **Azure OpenAI Models** – Natural language understanding
- **File Search (RAG)** – Policy document retrieval
- **Code Interpreter** – Claims dataset analysis
- **Custom Function Tools** – Claim status and fraud risk scoring
- **Web Search Integration** – Real-time regulatory updates
- **FastAPI Web Application** – User interaction interface
- **Azure Web App** – Cloud deployment

---

# Features

- Policy document Q&A using **Retrieval-Augmented Generation (RAG)**
- Claims dataset analysis using **AI-powered analytics**
- Fraud risk detection using **custom function tools**
- Real-time regulatory updates via **web search**
- Interactive **FastAPI web application**
- **Azure cloud deployment**

---

# Project Structure

```
smartclaims-agent
│
├── app/                 # FastAPI web application
├── labs/                # Project scripts
├── data/                # Sample datasets and policy documents
├── utils/               # Utility functions
├── outputs/             # Generated outputs
├── requirements.txt     # Python dependencies
├── startup.sh           # Azure Web App startup script
└── README.md            # Project documentation
```

---

# Technologies Used

### Programming
- Python
- FastAPI

### Azure AI Services
- Microsoft Foundry Agent Service
- Azure OpenAI
- Azure Web App

### AI Capabilities
- Retrieval-Augmented Generation (RAG)
- Code Interpreter
- Function Calling
- Web Search Integration