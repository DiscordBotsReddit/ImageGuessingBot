import json
import unicodedata
from typing import List

import discord
from discord import app_commands
from discord.ext import commands
from modals.game import Game
from modals.image import Image
from sqlalchemy import create_engine, delete, distinct, select
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
    
    async def start_game_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        with Session(engine) as session:
            results = session.scalars(select(distinct(Image.quiz_bank)).where(Image.quiz_bank.startswith(current), Image.guild_id==interaction.guild_id).order_by(Image.quiz_bank.asc()).limit(25)).all()
        return [app_commands.Choice(name=solution, value=solution) for solution in results]

    @app_commands.command(name='start', description='Starts a new guessing game.')  #type: ignore
    @app_commands.describe(timeout='The length of time you want the round to run before the game closes (default=5 minutes).')
    @app_commands.describe(guess_bank='The group of images you want to use for this guessing game.')
    @app_commands.autocomplete(guess_bank=start_game_autocomplete)
    async def start_new_game(self, interaction: discord.Interaction, guess_bank: str, timeout: int = 300):
        if str(interaction.channel.type) != 'text':  #type: ignore
            if 'thread' not in str(interaction.channel.type):  #type: ignore
                return await interaction.response.send_message("Please run this command in a text channel.")
        with Session(engine) as session:
            cur_game = session.scalar(select(Game).where(Game.guild_id==interaction.guild_id,Game.channel_id==interaction.channel_id))
        if cur_game is None:
            with Session(engine) as sess:
                new_game = Game(
                    guild_id=interaction.guild_id,
                    channel_id=interaction.channel_id,
                    timeout=timeout,
                    quiz_bank=guess_bank
                )
                sess.add(new_game)
                sess.commit()
            await interaction.response.send_message(f"New guessing game starting from the `{guess_bank}` image bank! (Timeout length = `{timeout}` seconds)")
        else:
            await interaction.response.send_message("There is a game already going in this channel.", ephemeral=True, delete_after=30)


    @app_commands.command(name='end', description='Ends the current guessing game.')  #type: ignore
    async def end_game(self, interaction: discord.Interaction):
        with Session(engine) as session:
            session.execute(delete(Game).where(Game.guild_id==interaction.guild_id,Game.channel_id==interaction.channel_id))
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