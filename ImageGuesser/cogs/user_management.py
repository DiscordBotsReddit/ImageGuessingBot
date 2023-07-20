import json
import unicodedata
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session

from modals.points import Points

with open("./config.json", "r") as f:
    config = json.load(f)

engine = create_engine(config["DATABASE"])


class UserManagement(commands.GroupCog, name='user'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed

    
    @app_commands.command(name="reset_points", description='Reset the user\'s points to 0 (zero).')
    @app_commands.describe(double_check="Are you SURE you want to reset them to 0?")
    @app_commands.checks.has_permissions(ban_members=True)
    async def user_reset_points(self, interaction: discord.Interaction, member: discord.Member, double_check: Literal['no', 'yes']):
        if double_check != 'yes':
            return await interaction.response.send_message(f"{member.mention} points were **NOT** reset.", ephemeral=True, delete_after=30)
        with Session(engine) as session:
            session.execute(update(Points).where(Points.guild_id==interaction.guild_id,Points.user_id==member.id).values(points=0))
            session.commit()
        await interaction.response.send_message(f"{member.mention} had their points reset to 0.")
    
async def setup(bot: commands.Bot):
    await bot.add_cog(UserManagement(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot: commands.Bot):
    await bot.remove_cog(UserManagement(bot)) #type: ignore
    print(f"{__name__[5:].upper()} unloaded")