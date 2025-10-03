# Gmail MCP - AI-Powered Email Assistant

An intelligent Gmail client that uses **MCP (Model Context Protocol)** to interact with Gmail and **Gemini AI** to provide smart email management capabilities.

## 🌟 Features

- **🤖 AI-Powered Email Analysis** - Uses Gemini AI to analyze emails and determine appropriate actions
- **📧 Complete Gmail Integration** - Send, read, organize, and manage emails via Gmail API
- **🔧 MCP Protocol** - Modern client-server architecture using Model Context Protocol
- **📊 Full Transparency** - Complete logging of all AI interactions
- **🎯 Smart Actions** - Automatic replies, summaries, spam detection, and email organization
- **💬 Interactive Interface** - Command-line interface for easy email management

## 🏗️ Architecture

```
┌─────────────────┐    MCP Protocol    ┌─────────────────┐
│   talk2gmail.py │ ◄─────────────────► │  gmail/server.py │
│   (MCP Client)  │                    │  (MCP Server)   │
│                 │                    │                 │
│ • Gemini AI     │                    │ • Gmail API     │
│ • User Interface│                    │ • OAuth 2.0     │
│ • Command Parser│                    │ • Email Tools   │
└─────────────────┘                    └─────────────────┘
```

## 📦 Components

### 1. **Gmail MCP Server** (`gmail/server.py`)
- Provides Gmail API integration via MCP tools
- Handles OAuth 2.0 authentication
- Exposes email operations as MCP tools

### 2. **Gmail MCP Client** (`talk2gmail.py`)
- Connects to Gmail MCP server
- Uses Gemini AI for intelligent email analysis
- Provides interactive command interface

## 🛠️ Available Gmail Tools

The MCP server provides these email management tools:

| Tool | Description | Parameters |
|------|-------------|------------|
| `send-email` | Send emails | `recipient_id`, `subject`, `message` |
| `get-unread-emails` | Retrieve unread emails | None |
| `read-email` | Get full email content | `email_id` |
| `trash-email` | Move emails to trash | `email_id` |
| `mark-email-as-read` | Mark emails as read | `email_id` |
| `open-email` | Open email in browser | `email_id` |

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **uv** - Fast Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
3. **Google Cloud Project** with Gmail API enabled
4. **Gemini API Key**

### Installation

1. **Install uv (if not already installed):**
   ```bash
   # On macOS and Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # On Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Or with pip
   pip install uv
   ```

2. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd gmail_mcp
   ```

3. **Install dependencies with uv:**
   ```bash
   # Install all dependencies (recommended)
   uv sync
   
   # Or install with optional enhanced features
   uv sync --extra enhanced
   
   # Or install with development dependencies
   uv sync --extra dev
   ```

3. **Set up environment variables:**
   ```bash
   # Create .env file
   echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env
   ```

4. **Set up Gmail OAuth:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Download credentials as `client_creds.json`

### First Run

```bash
uv run python talk2gmail.py
```

On first run, you'll complete the OAuth flow:
1. Browser opens for Google authentication
2. Grant permissions to access Gmail
3. Token saved for future use

### Alternative uv Commands

```bash
# Run with uv (recommended)
uv run python talk2gmail.py

# Or activate virtual environment and run directly
uv shell
python talk2gmail.py
```

## 💻 Usage

### Example Queries

```bash
# Natural language queries
📧 Enter your Gmail request: get my unread emails
📧 Enter your Gmail request: read the latest email from john@example.com
📧 Enter your Gmail request: send a thank you email to sarah@company.com
```

## 🤖 AI-Powered Features

### Smart Email Analysis

The AI analyzes emails and determines actions:

- **REPLY** - Generates contextual responses
- **SUMMARIZE** - Creates concise summaries
- **URGENT** - Flags important emails
- **SPAM** - Detects and handles spam
- **ARCHIVE** - Organizes routine emails

### Example AI Analysis

```
📧 Processing email: abc123
📖 From: client@company.com
📝 Subject: Project Update Required
🤖 AI Action: REPLY
💭 AI Reasoning: Client requesting project status - should provide update
✅ Reply sent: "Thank you for your inquiry. I'll provide the project update by end of day."
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Gmail Credentials

1. **Google Cloud Console Setup:**
   - Create project
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Add authorized redirect URIs: `http://localhost:8080`

2. **Download credentials as `client_creds.json`**

### Required Scopes

The application requires these Gmail scopes:
- `https://www.googleapis.com/auth/gmail.modify`

## 📁 Project Structure

```
gmail_mcp/
├── gmail/
│   ├── __init__.py          # Package entry point
│   └── server.py            # Gmail MCP server
├── talk2gmail.py            # Gmail MCP client
├── client_creds.json        # Gmail OAuth credentials (you provide)
├── token.json              # OAuth tokens (auto-generated)
├── .env                    # Environment variables (you create)
├── pyproject.toml          # Project configuration and dependencies
├── requirements.txt        # Python dependencies (legacy)
├── uv.lock                 # Dependency lock file (auto-generated)
└── README.md              # This file
```

## 🔐 Security

- **OAuth 2.0** - Secure authentication with Google
- **Local Storage** - Tokens stored locally, never transmitted
- **Minimal Scopes** - Only requests necessary Gmail permissions
- **No Data Collection** - All processing happens locally

**Made with ❤️ using MCP (Model Context Protocol) and Gemini AI**