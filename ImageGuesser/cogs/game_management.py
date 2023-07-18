import json
import os
import unicodedata
from typing import List

import discord
from discord import app_commands
from discord.ext import commands
from modals.game import Game
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

with open("./config.json", "r") as f:
    config = json.load(f)

engine = create_engine(config["DATABASE"])


class GameManagement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed
    
    @app_commands.command(name='start', description='Starts a new guessing game.')  #type: ignore
    async def start_new_game(self, interaction: discord.Interaction):
        if str(interaction.channel.type) != 'text':  #type: ignore
            if 'thread' not in str(interaction.channel.type):  #type: ignore
                return await interaction.response.send_message("Please run this command in a text channel.")
        with Session(engine) as session:
            cur_game = session.scalar(select(Game).where(Game.guild_id==interaction.guild_id))
        if cur_game is None:
            with Session(engine) as sess:
                new_game = Game(
                    guild_id=interaction.guild_id,
                    channel_id=interaction.channel_id
                )
                sess.add(new_game)
                sess.commit()
            await interaction.response.send_message("New guessing game starting!")
        else:
            await interaction.response.send_message("Game already going...", ephemeral=True, delete_after=30)


    @app_commands.command(name='end', description='Ends the current guessing game.')  #type: ignore
    async def end_game(self, interaction: discord.Interaction):
        with Session(engine) as session:
            session.execute(delete(Game).where(Game.guild_id==interaction.guild_id))
            session.commit()
        await interaction.response.send_message("Current game ended!")
    

async def setup(bot: commands.Bot):
    await bot.add_cog(GameManagement(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot: commands.Bot):
    with Session(engine) as session:
        session.execute(delete(Game))
        session.commit()
    await bot.remove_cog(GameManagement(bot)) #type: ignore
    print(f"{__name__[5:].upper()} unloaded")