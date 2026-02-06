# AI Operations Assistant

A multi-agent AI system that accepts natural-language tasks, plans execution steps, calls real APIs, and returns structured answers.

## Architecture

The system uses a **three-agent architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                    User Natural Language Task                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      PLANNER AGENT                           │
│  • Analyzes user request                                     │
│  • Creates step-by-step execution plan                       │
│  • Selects appropriate tools for each step                   │
│  • Outputs: JSON plan with steps and tool assignments        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      EXECUTOR AGENT                          │
│  • Iterates through plan steps                               │
│  • Calls appropriate tools/APIs                              │
│  • Implements retry logic for failures                       │
│  • Outputs: Results from each step execution                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      VERIFIER AGENT                          │
│  • Validates execution completeness                          │
│  • Checks for missing or incorrect data                      │
│  • Formats final response for user                           │
│  • Outputs: Structured, human-readable response              │
└─────────────────────────────────────────────────────────────┘
```

## Features

- **Multi-Agent System**: Planner, Executor, and Verifier agents working together
- **LLM-Powered Reasoning**: Uses Google Gemini for intelligent task planning and response formatting
- **Real API Integrations**:
  - **GitHub API**: Search repositories, get repo details, user information
  - **Weather API**: Current weather and 7-day forecast for any city (Open-Meteo)
- **Multiple Interfaces**: CLI, Interactive mode, and REST API
- **Error Handling**: Retry logic and graceful fallbacks

## Project Structure

```
ai_ops_assistant/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py      # Abstract base class for agents
│   ├── planner_agent.py   # Task planning and decomposition
│   ├── executor_agent.py  # Step execution with retry logic
│   └── verifier_agent.py  # Result validation and formatting
├── tools/
│   ├── __init__.py
│   ├── base_tool.py       # Abstract base class for tools
│   ├── github_tool.py     # GitHub API integration
│   └── weather_tool.py    # Weather API integration
├── llm/
│   ├── __init__.py
│   └── gemini_client.py   # Google Gemini LLM client
├── static/
│   └── index.html         # Web UI (modern, responsive)
├── main.py                # Entry point (CLI, API, UI)
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## Installation

1. **Clone/Navigate to the project**:
   ```bash
   cd ai_ops_assistant
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

## Usage

### Web UI Mode (Recommended for Demo)

```bash
python main.py --api --port 8000
```

Then open your browser and go to: **http://localhost:8000**

You'll see a beautiful web interface where you can:
- Enter natural language tasks
- Click example chips to try pre-built queries
- See real-time agent processing steps
- View formatted results with markdown rendering

### Interactive CLI Mode

```bash
python main.py
```

This starts an interactive terminal session where you can type natural language tasks.

### Single Task Mode

```bash
python main.py "Find the top 5 machine learning repositories on GitHub"
```

With verbose output:
```bash
python main.py -v "What's the weather in Tokyo?"
```

### REST API Mode

```bash
python main.py --api --port 8000
```

Then make requests:
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{"task": "Search for Python web frameworks on GitHub", "verbose": false}'
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/tools` | GET | List available tools |
| `/task` | POST | Submit a task for processing |

## Example Tasks

Here are some example tasks you can try:

1. **GitHub Operations**:
   - "Find the top 5 Python web frameworks on GitHub"
   - "Get information about the react repository owned by facebook"
   - "Search for repositories about machine learning with more than 50000 stars"
   - "Tell me about the GitHub user 'torvalds'"

2. **Weather Operations**:
   - "What's the current weather in New York?"
   - "Get the 7-day weather forecast for London"
   - "What's the weather like in Tokyo, Japan?"

3. **Combined Tasks**:
   - "Find popular weather API repositories on GitHub and tell me the weather in San Francisco"
   - "Search for climate change repositories and get the forecast for Miami"

## How It Works

### 1. Planner Agent
Takes the user's natural language input and uses the LLM to:
- Understand the task requirements
- Break down complex tasks into steps
- Select appropriate tools for each step
- Generate a JSON execution plan

### 2. Executor Agent
Takes the plan and:
- Iterates through each step
- Calls the specified tools with parameters
- Implements retry logic (3 attempts) for API failures
- Collects results from each step

### 3. Verifier Agent
Takes the execution results and:
- Analyzes completeness (success rate)
- Identifies any issues or failures
- Uses LLM to format a human-readable response
- Provides fallback formatting if LLM fails

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `GITHUB_TOKEN` | No | GitHub PAT for higher rate limits |

## API Integration Details

### GitHub API
- **Base URL**: `https://api.github.com`
- **Authentication**: Optional token for higher rate limits
- **Operations**: Search repos, get repo details, get user info

### Weather API (Open-Meteo)
- **Base URL**: `https://api.open-meteo.com`
- **Authentication**: None required (free API)
- **Operations**: Current weather, 7-day forecast
- Uses geocoding to convert city names to coordinates

## Error Handling

- **API Failures**: Automatic retry (up to 3 attempts)
- **Invalid Plans**: Validation before execution
- **Partial Success**: Continues execution even if some steps fail
- **LLM Failures**: Fallback formatting for responses

## Extending the System

### Adding New Tools

1. Create a new file in `tools/`:
```python
from tools.base_tool import BaseTool

class MyNewTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property
    def description(self) -> str:
        return "Description of what the tool does"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
    
    def execute(self, **kwargs) -> dict:
        # Implementation
        return {"success": True, "data": result, "error": None}
```

2. Register the tool in `main.py`:
```python
self.tools = [
    GitHubTool(),
    WeatherTool(),
    MyNewTool()  # Add here
]
```

## License

MIT License

## Author

Built as a demonstration of multi-agent AI architecture with LLM integration.
