import json
import unicodedata
from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands
from modals.game import Game
from modals.image import Image
from modals.points import Points
from sqlalchemy import create_engine, delete, select, update
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
    
    
    @app_commands.command(name='new', description='Add a new image to the guessing database.')  # type: ignore
    @app_commands.describe(solution='The text you want users to send to have a correct answer (case-sensitive)')
    @app_commands.describe(quiz_bank='The bank of questions you want this solution to be in.')
    async def add_new_image(self, interaction: discord.Interaction, solution: str, quiz_bank: str, image: discord.Attachment):
        with Session(engine) as session:
            new_image = Image(
                guild_id=interaction.guild_id,
                image=await image.read(),
                solution=solution,
                quiz_bank=quiz_bank
            )
            session.add(new_image)
            session.commit()
        await interaction.response.send_message(f"Received your new image!\nImage URL: {image.url}\nSolution: `{solution}`\nQuiz Bank: `{quiz_bank}`", suppress_embeds=True, ephemeral=True, delete_after=120)


    async def remove_image_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        with Session(engine) as session:
            results = session.scalars(select(Image.solution).where(Image.solution.startswith(current), Image.guild_id==interaction.guild_id).order_by(Image.solution.asc()).limit(25)).all()
        return [app_commands.Choice(name=solution, value=solution) for solution in results]
    
    @app_commands.command(name='remove', description='Remove an image from the guessing database.')  # type: ignore
    @app_commands.describe(solution='The solution you want to remove from the database (case-sensitive).')
    @app_commands.autocomplete(solution=remove_image_autocomplete)
    async def remove_image(self, interaction: discord.Interaction, solution: str):
        with Session(engine) as session:
            session.execute(delete(Image).where(Image.solution==solution))
            session.commit()
        await interaction.response.send_message(f"Removed `{solution}` from the guessing database.")

    
    async def update_image_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        with Session(engine) as session:
            results = session.scalars(select(Image.solution).where(Image.solution.startswith(current), Image.guild_id==interaction.guild_id).order_by(Image.solution.asc()).limit(25)).all()
        return [app_commands.Choice(name=solution, value=solution) for solution in results]
    
    @app_commands.command(name='update', description='Update an existing image in the guessing database.')  # type: ignore
    @app_commands.describe(solution='The solution you want to update in the database (case-sensitive).')
    @app_commands.autocomplete(solution=update_image_autocomplete)
    async def update_image(self, interaction: discord.Interaction, solution: str, new_solution: Optional[str], new_image: Optional[discord.Attachment], new_bank: Optional[str]):
        with Session(engine) as session:
            if new_image is not None:
                session.execute(update(Image).where(Image.solution==solution).values(image=await new_image.read()))
            if new_bank is not None:
                session.execute(update(Image).where(Image.solution==solution).values(quiz_bank=new_bank))
            if new_solution is not None:
                session.execute(update(Image).where(Image.solution==solution).values(solution=new_solution))
            session.commit()
        await interaction.response.send_message(f"Updated `{solution}` in the guessing database.")


async def setup(bot: commands.Bot):
    await bot.add_cog(DataManagement(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot: commands.Bot):
    await bot.remove_cog(DataManagement(bot)) #type: ignore
    print(f"{__name__[5:].upper()} unloaded")
