import asyncio
import math

import discord

from discord.ext import commands
#Files used in this program
from YTDLSource import YTDLError, YTDLSource
from VoiceState import VoiceState
from song import Song

class MusicBot(commands.Cog):

    def __init__(self, client : commands.Bot):
        self.client = client
        self.voice_states = {}

        self.client.remove_command('help')

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state or not state.exists:
            state = VoiceState(self.client, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.client.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('This command can\'t be used in DM channels.')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('An error occurred: {}'.format(str(error)))

    @commands.command(pass_context = True, invoke_without_subcommand=True)
    async def join(self, ctx: commands.Context):
        """Joins a voice channel."""
        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(pass_context = True, aliases = ['disconnect'])
    async def leave(self, ctx : commands.Context):
        if not ctx.voice_state.voice:
            return await ctx.send('Not connected to any voice channel.')

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(pass_context = True)
    async def volume(self, ctx : commands.Context, *, volume: int):
        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        if 0 > volume > 100:
            return await ctx.send('Volume must be between 0 and 100')

        ctx.voice_state.volume = volume / 100
        await ctx.send('Volume of the player set to {}%'.format(volume))

    @commands.command(pass_context = True, aliases = ['now'])
    async def current(self, ctx : commands.Context):
        if ctx.voice_state.is_playing:
            embed = ctx.voice_state.current.create_embed()
            await ctx.send(embed=embed)
        else:
            await ctx.send("Nothing is playing!")

    @commands.command(pass_context = True, aliases = ['ps'])
    async def pause(self, ctx : commands.Context):
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')

    @commands.command(pass_context = True, aliases = ['continue'])
    async def resume(self, ctx : commands.Context):
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')

    @commands.command(pass_context = True)
    async def stop(self, ctx : commands.Context):
        ctx.voice_state.songs.clear()

        if ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction('⏹')

    @commands.command(pass_context = True, aliases = ['s'])
    async def skip(self, ctx : commands.Context):
        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing any music right now...')

        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester:
            await ctx.message.add_reaction('⏭')
            ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= 3:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()
            else:
                await ctx.send('Skip vote added, currently at **{}/3**'.format(total_votes))

        else:
            await ctx.send('You have already voted to skip this song.')

    @commands.command(pass_context = True, aliases = ['q'])
    async def queue(self, ctx : commands.Context, *, page : int = 1):
        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                 .set_footer(text='Viewing page {}/{}'.format(page, pages)))
        await ctx.send(embed=embed)

    @commands.command(pass_context = True)
    async def shuffle(self, ctx : commands.Context):
        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction('✅')
    
    @commands.command(pass_context = True, aliases = ['delete', 'rm'])
    async def remove(self, ctx : commands.Context, index : int):
        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction('✅')

    @commands.command(pass_context = True, aliases = ['l'])
    async def loop(self, ctx: commands.Context):
        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction('✅')

    @commands.command(pass_context = True, aliases=['p'])
    async def play(self, ctx: commands.Context, *, search: str):
        """Plays a song.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.client.loop)
            except YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                if not ctx.voice_state.voice:
                    await ctx.invoke(self.join)

                song = Song(source)
                await ctx.voice_state.songs.put(song)
                await ctx.send('Enqueued {}'.format(str(source)))

    @commands.command(pass_context = True)
    async def search(self, ctx : commands.Context, *, search : str):
        async with ctx.typing():
            try:
                source = await YTDLSource.search_source(self.client, ctx, search, loop=self.client.loop)
            except YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                if source == 'sel_invalid':
                    await ctx.send('Invalid selection')
                elif source == 'cancel':
                    await ctx.send(':white_check_mark:')
                elif source == 'timeout':
                    await ctx.send(':alarm_clock: **Time\'s up bud**')
                else:
                    if not ctx.voice_state.voice:
                        await ctx.invoke(self.join)

                    song = Song(source)
                    await ctx.voice_state.songs.put(song)
                    await ctx.send('Enqueued {}'.format(str(source)))

    @join.before_invoke
    @play.before_invoke
    async def sanity_check(self, ctx : commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Bot is already in a voice channel.')

    @commands.command(pass_context = True, aliases = ['h'])
    async def help(self, ctx):
        embed = discord.Embed(colour=discord.Colour(0xb175ff), url="https://discordapp.com", description="This is the command help text for shokie-bot.")
        embed.set_thumbnail(url="https://pbs.twimg.com/profile_images/1436261093861732376/9HV4KPtC_400x400.jpg")
        embed.set_author(name="Help for shokie-bot")

        embed.add_field(name="1. Join/Summon", value="Joins the Bot to the specified channel\nUsage: `$join` or `$summon`", inline=False)
        embed.add_field(name="2. Leave/Disconnect", value="Disconnects bot from the connected channel\nUsage: `$leave` or `$disconnect`", inline=False)
        embed.add_field(name="3. Play", value="Plays the specified song or adds it to queue as required\nBoth song names and youtube urls are supported\nUsage: `$play <songname/url>` or `$p <songname/url>`", inline=False)
        embed.add_field(name="4. Now Playing", value="Shows the now playing song's information\nUsage: `$now` or `$current`", inline=False)
        embed.add_field(name="5. Pause", value="Pauses the current song\nUsage: `$pause` or `$ps`", inline=False)
        embed.add_field(name="6. Resume", value="Resumes the paused song\nUsage: `$resume` or `$continue`", inline=False)
        embed.add_field(name="7. Loop", value="Repeats the currently playing song\nUsage: `$loop` or `$l`", inline=False)
        embed.add_field(name="8. Skip", value="Skips the currently playing song, if any\nUsage: `$skip` or `$s`", inline=False)
        embed.add_field(name="9. Queue", value="Shows the currently playing queue\nUsage: `$queue` or `$q`", inline=False)
        embed.add_field(name="10. Remove", value="Removes and pops out a song at specified index in the queue\nUsage: `$remove <index>` or `$rm <index>` or `$delete <index>`", inline=False)
        await ctx.send(embed = embed)

def setup(client):
    client.add_cog(MusicBot(client))
    print("MusicBot is loaded.")