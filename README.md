# 🎙️ Discord Slur Tracker Bot

A Discord bot that joins your voice channel, transcribes speech locally using
[Whisper](https://github.com/openai/whisper), and counts how many times each
user says a slur. Great for moderation accountability.

**Transcripts are never stored** — only the slur counts are kept in memory.

---

## Setup

### 1. Install dependencies

```bash
pip install "py-cord[voice]" faster-whisper pynacl
```

> **Note:** `py-cord` is a maintained fork of `discord.py` with Voice Receive support.
> Do **not** mix it with `discord.py`.

### 2. Create a Discord Bot

1. Go to https://discord.com/developers/applications → **New Application**
2. **Bot** tab → **Add Bot** → copy the token
3. **OAuth2 → URL Generator** — enable scopes: `bot`
4. Enable permissions: `Connect`, `Speak`, `Use Voice Activity`, `Send Messages`, `Embed Links`, `Attach Files`
5. Invite the bot to your server using the generated URL

Under **Bot** settings, enable:
- ✅ Server Members Intent
- ✅ Message Content Intent

### 3. Configure

Edit `config.py`:

```python
BOT_TOKEN = "your-token-here"

SLUR_LIST = [
    "word1",
    "word2",
    # ...
]
```

### 4. Run

```bash
python bot.py
```

---

## Commands

| Command | Permission | Description |
|---------|------------|-------------|
| `!join` | Manage Server | Join your voice channel & start tracking |
| `!leave` | Manage Server | Stop recording & disconnect |
| `!stats` | Everyone | Show the slur leaderboard |
| `!reset` | Manage Server | Clear all counts for this server |
| `!export` | Manage Server | Download stats as a JSON file |

---

## How it works

1. `!join` — bot connects and starts a **WaveSink** recording session.
2. Every time `!leave` is called (or you call it mid-session), the bot:
   - Takes each user's audio buffer
   - Transcribes it with **faster-whisper** (fully local, no API calls)
   - Counts matches against your `SLUR_LIST`
   - Posts a summary embed in the text channel
3. `!stats` shows a ranked leaderboard at any time.

---

## Privacy notes

- Transcription runs **100% locally** via `faster-whisper` — no audio leaves your machine.
- Raw transcripts are **discarded immediately** after counting; only the integer count per user is stored in memory.
- Counts reset on bot restart unless you use `!export` to save them.

---

## Whisper model sizes

| Model | RAM | Speed | Accuracy |
|-------|-----|-------|----------|
| tiny | ~1 GB | Very fast | Basic |
| base | ~1 GB | Fast | Good |
| small | ~2 GB | Moderate | Better |
| medium | ~5 GB | Slow | Great |
| large-v2 | ~10 GB | Very slow | Best |

Set `WHISPER_MODEL_SIZE` in `config.py`.
