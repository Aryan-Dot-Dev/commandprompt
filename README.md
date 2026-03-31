# CommandPrompt - Natural Language Shell (originally from [Junaid Mahmood](https://github.com/junaid-mahmood/))

**Talk to your terminal in plain English.** Let AI understand your intent and generate the right commands for your shell.

> **Supported**: Windows (PowerShell, CMD), macOS (zsh, bash), Linux (bash, zsh)

---

## Features

✨ **Multi-Shell Support** - Automatically detects your shell (PowerShell, CMD, zsh, bash) and generates syntax-correct commands

🤖 **Dual LLM Support** - Choose between Gemini and Nvidia NIM APIs with automatic fallback models

💾 **Smart History** - Maintains command history for context-aware suggestions

🪟 **Cross-Platform** - Works seamlessly on Windows, macOS, and Linux

⚡ **Fast & Lightweight** - Python-based with minimal dependencies

🔄 **Fallback Strategy** - Automatically tries alternative models if primary fails

---

## Install

### Windows (PowerShell)

```powershell
# Clone the repository
git clone https://github.com/Aryan-Dot-Dev/commandprompt.git
cd commandprompt

# Run installer
.\install.ps1
```

### macOS / Linux (Bash)

```bash
# Clone the repository
git clone https://github.com/Aryan-Dot-Dev/commandprompt.git
cd nlsh

# Run installer
bash install.sh
```

---

## Uninstall

### Windows

```powershell
.\uninstall.ps1
```

### macOS / Linux

```bash
bash uninstall.sh
```

---

## Usage

Start the interactive shell:

```bash
nlsh
```

Type naturally in English:

```
> list all python files
→ find . -name "*.py"

> git commit with message fixed bug  
→ git commit -m "fixed bug"

> show the 5 largest files
→ du -sh * | sort -rh | head -5

> find json files modified today
→ find . -name "*.json" -mtime -1
```

Press `Enter` to confirm and execute the suggested command.

---

## Commands

| Command | Description |
|---------|-------------|
| `!api` | Change or configure API key (Gemini or Nvidia NIM) |
| `!help` | Show available commands |
| `!uninstall` | Remove CommandPrompt from your system |
| `!cmd <command>` | Run any command directly without AI |
| `Ctrl+D` or `Ctrl+C` | Exit CommandPrompt |

---

## Configuration

### API Keys

On first run, you'll be prompted to choose an LLM provider:

- **Gemini** - Get key at https://aistudio.google.com/apikey
- **Nvidia NIM** - Get key at https://build.nvidia.com/

Configuration is saved in:
- **Windows**: `%USERPROFILE%\.nlsh\.env`
- **macOS/Linux**: `~/.nlsh/.env`

### Change API Key

```
> !api
```

Select a provider and enter your API key. It will be saved for future sessions.

---

## Supported Models

### Primary Models
- **Gemini**: `gemini-3-flash-preview`
- **Nvidia NIM**: `meta/llama-3.1-70b-instruct`

### Fallback Models
- **Gemini**: `gemini-2.5-flash` (if primary fails)
- **Nvidia NIM**: `moonshotai/kimi-k2.5` (if primary fails)

The system automatically tries the primary model first and falls back to the alternative if needed.

---

## Shell-Specific Syntax

### PowerShell
```
Get-ChildItem -Recurse -File
Where-Object { $_.Length -gt 10MB }
```

### Command Prompt
```
dir /s /b
findstr /r "pattern" file.txt
```

### Bash/Zsh
```
find . -type f -name "*.txt"
grep "pattern" file.txt
```

CommandPrompt detects your shell and generates the appropriate syntax automatically.

---

## Requirements

- **Python 3.7+**
- **Git** (for installation)
- **API Key** (Gemini or Nvidia NIM)

---

## Troubleshooting

### "Python 3 is required"
Install Python from [python.org](https://www.python.org/downloads/)

### API Key Not Working
- Verify your API key is valid and not expired
- Try `!api` to update your key
- Check that your API key has proper permissions

### Shell Not Detected
CommandPrompt will default to your system's default shell. You can manually set the `LLM_PROVIDER` in the `.env` file.

### Rate Limiting
If you hit rate limits, wait a moment and try again. CommandPrompt will automatically retry with fallback models.

---

## How It Works

1. **You type** a natural language command
2. **CommandPrompt detects** your current shell (PowerShell, bash, zsh, etc.)
3. **AI generates** a command using the correct shell syntax
4. **You confirm** with Enter to execute
5. **History is saved** for context in future suggestions

---

## Privacy

Your API key is stored locally on your machine in `~/.nlsh/.env`. Commands and outputs are only sent to your configured LLM provider.

---

## License

MIT License - See LICENSE file for details

---

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

---

## Credits

Created by [Aryan-Dot-Dev](https://github.com/Aryan-Dot-Dev)
