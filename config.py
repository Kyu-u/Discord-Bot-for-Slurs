# Edit this file before running the bot.

# Your Discord bot token (from https://discord.com/developers/applications)
BOT_TOKEN = ""

# Command prefix
PREFIX = "!"

# Whisper model size: "tiny", "base", "small", "medium", "large-v2"
# Larger = more accurate but slower & more RAM.
# "base" is a good starting point for most machines.
WHISPER_MODEL_SIZE = "base"

# Takes list of slurs in slurs.txt
with open("slurs.txt", "r", encoding="utf-8") as f:
    SLUR_LIST = [line.strip() for line in f if line.strip()]
