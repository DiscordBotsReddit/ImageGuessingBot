import json
import unicodedata
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from modals.game import Game
from modals.image import Image
from modals.points import Points

with open("./config.json", "r") as f:
    config = json.load(f)

engine = create_engine(config["DATABASE"])


async def find_cmd(bot: commands.Bot, cmd: str, group: Optional[str]):
    if group is None:
        command = discord.utils.find(
            lambda c: c.name.lower() == cmd.lower(),
            await bot.tree.fetch_commands(),
        )
        return command
    else:
        cmd_group = discord.utils.find(
            lambda cg: cg.name.lower() == group.lower(),
            await bot.tree.fetch_commands(),
        )
        for child in cmd_group.options:  #type: ignore
            if child.name.lower() == cmd.lower():
                return child
    return "No command found."


class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed
    

    @app_commands.command(name="version", description="Show the bot's version.")
    async def show_version(self, interaction: discord.Interaction):
        with open("./config.json", "r") as f:
            config = json.load(f)
        await interaction.response.send_message(f"Current version: `v{config['VERSION']}`")
    

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        print(f"Added to {guild.name} (ID: {guild.id})")


    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        with Session(engine) as session:
            session.execute(delete(Image).where(Image.guild_id==guild.id))
            session.execute(delete(Game).where(Game.guild_id==guild.id))
            session.execute(delete(Points).where(Points.guild_id==guild.id))
            session.commit()
        print(f"Removed from {self.fix_unicode(guild.name)} (ID: {guild.id}) - All data removed.")
    

async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot: commands.Bot):
    await bot.remove_cog(Utility(bot)) #type: ignore
    print(f"{__name__[5:].upper()} unloaded")