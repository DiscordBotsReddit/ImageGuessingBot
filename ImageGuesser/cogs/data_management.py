import json
import unicodedata
from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import create_engine, delete, select, update
from sqlalchemy.orm import Session

from modals.image import Image

with open("./config.json", "r") as f:
    config = json.load(f)

engine = create_engine(config["DATABASE"])


class DataManagement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed
    

    async def solution_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        with Session(engine) as session:
            results = session.scalars(select(Image.solution).where(Image.solution.startswith(current), Image.guild_id==interaction.guild_id).order_by(Image.solution.asc()).limit(25).distinct()).all()
        return [app_commands.Choice(name=solution, value=solution) for solution in results]
    

    async def databank_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        with Session(engine) as session:
            results = session.scalars(select(Image.databank).where(Image.databank.startswith(current), Image.guild_id==interaction.guild_id).order_by(Image.databank.asc()).limit(25).distinct()).all()
        return [app_commands.Choice(name=solution, value=solution) for solution in results]
    
    
    @app_commands.command(name='new', description='Add a new image to the guessing database.')  # type: ignore
    @app_commands.describe(solution='The text you want users to send to have a correct answer (case-sensitive)')
    @app_commands.describe(databank='The bank of questions you want this solution to be in.')
    async def add_image(self, interaction: discord.Interaction, solution: str, databank: str, image: discord.Attachment):
        with Session(engine) as session:
            new_image = Image(
                guild_id=interaction.guild_id,
                image=await image.read(),
                solution=solution,
                databank=databank
            )
            session.add(new_image)
            session.commit()
        await interaction.response.send_message(f"Received your new image!\nImage URL: {image.url}\nSolution: `{solution}`\nQuiz Bank: `{databank}`", suppress_embeds=True, ephemeral=True, delete_after=120)

    
    @app_commands.command(name='remove', description='Remove an image from the guessing database.')  # type: ignore
    @app_commands.describe(solution='The solution you want to remove from the database (case-sensitive).')
    @app_commands.autocomplete(solution=solution_autocomplete)
    @app_commands.autocomplete(databank=databank_autocomplete)
    async def remove_image(self, interaction: discord.Interaction, solution: str, databank: str):
        with Session(engine) as session:
            session.execute(delete(Image).where(Image.solution==solution,Image.guild_id==interaction.guild_id,Image.databank==databank))
            session.commit()
        await interaction.response.send_message(f"Removed `{solution}` (databank: `{databank}`) from the guessing database.")

    
    @app_commands.command(name='update', description='Update an existing image in the guessing database.')  # type: ignore
    @app_commands.describe(solution='The solution you want to update in the database (case-sensitive).')
    @app_commands.autocomplete(solution=solution_autocomplete)
    async def update_image(self, interaction: discord.Interaction, solution: str, new_solution: Optional[str], new_image: Optional[discord.Attachment], new_bank: Optional[str]):
        with Session(engine) as session:
            if new_image is not None:
                session.execute(update(Image).where(Image.solution==solution).values(image=await new_image.read()))
            if new_bank is not None:
                session.execute(update(Image).where(Image.solution==solution).values(databank=new_bank))
            if new_solution is not None:
                session.execute(update(Image).where(Image.solution==solution).values(solution=new_solution))
            session.commit()
        await interaction.response.send_message(f"Updated `{solution}` in the guessing database.")

    
    @app_commands.command(name='copy', description='Copy an image from one databank to another.')
    @app_commands.autocomplete(solution=solution_autocomplete)
    @app_commands.autocomplete(old_bank=databank_autocomplete)
    @app_commands.autocomplete(new_bank=databank_autocomplete)
    async def update_databank(self, interaction: discord.Interaction, solution: str, old_bank: str, new_bank: str):
        with Session(engine) as session:
            old_entry_image = session.scalar(select(Image.image).where(Image.guild_id==interaction.guild_id,Image.solution==solution,Image.databank==old_bank))
        with Session(engine) as session:
            new_entry = Image(
                guild_id=interaction.guild_id,
                image=old_entry_image,
                solution=solution,
                databank=new_bank
            )
            session.add(new_entry)
            session.commit()
        await interaction.response.send_message(f"Successfully copied `{solution}` from `{old_bank}` databank to `{new_bank}`.", ephemeral=True, delete_after=30)




async def setup(bot: commands.Bot):
    await bot.add_cog(DataManagement(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot: commands.Bot):
    await bot.remove_cog(DataManagement(bot)) #type: ignore
    print(f"{__name__[5:].upper()} unloaded")
