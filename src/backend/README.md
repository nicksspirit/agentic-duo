# Backend

## 🚀 Getting Started

1. **Set up environment variables:**
   - Create a `.env` file in this directory (`src/backend/`)
   - Add your Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

2. **Install dependencies:**
   ```bash
   cd src/backend
   uv sync
   ```

## 🎤 Interactive Slide Deck Client (New!)

This is the main client that allows you to control the slide deck simulation with your voice, using the modular backend architecture.

### Usage

Run the client:
```bash
cd src/backend
SHOW_THINKING_LOGS=1 uv run python slide_deck_client.py
```

### Voice Commands

Once you see "Listening for commands...", try saying:

- **Navigation**:
  - "Go to the **next slide**"
  - "Go back to the **previous slide**"
  - "Jump to **slide 5**"
  
- **Content**:
  - "Add a bullet point about **AI is awesome**"
  - "Add a note saying **remember to mention scalability**"

- **Context & Summary**:
  - "**Summarize** the presentation so far"
  - "What is the **current status**?" (Uses `get_presentation_context`)
  - "What slide am I on?"

### Logs

- **Thinking Logs**: With `SHOW_THINKING_LOGS=1`, you'll see the AI's decision process in the console.
- **Execution Log**: Detailed logs are written to `execution.log`.

---

## 🎤 Intent Detection Client (Legacy)

The project also includes a simpler speech-to-action client for basic testing.

### Usage

Run the intent client:

```bash
cd src/backend
uv run python intent_client.py
```

The client recognizes basic commands like "**print hello**", "**say goodbye**", etc.

### Configuration

#### Thinking Logs

By default, thinking logs (model reasoning) are disabled. Enable them for development:

**Via environment variable:**
```bash
SHOW_THINKING_LOGS=1 uv run python intent_client.py
```

**Or modify the code:**
```python
# In intent_client.py, change:
SHOW_THINKING_LOGS = True  # Default is False
```

### Execution Log

All function executions are logged to `execution.log` in the backend directory with timestamps:

```
[2025-01-XX XX:XX:XX] [INTENT DETECTED] Function: print_hello
[2025-01-XX XX:XX:XX] [FUNCTION CALLED] print_hello() - Hello!
```

### How It Works

1. **Audio Capture**: Captures 16kHz PCM audio from microphone via `AudioProcessor`.
2. **Streaming**: Streams audio chunks to Gemini Live API in real-time.
3. **Intent Detection**: Gemini analyzes speech and detects when commands match function descriptions.
4. **Function Execution**: Detected intents trigger valid Python functions via `ToolExecutor`.
5. **Logging**: All executions are logged to `execution.log`.
