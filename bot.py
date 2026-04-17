"""
Discord Slur Tracker Bot
========================
Joins a voice channel, transcribes speech using Whisper,
and counts how many times each user says a slur.

Requirements:
    pip install "py-cord[voice]" faster-whisper pynacl

Usage:
    1. Add your bot token and slur list to config.py
    2. Run: python bot.py
    3. In Discord: !join, !leave, !stats, !reset
"""

import discord
from discord.ext import commands
from discord.sinks import WaveSink
import asyncio
import io
import os
import json
import datetime
from collections import defaultdict
from faster_whisper import WhisperModel
import config

# ── Whisper model (runs locally, no API key needed) ──────────────────────────
# Change "base" to "small", "medium", or "large-v2" for better accuracy
print("Loading Whisper model... (first run may download weights)")
whisper_model = WhisperModel(config.WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
print("Model ready.")

# ── Bot setup ─────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

bot = commands.Bot(command_prefix=config.PREFIX, intents=intents)

# ── State ─────────────────────────────────────────────────────────────────────
# guild_id -> { user_id -> count }
slur_counts: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))
# guild_id -> { user_id -> name }
user_names: dict[int, dict[int, str]] = defaultdict(dict)
# guild_id -> session start time
session_start: dict[int, datetime.datetime] = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def count_slurs(text: str) -> int:
    """Count how many slurs appear in a transcribed string."""
    text_lower = text.lower()
    total = 0
    for slur in config.SLUR_LIST:
        total += text_lower.count(slur.lower())
    return total


def transcribe_audio(pcm_bytes: bytes) -> str:
    """Run Whisper on raw WAV bytes and return the transcript."""
    import tempfile, wave, struct

    # Write to a temp WAV file (Whisper needs a file path or numpy array)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(2)        # Discord sends stereo
            wf.setsampwidth(2)        # 16-bit
            wf.setframerate(48000)    # 48 kHz
            wf.writeframes(pcm_bytes)

    segments, _ = whisper_model.transcribe(tmp_path, beam_size=5)
    transcript = " ".join(seg.text for seg in segments)
    os.unlink(tmp_path)
    return transcript.strip()


# ── Recording callback ────────────────────────────────────────────────────────

async def finished_callback(sink: WaveSink, channel: discord.TextChannel, *args):
    """Called when recording stops. Transcribe each user's audio."""
    guild = channel.guild
    results = []

    for user_id, audio in sink.audio_data.items():
        member = guild.get_member(user_id)
        name = member.display_name if member else f"User {user_id}"
        user_names[guild.id][user_id] = name

        pcm_bytes = audio.file.read()
        if len(pcm_bytes) < 4800:   # skip < 0.05 s of audio
            continue

        transcript = await asyncio.to_thread(transcribe_audio, pcm_bytes)
        if not transcript:
            continue

        n = count_slurs(transcript)
        if n:
            slur_counts[guild.id][user_id] += n
            results.append(f"**{name}**: {n} slur(s) detected  *(transcript hidden)*")

    if results:
        embed = discord.Embed(
            title="🔴 Slurs detected this segment",
            description="\n".join(results),
            color=discord.Color.red(),
        )
        await channel.send(embed=embed)


# ── Commands ──────────────────────────────────────────────────────────────────

@bot.command(name="join")
@commands.has_permissions(manage_guild=True)
async def join(ctx: commands.Context):
    """Join the caller's voice channel and start tracking."""
    if not ctx.author.voice:
        return await ctx.send("❌ You must be in a voice channel first.")

    vc = ctx.author.voice.channel
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.disconnect()

    voice_client = await vc.connect()
    session_start[ctx.guild.id] = datetime.datetime.utcnow()

    voice_client.start_recording(
        WaveSink(),
        finished_callback,
        ctx.channel,         # text channel to report in
    )

    await ctx.send(
        f"🎙️ Joined **{vc.name}** — tracking started.\n"
        f"Use `{config.PREFIX}leave` to stop and see final stats."
    )


@bot.command(name="leave")
@commands.has_permissions(manage_guild=True)
async def leave(ctx: commands.Context):
    """Stop recording and disconnect."""
    vc = ctx.guild.voice_client
    if not vc:
        return await ctx.send("❌ I'm not in a voice channel.")

    vc.stop_recording()          # triggers finished_callback
    await asyncio.sleep(2)       # give callback time to finish
    await vc.disconnect()
    await ctx.send("🛑 Stopped tracking. Use `!stats` to see the full leaderboard.")


@bot.command(name="stats")
async def stats(ctx: commands.Context):
    """Show the slur leaderboard for this server."""
    counts = slur_counts.get(ctx.guild.id)
    if not counts:
        return await ctx.send("📊 No data yet — start a session with `!join`.")

    sorted_users = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, count) in enumerate(sorted_users):
        name = user_names[ctx.guild.id].get(uid, f"User {uid}")
        medal = medals[i] if i < 3 else f"{i+1}."
        lines.append(f"{medal} **{name}** — {count} slur(s)")

    start = session_start.get(ctx.guild.id)
    footer = f"Session started {start.strftime('%Y-%m-%d %H:%M UTC')}" if start else ""

    embed = discord.Embed(
        title="📊 Slur Leaderboard",
        description="\n".join(lines),
        color=discord.Color.orange(),
    )
    if footer:
        embed.set_footer(text=footer)
    await ctx.send(embed=embed)


@bot.command(name="reset")
@commands.has_permissions(manage_guild=True)
async def reset(ctx: commands.Context):
    """Reset the leaderboard for this server."""
    slur_counts.pop(ctx.guild.id, None)
    user_names.pop(ctx.guild.id, None)
    session_start.pop(ctx.guild.id, None)
    await ctx.send("✅ Leaderboard reset.")


@bot.command(name="export")
@commands.has_permissions(manage_guild=True)
async def export(ctx: commands.Context):
    """Export stats as a JSON file."""
    counts = slur_counts.get(ctx.guild.id, {})
    names  = user_names.get(ctx.guild.id, {})
    data = [
        {"user_id": uid, "name": names.get(uid, str(uid)), "count": cnt}
        for uid, cnt in sorted(counts.items(), key=lambda x: -x[1])
    ]
    buf = io.BytesIO(json.dumps(data, indent=2).encode())
    buf.seek(0)
    await ctx.send(
        "📁 Here are your stats:",
        file=discord.File(buf, filename="slur_stats.json"),
    )


# ── Error handling ────────────────────────────────────────────────────────────

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need **Manage Server** permission to use that command.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"⚠️ Error: {error}")


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")
    print(f"   Prefix: {config.PREFIX}")
    print(f"   Whisper model: {config.WHISPER_MODEL_SIZE}")
    print(f"   Tracking {len(config.SLUR_LIST)} term(s)")


# ── Run ───────────────────────────────────────────────────────────────────────
bot.run(config.BOT_TOKEN)
