# Vidda Agentic Architecture

The following Mermaid diagram outlines the multi-agent ADK backend workflow and how it interacts with the Model Context Protocol (MCP) RAG server and Human-in-the-Loop review process.

```mermaid
flowchart TD
    %% Define styles
    classDef user fill:#2C3E50,stroke:#34495E,stroke-width:2px,color:#fff;
    classDef agent fill:#3498DB,stroke:#2980B9,stroke-width:2px,color:#fff;
    classDef mcp fill:#E67E22,stroke:#D35400,stroke-width:2px,color:#fff;
    classDef db fill:#27AE60,stroke:#2ECC71,stroke-width:2px,color:#fff;
    classDef orchestrator fill:#8E44AD,stroke:#9B59B6,stroke-width:2px,color:#fff;

    %% Nodes
    User([User / Dashboard]):::user
    
    subgraph ADK Multi-Agent System
        Orchestrator{Orchestrator Agent}:::orchestrator
        RoleAgent[Role Extractor Agent]:::agent
        RiskAgent[Risk Extractor Agent]:::agent
        RegAgent[Regulation Extractor Agent]:::agent
        TrainAgent[Training Creator Agent]:::agent
    end

    MCP[(Cloud MCP RAG Server)]:::mcp
    DB[(Vidda Database)]:::db

    %% Workflow Connections
    User -- "1. Uploads Role Description" --> Orchestrator
    
    Orchestrator -- "2. Delegates Extraction" --> RoleAgent
    RoleAgent -- "Returns Responsibilities" --> Orchestrator

    Orchestrator -- "3. Delegates Risk Mapping" --> RiskAgent
    RiskAgent -- "Queries Tools" --> MCP
    MCP -- "Returns Risk Data" --> RiskAgent
    RiskAgent -- "Returns Risk Types" --> Orchestrator

    Orchestrator -- "4. Delegates Compliance Search" --> RegAgent
    RegAgent -- "Queries Tools" --> MCP
    MCP -- "Returns Regulations" --> RegAgent
    RegAgent -- "Returns AMLR Rules" --> Orchestrator

    Orchestrator -- "5. Delegates Plan Generation" --> TrainAgent
    TrainAgent -- "Returns 4-Quarter Plan" --> Orchestrator
    
    Orchestrator -- "6. Saves Draft Plan" --> DB
    
    %% Human In The Loop
    User -- "7. Reviews Draft Plan" --> DB
    User -. "8. Submits Feedback / Revision" .-> TrainAgent
    TrainAgent -. "9. Updates & Saves Revised Plan" .-> DB

```
