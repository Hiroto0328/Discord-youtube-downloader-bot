import discord
from discord import app_commands
from discord.ext import commands
import dropbox
import os
import asyncio
import subprocess
import time

DROPBOX_ACCESS_TOKEN = "Dropboxトークン"
dropbox_client = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="youtube_dl", description="指定したYoutubeの動画をダウンロードできます")
async def upload(interaction: discord.Interaction, url: str):
    await interaction.response.send_message("<a:loading:1329263542565732475>動画をダウンロードしています...", ephemeral=True)

   
    timestamp = int(time.time())
    output_path = f"downloaded_video_{timestamp}.mp4"

    try:
        command = [
            "yt-dlp",
            url,
            "-o", output_path,
            "-f", "best[ext=mp4]"
        ]
        start_time = time.time()
        subprocess.run(command, check=True)

      
        with open(output_path, "rb") as file:
            dropbox_path = f"/{os.path.basename(output_path)}"
            dropbox_client.files_upload(file.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)

       
        elapsed_time = time.time() - start_time
        delete_delay = max(180, int(elapsed_time) + 60)

       
        shared_link_metadata = dropbox_client.sharing_create_shared_link_with_settings(dropbox_path)
        shared_url = shared_link_metadata.url.replace("?dl=0", "?dl=1")

       
        await interaction.followup.send(
            f"処理が終了しました。ダウンロードリンク: {shared_url}\n\n"
            f"※この動画は{delete_delay // 60}分後に削除されます。" , ephemeral=True
        )

       
        asyncio.create_task(delete_after_delay(dropbox_path, delete_delay))

    except Exception as e:
        await interaction.followup.send(f"エラーが発生しました: {e}", ephemeral=True)

    finally:
       
        if os.path.exists(output_path):
            os.remove(output_path)

async def delete_after_delay(file_path: str, delay: int):
    """指定時間後にDropboxからファイルを削除する"""
    await asyncio.sleep(delay)
    try:
        dropbox_client.files_delete_v2(file_path)
        print(f"Deleted file: {file_path}")
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")

bot.run("ここにトークン")
