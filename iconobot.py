import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

BASE_URL = "https://iconostasis.onrender.com"

# Fonts (you can replace with local .ttf fonts)
TITLE_FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
TEXT_FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)

@bot.command()
async def icon(ctx, icon_id: int):
    try:
        # Fetch icon JSON
        resp = requests.get(f"{BASE_URL}/api/icon/{icon_id}")
        if resp.status_code != 200:
            await ctx.send(f"Icon ID {icon_id} not found.")
            return
        data = resp.json()

        # Create base image
        width, height = 800, 400
        card = Image.new("RGBA", (width, height), (30, 30, 30, 255))  # dark bg
        draw = ImageDraw.Draw(card)

        # Load icon image
        icon_resp = requests.get(data["image_url"])
        icon_img = Image.open(BytesIO(icon_resp.content)).convert("RGBA")
        icon_img = icon_img.resize((200, 200))
        card.paste(icon_img, (50, 100), icon_img)

        # Title
        draw.text((270, 50), data["title"], font=TITLE_FONT, fill=(255, 215, 0))

        # Metadata
        meta_y = 100
        spacing = 30
        metadata = [
            f"Saint(s): {', '.join(data.get('saints', [])) or 'None'}",
            f"Tradition: {data.get('tradition', 'Unknown')}",
            f"Century: {data.get('century', 'Unknown')}",
            f"Region: {data.get('region', 'Unknown')}",
            f"Iconographer: {data.get('iconographer', 'Unknown')}",
            f"Uploaded by: {data.get('uploader','Unknown')}"
        ]
        for i, line in enumerate(metadata):
            draw.text((270, meta_y + i*spacing), line, font=TEXT_FONT, fill=(255, 255, 255))

        # Save to bytes
        buffer = BytesIO()
        card.save(buffer, format="PNG")
        buffer.seek(0)

        # Send as Discord file
        await ctx.send(file=discord.File(fp=buffer, filename=f"icon_{icon_id}.png"))

    except Exception as e:
        await ctx.send(f"Error generating icon card: {e}")


