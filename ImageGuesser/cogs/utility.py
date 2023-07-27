import datetime
import io
import json
import os
import unicodedata
from time import time
from typing import Optional

import discord
import PIL.Image as PImage
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import BucketType
from sqlalchemy import create_engine, delete, distinct, select
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
    

    @commands.command(name='imglookup', hidden=True)
    @commands.is_owner()
    async def imglookup(self, ctx: commands.Context, id: int):
        try:
            new_filename = str(id)+'-tempimg.png'
            with Session(engine) as session:
                pre_image = session.execute(select(Image.image).where(Image.id==id)).one_or_none()
            if pre_image is None:
                return await ctx.reply("No image with that ID.")
            pre_image = PImage.open(io.BytesIO(pre_image[0]))
            pre_image.save(new_filename)
            post_img = discord.File(new_filename, filename='image.png')
            await ctx.reply(file=post_img) #type: ignore
            os.remove(new_filename)
        except Exception as e:
            await ctx.reply(f"Error:\n{e}")

    @commands.command(name='imgrem', hidden=True)
    @commands.is_owner()
    async def imgrem(self, ctx: commands.Context, id: int):
        with Session(engine) as session:
            can_delete = session.execute(select(Image).where(Image.id==id)).all()
            if can_delete is None:
                return await ctx.reply("No image with that ID.")
            session.execute(delete(Image).where(Image.id==id))
            session.commit()
        await ctx.reply(f"Deleted image with id #{id}.")
    

    @app_commands.command(name="stats", description="Show the bot's stats.")
    @app_commands.checks.cooldown(rate=1, per=60, key=lambda g: (g.guild_id))
    async def show_bot_stats(self, interaction: discord.Interaction):
        with open("./config.json", "r") as f:
            config = json.load(f)
        stats_embed = discord.Embed(color=discord.Color.orange(), title=f"{self.bot.user.display_name}'s Stats")
        stats_embed.set_thumbnail(url=self.bot.user.avatar.url)
        try:
            stats_embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)
        except:
            stats_embed.set_author(name=interaction.user.display_name)
        stats_embed.add_field(name='Current Version', value=f"`{config['VERSION']}`", inline=False)
        stats_embed.add_field(name='Last Reboot', value=f"<t:{int(start_time)}:R>", inline=False)
        total_members = 0
        for guild in self.bot.guilds:
            total_members += guild.member_count
        stats_embed.add_field(name="Total Members", value=f"{total_members:,}")
        stats_embed.add_field(name="Total Guilds", value=f"{len(self.bot.guilds):,}")
        with Session(engine) as session:
            num_images = session.scalars(select(Image.id)).all()
            num_players = session.scalars(select(distinct(Points.user_id))).all()
        stats_embed.add_field(name="", value=f"")
        stats_embed.add_field(name="Total Images", value=f"{len(num_images):,}")
        stats_embed.add_field(name='Total Players', value=f"{len(num_players):,}")
        stats_embed.add_field(name="", value=f"")
        await interaction.response.send_message(embed=stats_embed)

    @show_bot_stats.error
    async def on_show_bot_stats_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            use_again = datetime.datetime.now() + datetime.timedelta(seconds=int(error.retry_after))
            await interaction.response.send_message(f"That command can be used again <t:{int(use_again.timestamp())}:R>.", ephemeral=True, delete_after=int(error.retry_after))
    

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
    global start_time
    start_time = time()
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot: commands.Bot):
    await bot.remove_cog(Utility(bot)) #type: ignore
    print(f"{__name__[5:].upper()} unloaded")