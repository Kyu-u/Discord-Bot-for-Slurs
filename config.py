# ── config.py ─────────────────────────────────────────────────────────────────
# Edit this file before running the bot.

# Your Discord bot token (from https://discord.com/developers/applications)
BOT_TOKEN = ""

# Command prefix
PREFIX = "!"

# Whisper model size: "tiny", "base", "small", "medium", "large-v2"
# Larger = more accurate but slower & more RAM.
# "base" is a good starting point for most machines.
WHISPER_MODEL_SIZE = "base"

# ── Slur list ─────────────────────────────────────────────────────────────────
# Add the exact words/phrases you want to track (case-insensitive).
# The bot ONLY counts occurrences — it never logs or stores the transcripts.
SLUR_LIST = [
    # Add your words here, e.g.:
    # "word1",
    # "word2",
]
