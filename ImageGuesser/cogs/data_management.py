import json
import os
import unicodedata
from typing import List

import discord
from discord import app_commands
from discord.ext import commands
from modals.game import Game
from modals.image import Image
from modals.points import Points
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

with open("./config.json", "r") as f:
    config = json.load(f)

engine = create_engine(config["DATABASE"])


class DataManagement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        with Session(engine) as session:
            session.execute(delete(Image).where(Image.guild_id==guild.id))
            session.execute(delete(Game).where(Game.guild_id==guild.id))
            session.execute(delete(Points).where(Points.guild_id==guild.id))
            session.commit()
        print(f"Removed from {self.fix_unicode(guild.name)} (ID: {guild.id}) - All data removed.")
    
    @app_commands.command(name='new', description='Add a new image to the guessing database.')  # type: ignore
    @app_commands.describe(solution='The text you want users to send to have a correct answer (case-sensitive)')
    async def add_new_image(self, interaction: discord.Interaction, solution: str, image: discord.Attachment):
        solution = self.fix_unicode(solution)
        with Session(engine) as session:
            new_image = Image(
                guild_id=interaction.guild_id,
                image_url=image.url,
                solution=solution
            )
            session.add(new_image)
            session.commit()
        await interaction.response.send_message(f"Received your new image!\nImage URL: {image.url}\nSolution: `{solution}`", suppress_embeds=True, ephemeral=True, delete_after=120)


    async def remove_image_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        with Session(engine) as session:
            results = session.scalars(select(Image.solution).where(Image.solution.startswith(current), Image.guild_id==interaction.guild_id).limit(25)).all()

        return [app_commands.Choice(name=word, value=word) for word in results]
    
    @app_commands.command(name='remove', description='Remove an image from the guessing database.')  # type: ignore
    @app_commands.describe(word='The word/solution you want to remove from the database (case-sensitive).')
    @app_commands.autocomplete(word=remove_image_autocomplete)
    async def remove_image(self, interaction: discord.Interaction, word: str):
        word = self.fix_unicode(word)
        with Session(engine) as session:
            session.execute(delete(Image).where(Image.solution==word))
            session.commit()
        await interaction.response.send_message(f"Removed `{word}` from the guessing database.")


async def setup(bot: commands.Bot):
    await bot.add_cog(DataManagement(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot: commands.Bot):
    await bot.remove_cog(DataManagement(bot)) #type: ignore
    print(f"{__name__[5:].upper()} unloaded")
