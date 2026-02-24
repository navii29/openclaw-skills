# 🎯 Navii Automation System Architecture

```mermaid
flowchart TB
    subgraph Input["📥 INPUT SOURCES"]
        LI[LinkedIn Profiles]
        HN[HackerNews Show HN]
        MB[Moltbook Posts]
        GH[GitHub API]
        MAN[Manual Entry]
    end

    subgraph Core["🧠 LEAD INTELLIGENCE ENGINE"]
        WEB[Webhook Trigger]
        SCORE[Scoring Algorithm<br/>0-100 Punkte]
        TIER{Tier Classification}
    end

    subgraph Processing["⚙️ PROCESSING LAYER"]
        CODE1[Code Node:<br/>Lead Scoring]
        CODE2[Code Node:<br/>Outreach Generation]
        CODE3[Code Node:<br/>Report Generation]
    end

    subgraph Storage["💾 STORAGE"]
        NOTION[(Notion Database<br/>Lead Pipeline)]
        N8N_DB[(n8n Executions)]
    end

    subgraph Output["📤 OUTPUT CHANNELS"]
        SLACK[Slack Alerts<br/>#leads]
        EMAIL[Email Sequences]
        CAL[Calendly Booking]
        WEBHOOK[API Response]
    end

    subgraph Subagents["🤖 SUB-AGENT SYSTEM"]
        SA1[Lead Research Agent]
        SA2[Content Generator Agent]
        SA3[Outreach Writer Agent]
        SA4[Monitor Agent]
    end

    %% Data Flow
    LI --> WEB
    HN --> SA1
    MB --> SA1
    GH --> SA1
    MAN --> WEB

    WEB --> SCORE
    SCORE --> TIER
    
    TIER -->|HOT| CODE1
    TIER -->|WARM| CODE1
    TIER -->|COLD| CODE1

    CODE1 --> CODE2
    CODE2 --> NOTION
    
    NOTION --> SLACK
    NOTION --> EMAIL
    NOTION --> CAL
    
    CODE2 --> WEBHOOK
    
    SA1 -.->|found leads| WEB
    SA2 -.->|generates| CODE3
    SA3 -.->|writes| CODE2
    SA4 -.->|monitors| NOTION
    
    %% Styling
    style Input fill:#e1f5ff
    style Core fill:#fff3e0
    style Processing fill:#f3e5f5
    style Storage fill:#e8f5e9
    style Output fill:#ffebee
    style Subagents fill:#e8eaf6
```

---

## 📊 Detailed Component View

```mermaid
flowchart LR
    subgraph "🔗 LinkedIn Lead Intelligence"
        A[Webhook: linkedin-lead] --> B{Scoring Engine}
        B -->|Score ≥80| C[🔥 HOT Lead]
        B -->|Score 60-79| D[⚡ WARM Lead]
        B -->|Score <60| E[🧊 COLD Lead]
        
        C --> F[Generate Outreach]
        D --> F
        E --> F
        
        F --> G[Save to Notion]
        G --> H[Slack Alert]
        G --> I[API Response]
    end
```

---

## 🔄 Daily Operations Flow

```mermaid
sequenceDiagram
    participant Schedule as ⏰ Schedule Trigger
    participant Notion as 🗄️ Notion DB
    participant Code as 🧮 Code Node
    participant Slack as 💬 Slack
    participant Email as 📧 Gmail

    Schedule->>Notion: Get Leads (last 24h)
    Notion-->>Schedule: Lead Data
    Schedule->>Code: Generate Report
    Code->>Code: Calculate Stats
    Code->>Code: Format Message
    Code->>Slack: Send Daily Report
    Code->>Email: Send Email Report
    Slack-->>Code: Confirm
    Email-->>Code: Confirm
```

---

## 🏗️ System Layers

| Layer | Komponenten | Funktion |
|-------|-------------|----------|
| **Input** | LinkedIn, HN, Moltbook, GitHub | Lead Discovery |
| **Orchestration** | n8n Workflows | Prozess-Steuerung |
| **Intelligence** | Scoring Algorithm | Lead Qualifizierung |
| **Processing** | Code Nodes, Subagenten | Daten-Verarbeitung |
| **Storage** | Notion, n8n DB | Persistenz |
| **Output** | Slack, Email, Calendly | Kommunikation |

---

## 🎯 Lead Journey

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   DISCOVER  │────▶│    SCORE    │────▶│   SEGMENT   │
│             │     │             │     │             │
│ • LinkedIn  │     │ 0-100 Pts   │     │ 🔥 HOT      │
│ • HackerNews│     │             │     │ ⚡ WARM      │
│ • GitHub    │     │ Criteria:   │     │ 🧊 COLD      │
│ • Moltbook  │     │ • Title     │     │             │
│             │     │ • Industry  │     │             │
└─────────────┘     │ • Signals   │     └─────────────┘
                    └─────────────┘            │
                                               ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   CONVERT   │◀────│   ENGAGE    │
                    │             │     │             │
                    │ • Meeting   │     │ • Outreach  │
                    │ • Proposal  │     │ • Follow-up │
                    │ • Close     │     │ • Nurture   │
                    └─────────────┘     └─────────────┘
```

---

## 🤖 Sub-Agent Network

```
                    ┌─────────────────┐
                    │  MAIN AGENT     │
                    │    (Navii)      │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ LEAD RESEARCH │   │   CONTENT     │   │   MONITOR     │
│    AGENT      │   │   GENERATOR   │   │    AGENT      │
│               │   │               │   │               │
│ • GitHub API  │   │ • LinkedIn    │   │ • Web Checks  │
│ • HN Search   │   │ • Blog Posts  │   │ • Alerts      │
│ • Profile Sc. │   │ • Templates   │   │ • Reports     │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  SHARED MEMORY  │
                    │  (Notion/DB)    │
                    └─────────────────┘
```

---

## 📈 Data Flow Diagram

```mermaid
graph LR
    A[Raw Lead Data] --> B{Lead Scoring}
    B -->|Score| C[Tier Assignment]
    C --> D[Outreach Generation]
    D --> E[Notion Database]
    E --> F[Slack/Email]
    
    G[Daily Trigger] --> H[Report Generator]
    H --> I[Stats Aggregation]
    I --> J[Slack Report]
    I --> K[Email Report]
    
    L[GitHub API] --> M[Profile Scanner]
    M --> N[Lead Extractor]
    N --> A
```

---

## 🎨 Visual Overview (ASCII)

```
┌─────────────────────────────────────────────────────────────────┐
│                    NAVII AUTOMATION SYSTEM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INPUTS                    CORE ENGINE              OUTPUTS     │
│  ───────                   ──────────              ───────     │
│                                                                 │
│  ┌────────┐               ┌──────────┐           ┌────────┐   │
│  │LinkedIn│──────────────▶│  WEBHOOK │──────────▶│ Notion │   │
│  └────────┘               └──────────┘           └────────┘   │
│       │                         │                     │        │
│       │                   ┌─────▼─────┐              │        │
│       │                   │SCORING    │              ▼        │
│       │                   │ENGINE     │          ┌────────┐   │
│       │                   └─────┬─────┘          │ Slack  │   │
│       │                         │               └────────┘   │
│  ┌────────┐               ┌─────▼─────┐              │        │
│  │GitHub  │──────────────▶│   CODE    │──────────▶│ Gmail  │   │
│  └────────┘               │   NODE    │           └────────┘   │
│       │                   └───────────┘                        │
│       │                          │                             │
│  ┌────────┐               ┌─────▼─────┐                       │
│  │Hacker  │──────────────▶│ SUBAGENT  │                       │
│  │News    │               │ SYSTEM    │                       │
│  └────────┘               └───────────┘                       │
│                                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

*Letzte Aktualisierung: 2026-02-19*
