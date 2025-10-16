# Agent-007-Internal

An intelligent AI agent that automatically selects and sequences tools to answer domain-specific questions, providing structured tool chains for work management and analysis.



## 🚀 Features

- **Intelligent Tool Selection**: Automatically identifies and sequences the appropriate tools for your queries
- **Two-Step Processing**: Generates tool chain skeletons and fills arguments with context-aware reasoning
- **Minified JSON Tool Chains**: Structured, downloadable tool chains for integration and analysis
- **Work Management Tools**: Built-in tools for issues, tickets, sprints, and task management
- **Multiple LLM Support**: Configurable support for Groq, Google Gemini, and Mistral models
- **Modern Web Interface**: React-based frontend with responsive design

## 🛠️ Tech Stack

### Backend
- **Python 3.10.x**
- **Flask** - REST API framework
- **LangChain** - LLM integration and prompt management
- **Flask-CORS** - Cross-origin resource sharing

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **Sonner** - Toast notifications

### AI/ML
- **LangChain** - LLM orchestration
- **Groq** - Primary LLM provider (GPT-OSS models)
- **Google Generative AI** - Alternative LLM provider
- **Mistral AI** - Additional LLM provider

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js 18+**
- **npm or pnpm**

### API Keys Required
- **GROQ_API_KEY** - For Groq LLM services
- **Optional:**
    - **GOOGLE_API_KEY** - For Google Gemini 
    - **MISTRAL_API_KEY** - For Mistral AI 

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Agent-007-Internal
   ```

2. **Backend Setup**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd Frontend

   # Install dependencies (using pnpm)
   pnpm install

   # Or using npm
   npm install
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional (for alternative models)
GOOGLE_API_KEY=your_google_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
```

### Model Configuration

Edit `src/loadModel.py` to configure your preferred models:

```python
# Current configuration uses GPT-OSS-120B for both small and heavy models
small_model = "gpt-oss-120b"
large_model = "gpt-oss-120b"
```

Available options:
- `"gpt-oss-120b"` - Groq's GPT-OSS 120B model
- `"gpt-oss-20b"` - Groq's GPT-OSS 20B model
- `"llama-3.1-8b-instant"` - Llama 3.1 8B
- `"llama-3.3-70b-versatile"` - Llama 3.3 70B
- `"gemini"` - Google Gemini 2.5 Pro
- `"mistral-large-latest"` - Mistral Large

## 🚀 Running the Application

### Backend Server

Start the Flask API server:

```bash
python3 -m src.api.main
```

The server will run on `http://localhost:5000`

**Note**: Do NOT run `python3 src/api/main.py` directly. Use the module syntax as shown above.

### Frontend Development Server

In a separate terminal:

```bash
cd Frontend
pnpm dev
# or
npm run dev
```

The frontend will be available at `http://localhost:5173`



## 📖 Usage

### Web Interface

1. Open `http://localhost:5173` in your browser
2. Click "Start Conversation" on the landing page
3. Enter your query in the chat interface
4. View the generated tool chain in the right panel
5. Download or copy the JSON tool chain as needed

### CLI Usage

You can also use the backend directly as an interactive shell:

```bash
# Run the interactive CLI
python src/main.py
```

### Sample Queries

Try these example queries:

- "Summarize work items similar to don:core:dvrv-us-1:devo/0:issue/1"
- "Prioritize my P0 issues and add them to the current sprint"
- "Summarize high severity tickets from the customer UltimateCustomer"
- "What are my all issues in the triage stage under part FEAT-123?"
- "List all high severity tickets coming in from slack from customer Cust123 and generate a summary of them."
- "Given a customer meeting transcript T, create action items and add them to my current sprint"



## 🔄 How It Works

The agent follows a three-step process:

<img src="./architecture_diagram/image.png"></img>

### Step 1: Tool Chain Generation
- Analyzes the user query
- Identifies relevant tools from the available tool set
- Creates a skeleton JSON array with tool names and argument names
- Arguments are left empty (`""`) at this stage

### Step 2: Argument Filling
- Takes the skeleton plan and user query
- Uses context-aware reasoning to fill in appropriate argument values
- Supports dependencies between tools (using `$$PREV[index]` notation)
- Outputs a complete, executable tool chain

### Step 3: Hallucination Check
- Checks if the json is correctly made and fullfills the given query
- Returns the query to the user if the llm says the json is correct otherwise the json gets redirected to step 1 along with the context

## 🛠️ Available Tools

The system includes the following built-in tools:

- **works_list** - Filter and retrieve work items (issues, tickets, tasks)
- **summarize_objects** - Summarize lists of objects
- **prioritize_objects** - Sort objects by priority
- **add_work_items_to_sprint** - Add work items to sprints
- **get_sprint_id** - Get current sprint ID
- **get_similar_work_items** - Find similar work items
- **search_object_by_name** - Search for objects by name
- **create_actionable_tasks_from_text** - Extract tasks from text
- **who_am_i** - Get current user ID


## 🤝 Adding New Tools

1. Define your tool in `src/tool_list/usable_tool.py`
2. Include name, description, and arguments with types
3. Test the tool integration
4. Update documentation at 

## 👨‍💻 Development Team

Developed with ❤️ by:
- 🚀 [Rishi Chauhan](https://github.com/AquaRegia2179)
- 🔮 [Daksh Singhal](https://github.com/Leviethal)
- 🎯 [Soham Kakkar](https://github.com/soham-kakkar)
- 🎨 [Dashpreet Singh](https://github.com/dzdasherktb)
- 🚀 [Hemant Nagar](https://github.com/LASTHALFBLOODPRINCE)
- 🔮 [Anurag Mahipal](https://github.com/Anuragmahipal)
- 🎯 [Priyansh Singh](https://github.com/priyanshsingh-dev)
- 🎨 [Abhay Mishra](https://github.com/AquaRegia2179)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
