import asyncio
import io
import json
import os
import random
import re
import unicodedata
from typing import Union

import discord
import PIL.Image as PImage
from discord.ext import commands, tasks
from sqlalchemy import create_engine, delete, select, update
from sqlalchemy.orm import Session

from modals.game import Game
from modals.image import Image
from modals.points import Points

with open("./config.json", "r") as f:
    config = json.load(f)

engine = create_engine(config["DATABASE"])


class GameLogic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.game_loop.start()

    def cog_unload(self):
        self.game_loop.cancel()

    def fix_unicode(self, str):
        fixed = unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode()
        return fixed
    
    async def game_thread(self, channel_id: int):
        game_channel: Union[discord.TextChannel, discord.Thread] = await self.bot.fetch_channel(channel_id)  # type: ignore
        with Session(engine) as session:
            timeout_setting = session.scalar(select(Game.timeout).where(Game.guild_id==game_channel.guild.id,Game.channel_id==game_channel.id))
            game_bank = session.scalar(select(Game.databank).where(Game.guild_id==game_channel.guild.id,Game.channel_id==game_channel.id))
        with Session(engine) as session:
            guess_choices = session.execute(select(Image.image,Image.solution).where(Image.guild_id==game_channel.guild.id,Image.databank==game_bank)).fetchall()
        if len(guess_choices) == 0:
            with Session(engine) as session:
                session.execute(delete(Game).where(Game.guild_id==game_channel.guild.id,Game.channel_id==game_channel.id))
                session.commit()
            for task in asyncio.all_tasks():
                if task.get_name() == str(channel_id):
                    task.cancel()
            return await game_channel.send("You have no images to pick from!  New game cancelled.")
        pre_winning_img, winning_solution = random.choice(guess_choices)
        pre_winning_img = PImage.open(io.BytesIO(pre_winning_img))
        pre_winning_img.save(str(game_channel.id)+'-tempimg.png')
        post_winning_img = discord.File(str(game_channel.id)+'-tempimg.png', filename='guess.png')
        hint = winning_solution[0:2] + re.sub(r'[a-zA-Z]', '•', winning_solution[2:])
        round_embed = discord.Embed(title="", description=f"**HINT: {hint}**")
        round_embed.set_image(url='attachment://guess.png')
        await game_channel.send(file=post_winning_img,embed=round_embed) #type: ignore
        os.remove(str(game_channel.id)+'-tempimg.png')
        def check_right(m):
            return m.content == winning_solution and m.channel.id == game_channel.id
        try:
            msg = await self.bot.wait_for('message', check=check_right, timeout=timeout_setting)
            await msg.add_reaction("✅")
            with Session(engine) as session:
                user_has_points = session.execute(select(Points).where(Points.guild_id==game_channel.guild.id,Points.user_id==msg.author.id)).one_or_none()
                if user_has_points is None:
                    new_user = Points(
                        guild_id=game_channel.guild.id,
                        user_id=msg.author.id,
                        points=1
                    )
                    session.add(new_user)
                    session.commit()
                else:
                    cur_points = session.execute(
                        select(Points.points)
                        .where(
                        Points.guild_id==game_channel.guild.id,
                        Points.user_id==msg.author.id
                        )
                    ).one()
                    session.execute(
                        update(Points)
                        .where(
                            Points.guild_id==game_channel.guild.id,
                            Points.user_id==msg.author.id
                        )
                        .values(
                            points=cur_points[0]+1
                        )
                    )
                    session.commit()
            await game_channel.send(f"{msg.author.mention} got it right!\nAnswer was `{winning_solution}`.\n{msg.author.mention}'s current points: {'1' if user_has_points is None else cur_points[0]+1}")  #type: ignore
            await asyncio.sleep(3)
        except asyncio.TimeoutError:
            with Session(engine) as session:
                current_game = session.scalar(select(Game).where(Game.guild_id==game_channel.guild.id,Game.channel_id==game_channel.id))
                session.execute(delete(Game).where(Game.guild_id==game_channel.guild.id,Game.channel_id==game_channel.id))
                session.commit()
            if current_game is not None:
                await game_channel.send(f"### No one answered within {timeout_setting} seconds.  Game closed.")
    
    @tasks.loop(seconds=0.1)
    async def game_loop(self):
        with Session(engine) as session:
            all_games = session.scalars(select(Game.channel_id)).all()
        if len(all_games) > 0:
            for game in all_games:
                running_tasks = list()
                loop = asyncio.get_running_loop()
                for task in asyncio.all_tasks():
                    running_tasks.append(task.get_name())
                if str(game) in running_tasks:
                    pass
                else:
                    loop.create_task(self.game_thread(game), name=str(game))


async def setup(bot: commands.Bot):
    await bot.add_cog(GameLogic(bot))
    print(f"{__name__[5:].upper()} loaded")


async def teardown(bot: commands.Bot):
    await bot.remove_cog(GameLogic(bot)) #type: ignore
    print(f"{__name__[5:].upper()} unloaded")