┌─────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION LAYER                                │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    TASK DECOMPOSITION AGENT                         │ │
│  │  • Understands user prompt intent                                   │ │
│  │  • Breaks complex requests into sub-tasks                          │ │
│  │  • Determines required analysis types                               │ │
│  └────────────────────────┬───────────────────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────────────┐
│                    REASONING AGENTS LAYER                                 │
│                                                                          │
│  ┌────────────────────────┴──────────────────────────────────────────┐  │
│  │                    CONTEXT BUILDER AGENT                            │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │ • Data Profiling (auto-detect structure, types, patterns)   │  │  │
│  │  │ • Domain Inference (finance, sales, healthcare, etc.)       │  │  │
│  │  │ • Column Relationship Mapping                                │  │  │
│  │  │ • Semantic Understanding (column name → business meaning)    │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    STRATEGY PLANNER AGENT                            │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │ • Selects analysis methods based on data + prompt           │  │  │
│  │  │ • Determines visualization strategy                          │  │  │
│  │  │ • Plans narrative flow for reports                           │  │  │
│  │  │ • Identifies key metrics & KPIs                              │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────────────┐
│                    EXECUTION AGENTS LAYER                                 │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │ Statistical      │  │ Pattern          │  │ Correlation      │      │
│  │ Analysis Agent   │  │ Detection Agent  │  │ Agent            │      │
│  │                  │  │                  │  │                  │      │
│  │ • Descriptive    │  │ • Trend Analysis │  │ • Pearson        │      │
│  │ • Inferential    │  │ • Seasonality    │  │ • Spearman       │      │
│  │ • Distribution   │  │ • Anomaly Detect │  │ • Mutual Info    │      │
│  │ • Outlier Tests  │  │ • Clustering     │  │ • Cramer's V     │      │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘      │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │ Predictive       │  │ NLP/Text         │  │ Time Series      │      │
│  │ Analysis Agent   │  │ Analysis Agent   │  │ Agent            │      │
│  │                  │  │                  │  │                  │      │
│  │ • Regression     │  │ • Sentiment      │  │ • Decomposition  │      │
│  │ • Classification │  │ • Topic Modeling │  │ • Forecasting    │      │
│  │ • Feature Import │  │ • Entity Extract │  │ • ARIMA/Prophet  │      │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘      │
└──────────────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────────────┐
│                    INSIGHT SYNTHESIS LAYER                                │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    INSIGHT PRIORITIZATION AGENT                      │  │
│  │  • Ranks findings by significance, relevance, actionability         │  │
│  │  • Eliminates redundant insights                                     │  │
│  │  • Identifies contradictory patterns                                 │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    NARRATIVE GENERATION AGENT (LLM)                  │  │
│  │  • Creates executive summaries                                       │  │
│  │  • Generates contextual explanations                                 │  │
│  │  • Builds data storytelling flow                                     │  │
│  │  • Provides actionable recommendations                               │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────────────┐
│                    PRESENTATION LAYER                                     │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    DESIGN INTELLIGENCE AGENT                         │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │ • Layout Selection (appropriate for data type + narrative)   │  │  │
│  │  │ • Color Palette Generation (based on data domain)            │  │  │
│  │  │ • Typography & Visual Hierarchy                              │  │  │
│  │  │ • Responsive Slide Design                                     │  │  │
│  │  │ • Infographic Element Selection                              │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    SLIDE COMPOSER                                    │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │ • Template Engine (Jinja2 + custom templates)                │  │  │
│  │  │ • Chart Embedding (Plotly → Images → Slides)                 │  │  │
│  │  │ • Dynamic Content Layout                                     │  │  │
│  │  │ • Brand Kit Application                                      │  │  │
│  │  │ • Animation & Transition Planning (for PPTX)                 │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘


This needs to be created, currently as a sepratae app as agent under which which a data anlysis agent will be there,
i want you to plan this out as how can we use llamaindex and not write manual codes but uses framework capabilities of llamaindex as well as ours infra.