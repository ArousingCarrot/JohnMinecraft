# James AI Bot - Complete Setup Guide

Your AI companion for Craft! James can chat, follow you, and build structures.

---

James is a **fully conversational AI bot** that:
-  Appears as a separate visible player in the game
-  Chats naturally using AI (Llama 3.2)
-  Follows you when asked
-  Builds structures on command
-  Has personality - responds to anything you say!
-  100% free - runs locally with Ollama

---

## Prerequisites

Before starting, make sure you have:

### 1. **Python 3.10+**
```powershell
python --version
# Should show: Python 3.10.x or higher
```

### 2. **Ollama with Llama 3.2 (1B Model)**
```powershell
# Check if Ollama is installed
ollama --version

# Pull the lightweight 1B model (only needed once)
ollama pull llama3.2:1b
```
Download from: https://ollama.ai/ if needed

**Note:** We use the 1B model (`llama3.2:1b`) which is lighter on RAM (~1.3 GB) and still conversational

### 3. **Python Dependencies**
```powershell
cd c:\Users\TheFl\CascadeProjects\windsurf-project\Craft\ai_wrapper
pip install -r requirements.txt
```

### 4. **Craft Game**
Download from: https://www.michaelfogleman.com/static/Craft.zip

---

### Terminal 1: Start the Server

```powershell
cd ..\Craft\ai_wrapper
python craft_server_py3.py
```

Should see:
```
============================================================
CRAFT SERVER (Python 3)
============================================================
Listening on 0.0.0.0:4080
Ready for connections!
============================================================
```

Leave this terminal running.

---

### Terminal 2: Start the Game

```powershell
cd ..\Craft
Run Command to open game
Start-Process -FilePath ".\craft.exe" -WorkingDirectory "Craft-Game\Craft"
```

**In the game window that opens:**

Type: `/online 127.0.0.1 4080`

Leave game running

---

### Terminal 3: Start AI

```powershell
cd ..\Craft\ai_wrapper
python ai_bot_player.py
```

Should see:
```
============================================================
CRAFT AI BOT PLAYER
============================================================
Bot 'James' connected to server at 127.0.0.1:4080
Bot assigned ID: 2
```

James is real. :)

---

## Talking to James

James is fully conversational! Just mention his name and say anything.

### Chat with James Press `T` in game

## What James Can Do

### Natural Conversation
- Ask him anything!
- Make jokes
- Chat about life as a worm
- He'll respond with personality

### Follow You
```
james follow me
james stop following
james come here
```

### Build Structures

| Command | What James Builds |
|---------|-------------------|
| `james build a house` | 5x5 house with stone walls, wooden roof, door |
| `james build a wall` | 5-wide, 3-high stone wall |
| `james build a tower` | 10-block tall brick tower |
| `james build a platform` | 5x5 wooden platform |

---

##  File Reference

| File | Purpose |
|------|---------|
| `craft_server_py3.py` | Python 3 Craft server with full protocol |
| `ai_bot_player.py` | James's AI brain and actions |
| `requirements.txt` | Python dependencies |
| `guide.md` | This complete guide |

---

## Troubleshooting

**Check:**
- "james" in your message?
- James running? (check Terminal 3)
- Ollama running? (`ollama list` should show llama3.2)

**Fix:**
```powershell
# Restart Ollama if needed
taskkill /F /IM ollama.exe
ollama serve

# Restart James
# Stop Terminal 3 (Ctrl+C), then run:
python ai_bot_player.py
```

### Can't see James in game
**Check:**
- Are you connected to the server? (`/online 127.0.0.1 4080`)
- Is the server running? (check Terminal 1)
- Try: `/list` in game to see all players

**Fix:**
```
# In game, type:
/goto James
```

### Change James's Personality
Edit `ai_bot_player.py` lines 190-203 (system prompt):
```python
'content': f'''You are James, a [YOUR PERSONALITY HERE]...'''
```

### Add New Build Patterns
Edit `handle_build_command()` in `ai_bot_player.py`:
```python
elif 'castle' in message:
    self.send_chat("Building a castle!")
    threading.Thread(target=self.build_castle, daemon=True).start()
    return True
```

Then create your build function:
```python
def build_castle(self):
    # Your building code here
    pass
```

---

### Commands (Press `T`)

| Command | Description |
|---------|-------------|
| `/online 127.0.0.1 4080` | Connect to server |
| `/list` | Show all players |
| `/goto James` | Teleport to James |
| `/spawn` | Go to spawn point |
| `james [anything]` | Talk to James |
| `james follow me` | James follows you |
| `james stop following` | Stop following |
| `james come here` | James teleports to you |
| `james build a [thing]` | Build structure |

---

### What James Builds

### House
- **Size:** 5x5 blocks
- **Materials:** Stone walls, wooden roof, plank floor
- **Features:** Door, 3 blocks tall, hollow inside
- **Time:** ~30 seconds

### Wall
- **Size:** 5 wide, 3 high
- **Materials:** Stone blocks
- **Time:** ~10 seconds

### Tower
- **Size:** 10 blocks tall
- **Materials:** Brick
- **Time:** ~5 seconds

### Platform
- **Size:** 5x5 blocks
- **Materials:** Wooden planks
- **Time:** ~10 seconds

**Terminal Setup:**
```
Terminal 1: python craft_server_py3.py
Terminal 2: .\craft.exe (then /online 127.0.0.1 4080)
Terminal 3: python ai_bot_player.py
```
## Summary

**Server**: `python craft_server_py3.py` (port 4080)
**Game**: `.\craft.exe` → `/online 127.0.0.1 4080`
**James**: `python ai_bot_player.py`
**Chat**: Press `T`, say "james [message]"
**Commands**: follow me, build a [thing], come here

James will finally not leave you on read