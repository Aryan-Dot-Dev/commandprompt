#!/usr/bin/env python3
import signal
import os
import sys
import subprocess

def exit_handler(sig, frame):
    print()
    raise InterruptedError()

signal.signal(signal.SIGINT, exit_handler)

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")

def load_env():
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value

def save_api_key(provider: str, api_key: str):
    # Ensure directory exists
    env_dir = os.path.dirname(env_path)
    if env_dir and not os.path.exists(env_dir):
        os.makedirs(env_dir, exist_ok=True)
    
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
    
    env_dict = {}
    for line in lines:
        line = line.strip()
        if line and "=" in line:
            key, value = line.split("=", 1)
            env_dict[key] = value
    
    env_dict["LLM_PROVIDER"] = provider
    
    provider_key_map = {
        "gemini": "GEMINI_API_KEY",
        "nvidia": "NVIDIA_NIM_API_KEY"
    }
    
    key_name = provider_key_map.get(provider.lower())
    if key_name:
        env_dict[key_name] = api_key
    
    with open(env_path, "w") as f:
        for key, value in env_dict.items():
            f.write(f"{key}={value}\n")

def setup_api_key():
    try:
        import questionary
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "questionary", "-q"], check=False)
        import questionary
    
    provider = questionary.select(
        "Select LLM Provider:",
        choices=["gemini", "nvidia", "exit"],
        instruction="(Use arrow keys, press Enter to select)"
    ).ask()
    
    if not provider or provider == "exit":
        print("Skipped LLM provider setup. Using default (nvidia).\n")
        if not os.getenv("NVIDIA_NIM_API_KEY") and not os.getenv("GEMINI_API_KEY"):
            os.environ["LLM_PROVIDER"] = "nvidia"
        return
    
    provider_urls = {
        "gemini": "https://aistudio.google.com/apikey",
        "nvidia": "https://build.nvidia.com/"
    }

    provider_prompts = {
        "gemini": "Gemini API key",
        "nvidia": "Nvidia NIM API key"
    }
    
    url = provider_urls[provider]
    prompt_text = provider_prompts[provider]
    
    print(f"\nGet your key at: {url}\n")
    api_key = questionary.text(f"Enter {prompt_text}:").ask()
    
    if not api_key:
        print("No input provided.")
        return
    
    save_api_key(provider, api_key)
    os.environ["LLM_PROVIDER"] = provider
    os.environ[provider.upper() + "_API_KEY"] = api_key
    print(f"✓ {provider} configured!\n")

def show_help():
    print("\033[36m!api\033[0m       - Change API key")
    print("\033[36m!uninstall\033[0m - Remove nlsh")
    print("\033[36m!help\033[0m      - Show this help")
    print("\033[36m!cmd\033[0m       - Run cmd directly")
    print()

load_env()

first_run = not os.getenv("LLM_PROVIDER")
if first_run:
    setup_api_key()
    print("\033[1mnlsh\033[0m - talk to your terminal\n")
    show_help()

import requests

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "nvidia").lower()

command_history = []
MAX_HISTORY = 10
MAX_CONTEXT_CHARS = 4000

def get_context_size() -> int:
    return sum(len(e["command"]) + len(e["output"]) for e in command_history)

def add_to_history(command: str, output: str = ""):
    command_history.append({
        "command": command,
        "output": output[:500] if output else ""
    })
    while len(command_history) > MAX_HISTORY:
        command_history.pop(0)
    while get_context_size() > MAX_CONTEXT_CHARS and len(command_history) > 1:
        command_history.pop(0)

def format_history() -> str:
    if not command_history:
        return "No previous commands."
    
    lines = []
    for i, entry in enumerate(command_history[-5:], 1):
        lines.append(f"{i}. $ {entry['command']}")
        if entry['output']:
            output_lines = entry['output'].strip().split('\n')[:2]
            for line in output_lines:
                lines.append(f"   {line}")
    return "\n".join(lines)

def get_shell_type() -> str:
    """Detect the parent shell process."""
    if sys.platform == "win32":
        # Method 1: Check environment variable PROMPT (CMD sets it to $P$G)
        prompt_var = os.getenv("PROMPT", "")
        if prompt_var == "$P$G":
            return "cmd"
        
        # Method 2: Check parent process using psutil (more reliable)
        try:
            import psutil
            parent = psutil.Process(os.getpid()).parent()
            parent_name = parent.name().lower()
            if "powershell" in parent_name or "pwsh" in parent_name:
                return "powershell"
            elif "cmd" in parent_name:
                return "cmd"
        except:
            pass
        
        # Method 3: Use wmic to get parent process (Windows built-in)
        try:
            result = subprocess.run(
                ['wmic', 'process', 'where', f'processid={os.getpid()}', 'get', 'parentprocessid'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                parent_pid = int(result.stdout.split()[-1])
                parent_result = subprocess.run(
                    ['wmic', 'process', 'where', f'processid={parent_pid}', 'get', 'name'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if parent_result.returncode == 0:
                    parent_name = parent_result.stdout.lower()
                    if "powershell" in parent_name or "pwsh" in parent_name:
                        return "powershell"
                    elif "cmd" in parent_name:
                        return "cmd"
        except:
            pass
        
        # Fallback: Default to PowerShell (more common on modern Windows)
        return "powershell"
    else:
        return "zsh"

def call_llm(prompt: str) -> str:
    """Call the configured LLM provider."""
    provider = os.getenv("LLM_PROVIDER", "nvidia").lower()
    
    if provider == "gemini":
        try:
            from google import genai
        except ImportError:
            print("\n\033[33mInstalling google-generativeai...\033[0m")
            subprocess.run([sys.executable, "-m", "pip", "install", "google-genai", "-q"], check=False)
            try:
                from google import genai
            except ImportError:
                print("\033[31mFailed to install google-generativeai. Falling back to Nvidia NIM.\033[0m")
                provider = "nvidia"
        
        if provider == "gemini":
            try:
                client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                # Try primary model first
                try:
                    response = client.models.generate_content(
                        model="gemini-3-flash-preview",
                        contents=prompt
                    )
                    if not response or not response.text:
                        raise Exception("Empty response")
                    return response.text.strip()
                except Exception as primary_error:
                    # Fallback to gemini-2.5-flash
                    try:
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=prompt
                        )
                        if not response or not response.text:
                            raise Exception("Empty response")
                        return response.text.strip()
                    except Exception as fallback_error:
                        raise Exception(f"Primary: {str(primary_error)}, Fallback: {str(fallback_error)}")
            except Exception as e:
                raise Exception(f"Gemini error: {str(e)}")
    
    # Nvidia (default or fallback)
    headers = {
        "Authorization": f"Bearer {os.getenv('NVIDIA_NIM_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    # Try primary model first
    primary_model = "nvidia/nemotron-3-super-120b-a12b"
    fallback_model = "moonshotai/kimi-k2.5"
    
    for model in [primary_model, fallback_model]:
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "top_p": 0.5,
            "max_tokens": 50
        }
        try:
            response = requests.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                json=data,
                headers=headers,
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                if result and 'choices' in result and result['choices']:
                    content = result['choices'][0].get('message', {}).get('content')
                    if content:
                        return content.strip()
        except:
            pass
    
    # If both failed, raise error with details
    raise Exception(f"Nvidia NIM error: Both {primary_model} and {fallback_model} failed")

def get_command(user_input: str, cwd: str, shell_type: str, history_context: str) -> str:
    if shell_type == "cmd":
        shell_desc = "Windows CMD"
        syntax_guide = """WINDOWS CMD - REQUIRED SYNTAX:
dir              → list files
dir /s /b *.txt  → find files recursively
mkdir folder     → create directory
del filename     → delete file
copy src dest    → copy file
cd folder        → change directory
findstr /r "pattern" file → search text"""
        
        warning = "IMPORTANT: You are in Windows CMD. CMD does NOT have: head, tail, grep, sed, awk, pipes with filters. CMD is limited - use simple commands only."
    
    elif shell_type == "powershell":
        shell_desc = "PowerShell"
        syntax_guide = """POWERSHELL - REQUIRED SYNTAX:
Get-ChildItem                          → list files
Get-ChildItem -Recurse | ...          → complex operations
Get-ChildItem -Recurse -File | Sort-Object Length -Descending | Select-Object -First 3  → find 3 largest
New-Item -ItemType Directory -Name X  → create directory
Remove-Item filename                   → delete file
Copy-Item src dest                     → copy file
Set-Location folder                    → change directory
Select-String "pattern" file           → search text
Where-Object {...}                     → filter objects
Select-Object -First N                 → limit results"""
        
        warning = "IMPORTANT: You are in PowerShell. Use PowerShell cmdlets and syntax ONLY. Never use Unix commands (head, tail, grep, find, etc) or old CMD syntax (dir, copy)."
    
    else:
        shell_desc = "zsh"
        syntax_guide = """ZSH - REQUIRED SYNTAX:
ls                     → list files
find . -type f -name *.txt → find files
mkdir folder           → create directory
rm filename            → delete file
cp src dest            → copy file
cd folder              → change directory
grep "pattern" file    → search text
head -n 3 file         → first 3 lines
find . | sort -k5 -rn | head -3 → 3 largest files"""
        
        warning = "IMPORTANT: You are in zsh. Use Unix/Linux commands ONLY."
    
    prompt = f"""DETECTED SHELL: {shell_type.upper()}

{shell_desc} COMMAND SYNTAX:
{syntax_guide}

{warning}

STRICT OUTPUT FORMAT:
- OUTPUT: Exactly one command line only
- NO: Explanations, comments, markdown, or extra text
- NO: Line breaks or multiple commands
- MUST: Use ONLY the syntax shown above

Current directory: {cwd}
History: {history_context}

USER REQUEST: {user_input}

RESPOND WITH ONLY THE COMMAND:"""

    return call_llm(prompt)


def run_command(command: str, shell_type: str) -> tuple:
    """Run command with the appropriate shell."""
    if sys.platform == "win32" and shell_type == "powershell":
        # Run PowerShell commands explicitly with powershell.exe
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=30
        )
    else:
        # Use default shell (CMD on Windows, sh on Unix)
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
    
    return result.stdout, result.stderr

def is_natural_language(text: str) -> bool:
    if text.startswith("!"):
        return False
    shell_commands = ["ls", "pwd", "clear", "exit", "quit", "whoami", "date", "cal", 
                      "top", "htop", "history", "which", "man", "touch", "head", "tail",
                      "grep", "find", "sort", "wc", "diff", "tar", "zip", "unzip"]
    shell_starters = ["cd ", "ls ", "echo ", "cat ", "mkdir ", "rm ", "cp ", "mv ", 
                      "git ", "npm ", "node ", "npx ", "python", "pip ", "brew ", "curl ", 
                      "wget ", "chmod ", "chown ", "sudo ", "vi ", "vim ", "nano ", "code ", 
                      "open ", "export ", "source ", "docker ", "kubectl ", "aws ", "gcloud ",
                      "./", "/", "~", "$", ">", ">>", "|", "&&"]
    if text in shell_commands:
        return False
    return not any(text.startswith(s) for s in shell_starters)

def main():
    while True:
        try:
            cwd = os.getcwd()
            prompt = f"\033[32m{os.path.basename(cwd)}\033[0m > "
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
            
            if user_input.startswith("cd "):
                path = os.path.expanduser(user_input[3:].strip())
                try:
                    os.chdir(path)
                except Exception as e:
                    print(f"cd: {e}")
                continue
            elif user_input == "cd":
                os.chdir(os.path.expanduser("~"))
                continue
            
            if user_input == "!api":
                setup_api_key()
                global LLM_PROVIDER
                LLM_PROVIDER = os.getenv("LLM_PROVIDER", "nvidia").lower()
                continue
            
            if user_input == "!uninstall":
                confirm = input("\033[33mRemove nlsh? [y/N]\033[0m ")
                if confirm.lower() == "y":
                    import shutil
                    install_dir = os.path.expanduser("~/.nlsh")
                    bin_path = os.path.expanduser("~/.local/bin/nlsh")
                    if os.path.exists(install_dir):
                        shutil.rmtree(install_dir)
                    if os.path.exists(bin_path):
                        os.remove(bin_path)
                    print("\033[32m✓ nlsh uninstalled\033[0m")
                    sys.exit(0)
                continue
            
            if user_input == "!help":
                show_help()
                continue
            
            if user_input.startswith("!"):
                cmd = user_input[1:]
                if not cmd:
                    continue
                shell_type = get_shell_type()
                stdout, stderr = run_command(cmd, shell_type)
                print(stdout, end="")
                if stderr:
                    print(stderr, end="")
                add_to_history(cmd, stdout + stderr)
                continue
            
            if not is_natural_language(user_input):
                shell_type = get_shell_type()
                stdout, stderr = run_command(user_input, shell_type)
                print(stdout, end="")
                if stderr:
                    print(stderr, end="")
                add_to_history(user_input, stdout + stderr)
                continue
                        
            shell_type = get_shell_type()
            history_context = format_history()
            command = get_command(user_input, cwd, shell_type, history_context)
            confirm = input(f"\033[33m→ {command}\033[0m [Press Enter] ")
            
            if confirm == "":
                if command.startswith("cd "):
                    path = os.path.expanduser(command[3:].strip())
                    try:
                        os.chdir(path)
                    except Exception as e:
                        print(f"cd: {e}")
                else:
                    detected_shell = get_shell_type()
                    stdout, stderr = run_command(command, detected_shell)
                    print(stdout, end="")
                    if stderr:
                        print(stderr, end="")
                    add_to_history(command, stdout + stderr)
            
        except (EOFError, InterruptedError, KeyboardInterrupt):
            continue
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                print("\033[31mrate limit hit - wait a moment and try again\033[0m")
            elif "InterruptedError" not in err and "KeyboardInterrupt" not in err:
                print(f"\033[31merror: {err[:100]}\033[0m")

if __name__ == "__main__":
    main()