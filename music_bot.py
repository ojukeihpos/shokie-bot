import sys
import time
import traceback
import discord

from discord.ext import commands
import asyncio
from discord.player import FFmpegPCMAudio
from discord.utils import get
import youtube_dl as ytdl
from youtube_dl import YoutubeDL
#Files used in this program
from song import Song
from voice_client import VoiceClient

def __init__(self, client):
    self.client = client

def hh_mm_ss(time_in_seconds):
    min, sec = divmod(time_in_seconds, 60)
    hour = 0
    if min > 60:
        hour, min = divmod(min, 60)
    return (hour, min, sec)

def timeline(current_s, complete_s):
    pointer = "🔘"
    rest = "="
    timeratio = current_s/complete_s
    pointer_loc = int(timeratio*30)
    tl = ""
    for x in range (0, 31):
        if x == pointer_loc:
            tl += pointer
        else:
            tl += rest
    return tl

def double_dig(digit):
    if digit < 10:
        return "0" + str(digit)
    else:
        return str(digit)

def emb(desc):
    embed = discord.Embed()
    embed.color = 3553598
    embed.description = desc
    return embed

def validate_time(time_string):
    time_string = time_string.strip()
    count_colon = 0
    all_dig_except_colon = True
    for x in time_string:
        if x == ':':
            count_colon += 1
        elif not x.isdigit():
            all_dig_except_colon = False
    if all_dig_except_colon == False:
        return (False, "NOT_ALL_DIGITS")
    if not (count_colon > 0 and count_colon < 3):
        return (False, "COLONS_DONT_MATCH")
    splitted_time = time_string.split(':')
    time_dig = []
    for d in splitted_time:
        time_dig.append(int(d))
    proper_time = True
    for x in time_dig:
        if x >= 60:
            proper_time = False
    if proper_time == False:
        return (False, "TIME_IMPROPER")
    return (True, tuple(time_dig))

class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.voice_clients = {}
        self.client.remove_command('help')

    async def on_command_error(self, error: Exception, ctx: commands.Context):
        if hasattr(ctx.command, 'on_error'):
            return
        ignored = (commands.UserInputError)
        error = getattr(error, 'original', error)
        
        if isinstance(error, ignored):
            return
        
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send(embed=emb("**Not a valid command. Use `$help` if you need help regarding commands.**"))
    
    async def disconnect_save_bandwidth_task(self):
        await self.client.wait_until_ready()
        while True:
            for v in self.voice_clients.keys():
                flag = self.voice_clients[v].should_disconnect
                if flag:
                    await self.voice_clients[v].disconnect()
                    del self.voice_clients[v]
                    break
            await asyncio.sleep(2)

    async def server_count_sync(self):
        await self.client.wait_until_ready()
        while True:
            server_ids = []
            for s in self.client.guilds:
                server_ids.append(s.id)
            for vc_key in self.voice_clients.keys():
                if vc_key not in server_ids:
                    await self.voice_clients[vc_key].disconnect()
                    del self.voice_clients[vc_key]
                    break
            await asyncio.sleep(1)

    def channel_check(self, ch1, ch2):
        if ch1 is ch2:
            return (True, None)
        else:
            return (False, ch1.id)

    async def author_needs_to_be_in_same_vc(self, ctx, vc1, vc2):
        if vc1 is vc2:
            return
        else:
            await ctx.send(embed = emb("**You must be in the same voice channel as me to use this command.**"))
            return False

    async def server_specific_command(self, ctx):
        """To inform user that this command is server specific"""
        if ctx.message.guild is None:
            # Private message
            await ctx.send(embed = emb("**This command can only be called from a Server!** :poop:"))
            return False
        else:
            return

    # THIS WORKS FOR NOW I'M GOING TO CHANGE IT LATER
    @commands.command(pass_context = True, aliases = ['summon, appear'])
    async def join (self, ctx):
        """Joins the voice channel user is in."""
        x = await self.server_specific_command(ctx)
        if not x is None:
            # Means called from private msg
            return
        try:
            if(not ctx.message.guild.id in self.voice_clients.keys()):
                #There is no voice client of the server

                chid = self.get_channel_zipperjson(ctx.message.guild.id)
                if chid is None:
                    chid = ctx.message.channel.id
                ch = self.client.get_channel(chid)
                if ch is None:
                    # The channel no longer exists
                    pass
                else:
                    # Channel check
                    aa = self.channel_check(ch, ctx.message.channel)
                    if aa[0] == False:
                        await ctx.send(embed = emb("**Restricted to commands only in** <#{}>.:fox:".format(aa[1])))
                        return

                #Joining the voice channel author is in
                await ctx.author.voice.channel.connect()
                #Informing about the join
                await ctx.send(embed = emb("**Joined** `{}` :mega:".format(ctx.message.author.voice.channel.name)))
                #Storing the voice_client
                thisvc = ctx.author.voice.channel
                #Adding the VoiceClient class with voice_client to self.voice_clients with the server id as key
                self.voice_clients[ctx.message.guild.id] = VoiceClient(thisvc, self.client, ctx.message.guild.id, ctx.author.voice.channel, ctx)
            else:
                #There is a voice client of the server

                #Informing about the voice channel name in which the voice client is in
                await ctx.send(embed = emb("**I am already playing in** `{}` :metal:".format(self.voice_clients[ctx.message.guild.id].vc.channel.name)))

        except discord.errors.InvalidArgument:
            #The user is not in any voice channel
            await ctx.send(embed = emb("<@{}>, **you are supposed to be in a voice channel before asking me in.** :baby_chick:".format(ctx.message.author.id)))

    @commands.command(pass_context = True, aliases = ['disconnect, begone'])
    async def leave (self, ctx):
        """Leaves the voice channel of the server"""

        x = await self.server_specific_command(ctx)
        if not x is None:
            # Means called from private msg
            return
        if(ctx.message.guild.id in self.voice_clients.keys()):
            #VoiceClient present

            # # Channel check
            # aa = self.channel_check(self.voice_clients[ctx.message.guild.id].channel, ctx.message.channel)
            # if aa[0] == False:
            #     await ctx.send(embed = emb("**Restricted to commands only in** <#{}>.:fox:".format(aa[1])))
            #     return

            x = await self.author_needs_to_be_in_same_vc(ctx, ctx.message.author.voice.channel, self.voice_clients[ctx.message.guild.id].vc)
            if x is not None:
                return
            #Disconnecting Voice Client
            await self.voice_clients[ctx.message.guild.id].disconnect()

            #Delete voice client from self.voice_clients
            del self.voice_clients[ctx.message.guild.id]

            #Inform user
            await ctx.send(embed = emb("**Successfully disconnected**! :art:"))

        else:
            #VoiceClient not present

            #Inform user
            await ctx.send(embed = emb("**I am not connected!** :last_quarter_moon_with_face:"))

    def get_channel_zipperjson(self, sid):
        import json
        with open("zipper.json", "r") as z:
            try:
                zipp = json.load(z)
            except json.decoder.JSONDecodeError:
                zipp = {}
        if sid in zipp.keys():
            return zipp[sid]
        else: return

    @commands.command(pass_context = True, aliases = ['p'])
    async def play (self, ctx, *songname):
        x = await self.author_needs_to_be_in_same_vc(ctx, ctx.message.author.voice.channel, self.voice_clients[ctx.message.guild.id].channel)
        if x is not None:
            return
        if len(songname) == 0:
            if self.voice_clients[ctx.message.guild.id].is_playing() and self.voice_clients[ctx.message.guild.id].is_paused == True:
                # paused
                self.voice_clients[ctx.message.guild.id].resume()
                await ctx.send(embed = emb("**Player resumed**! :arrow_forward:"))
                return
            else:
                await ctx.send(embed = emb(":x: **Mention the song to play!**"))
                return

        if self.voice_clients[ctx.message.guild.id].current_song_obj is None and self.voice_clients[ctx.message.guild.id].is_queue_empty() and self.voice_clients[ctx.message.guild.id].first_song_getting_added != True:
            self.voice_clients[ctx.message.guild.id].first_song_getting_added = True
        
        url = False
        if len(songname) == 1 and (songname[0].startswith("https://www.youtube.com/watch?v=") or songname[0].startswith("www.youtube.com/watch?v=") or songname[0].startswith("https://youtu.be/")):
            url = True
            songname = songname[0]
        else:
            songname = ' '.join(songname)
        
        def get_song_info(url):
            if url == False:
                ytdl_options = {
                    'default_search' : 'auto',
                    'quiet' : True
                }
                with ytdl.YoutubeDL(ytdl_options) as ydl:
                    info_dict = ydl.extract_info(songname, download=False)
                    return info_dict
            else:
                ytdl_options = {
                    'quiet' : True
                }
                with ytdl.YoutubeDL(ytdl_options) as ydl:
                    info_dict = ydl.extract_info(songname, download=False)
                    return info_dict

        try:
            #Searching prompt
            await ctx.send("**Searching** `{}` :mag_right:".format(songname))
            #Typing
            async with ctx.typing():
                #Actually searching, prone of error if song not found.
                songinfo = await self.client.loop.run_in_executor(None, get_song_info, url)
                if songinfo['is_live'] is not None:
                # The song is a live telecast
                    await ctx.send(embed = emb("**Melody is under development for live playback.**"))
                    return
                # Creating the Song object
                song_object = Song(songname, ctx.message.author, songinfo)
                # Adding the Song object to current server's queue
                if self.voice_clients[ctx.message.guild.id].first_song_getting_added != True:
                    await asyncio.sleep(5)
                pos = self.voice_clients[ctx.message.guild.id].add_song_to_queue(song_object)
                if pos == 1 and self.voice_clients[ctx.message.guild.id].current_song_obj is None:
                    # This is the first song added to queue
                    await ctx.send("**Playing** :notes: `{}` **- Now!**".format(songinfo['title'].strip().title()))
                else:
                    # Creating added to queue embed
                    embed = discord.Embed()
                    embed.title = songinfo['title'].strip().title()
                    embed.url = songinfo['webpage_url']
                    embed.color = 12345678
                    embed.set_thumbnail(url = songinfo['thumbnail'])
                    embed.set_author(name = "Added to Queue", icon_url = ctx.message.author.avatar_url)
                    embed.add_field(inline = True, name = "Channel", value = songinfo['uploader'].strip().title())
                    hms = await self.client.loop.run_in_executor(None, hh_mm_ss, songinfo['duration'])
                    hms_tuple = ("" if hms[0]==0 else (str(hms[0]) + "h "), "" if hms[1]==0 else (str(hms[1]) + "m "), "" if hms[2]==0 else (str(hms[2]) + "s "))
                    embed.add_field(inline = True, name = "Duration", value = "{}{}{}".format(hms_tuple[0], hms_tuple[1], hms_tuple[2]))
                    embed.add_field(inline = True, name = "Position in Queue", value = str(pos))
                    if self.voice_clients[ctx.message.guild.id].current_song_obj is None:
                        await asyncio.sleep(5)
                        eta = self.voice_clients[ctx.message.guild.id].eta(len(self.voice_clients[ctx.message.guild.id].queue)-1)
                        hms = await self.client.loop.run_in_executor(None, hh_mm_ss, eta)
                        hms_tuple = ("" if hms[0]==0 else (str(hms[0]) + "h "), "" if hms[1]==0 else (str(hms[1]) + "m "), "" if hms[2]==0 else (str(hms[2]) + "s "))
                        embed.add_field(inline = True, name = "ETA until playing", value = "{}{}{}".format(hms_tuple[0], hms_tuple[1], hms_tuple[2]))
                        # Sending the Embed
                        await ctx.send(embed = embed)
                        ytdl_format_options = {
                            'format': 'bestaudio/best',
                            'restrictfilenames': True,
                            'noplaylist': True,
                            'nocheckcertificate': True,
                            'ignoreerrors': False,
                            'logtostderr': False,
                            'quiet': True,
                            'no_warnings': True,
                            'default_search': 'auto',
                            'source_address': '0.0.0.0', # bind to ipv4 since ipv6 addresses cause issues sometimes
                        }
                        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
                        voice = get(self.client.voice_clients, guild=ctx.guild)
                        with YoutubeDL(ytdl_format_options) as ydl:
                                info = ydl.extract_info(url, download=False)
                                voice.play(FFmpegPCMAudio(info['formats'][0]['url'], **FFMPEG_OPTIONS))
                                voice.is_playing()
                                print("Playing {}".format(self.current_song_obj.songinfo['title'].strip().title()))
        except ytdl.utils.DownloadError:
            # No search results
            await self.client.send_message(ctx.message.channel , embed = emb(":x: **No results!**"))


    @commands.command(pass_context = True)
    async def help(self, ctx, typ = "short"):
        embed = discord.Embed(colour=discord.Colour(0xb175ff), url="https://discordapp.com", description="This is the command help text for shokie-bot.")
        embed.set_thumbnail(url="https://pbs.twimg.com/profile_images/1436261093861732376/9HV4KPtC_400x400.jpg")
        embed.set_author(name="Help for shokie-bot")

        embed.add_field(name="1. Join/Summon", value="Joins the Bot to the specified channel\nUsage: `$join` or `$summon`", inline=False)
        embed.add_field(name="2. Leave/Disconnect", value="Disconnects bot from the connected channel\nUsage: `$leave` or `$disconnect`", inline=False)
        embed.add_field(name="3. Play", value="Plays the specified song or adds it to queue as required\nBoth song names and youtube urls are supported\nUsage: `$play <songname/url>` or `$p <songname/url>`", inline=False)
        embed.add_field(name="4. Now Playing", value="Shows the now playing song's information\nUsage: `$nowplaying` or `$np`", inline=False)
        embed.add_field(name="5. Pause", value="Pauses the current song\nUsage: `$pause` or `$ps`", inline=False)
        embed.add_field(name="6. Resume", value="Resumes the paused song\nUsage: `$resume` or `$continue`", inline=False)
        embed.add_field(name="7. Repeat", value="Repeats the currently playing song\nUsage: `$repeat` or `$r`", inline=False)
        embed.add_field(name="8. Skip", value="Skips the currently playing song, if any\nUsage: `$skip` or `$s`", inline=False)
        embed.add_field(name="9. Queue", value="Shows the currently playing queue\nUsage: `$queue` or `$q`", inline=False)

        if typ != "short" and typ != "small":
            embed.add_field(name="10. Remove", value="Removes and pops out a song at specified index in the queue\nUsage: `$remove <index>` or `$rm <index>`", inline=False)
            embed.add_field(name="11. Seek", value="Seeks current player to a specific time within the song's duration\nUsage: `$seek <timestamp>` or `$sk <timestamp>`, where `timestamp = hh:mm:ss or mm:ss`", inline=False)
            embed.add_field(name="12. Show NP Looped", value="Shows the now playing song every time a song changes\nA toogle switch to on/off this feature\nIt is a saved data for each server\nUsage: `$shownplooped` or `$snploop`", inline=False)
            embed.add_field(name="13. Add Favourite", value="Adds the current song or a song at a queue-index to the user's favourites\nIf no index is given, the current song is added\nUsage: `$addfav [queue-index]` or `$afav [queue-index]`", inline=False)
            embed.add_field(name="14. Show Favourites", value="Direct messages the saved favourites data of you\nUsage: `$showfav` or `$sfav`", inline=False)
            embed.add_field(name="15. Remove Favourite", value="Removes an indexed-favourite\nRefer to index shown before `sfav` message for index\nUsage: `$removefav <fav-index>` or `$rfav <fav-index>`", inline=False)
            embed.add_field(name="16. Play from Favourite", value="Plays or adds to queue the indexed favourite song\nUsage: `$playfav <fav-index>` or `$pfav <fav-index>`", inline=False)
            embed.add_field(name="17. Dedicate", value="Dedicates a song to someone also listening to the same queue in the same voice channel as the author who wants to dedicate\nUse only in the bot's private message as dedications are a secret\nThe person dedicated to will be informed when the dedicated song starts playing\nUsage: `$dedicate <songname>` or `$d <songname>`", inline=False)
            embed.add_field(name="18. Lyrics", value="Shows lyrics for the currently playing song or a song specifically asked for\nCan give wrong results oftentimes as this is under development\nUsage: `$lyrics [songname]` or `$l [songname]`", inline=False)

        await ctx.send(embed = embed)

def setup(client):
    client.add_cog(MusicBot(client))
    print("MusicBot is loaded.")