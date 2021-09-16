from song import Song
import asyncio
import discord
from discord.utils import get
from discord import FFmpegPCMAudio
import youtube_dl as ytdl
from youtube_dl import YoutubeDL
import time

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

class VoiceClient():
    def __init__(self, voice_client, bot_client, server, channel, ctx):
        self.vc = voice_client
        self.server = server # which discord am i in?
        self.client = bot_client # instance of my own existance
        
        # media player properties
        self.is_paused = False
        self.repeat = False
        self.show_current = False # do we show the current song on switch?
        self.channel = channel # which channel do we populate updates to?

        # auto disconnect properties
        self.disconnect_timer = 0
        self.should_disconnect = True
        self.time_to_delay = 300

        self.queue = [] # consists of Song objects, defined in song.py
        
        self.current_song_obj = None
        self.current_player = None
        self.current_player_time_started = 0
        self.current_player_total_paused = 0
        self.current_player_time_paused = 0

        self.volume = 1
        self.shuffle = False
        self.npmsg = None
        self.pmsg = None
        self.skp = False
        self.first_song_getting_added = False

        self.skip_people = [] # keep track of who is voting to skip

        self.client.loop.create_task(self.song_player_task(ctx)) # check queues, play songs

    def shuffle_state(self):
        self.shuffle = not self.shuffle
        return self.shuffle
    
    def change_vol_zero_to_hundred(self, vol):
        vol = vol/100
        if self.current_player is not None:
            self.current_player.volume = vol
            self.volume = vol

    def current_song_info(self):
        if not self.current_song_obj is None:
            return self.current_song_obj.songinfo
        else:
            return None

    def current_playing_time(self):
        """Returns current time of song being played"""
        if (self.current_player_time_paused != 0):
            # currently paused, alternatively check self.is_paused
            return time.time() - (self.current_player_time_started + self.current_player_time_paused + (time.time() - self.current_player_time_paused))
        else:
            a = time.time() - (self.current_player_time_started + self.current_player_total_paused)
            if a > 99999:
                print("What the hell? Line 98")
                return 0
            else:
                return a

    def eta(self, num):
        """Time until queue[num-1] plays"""
        if self.is_queue_empty():
            return self.current_song_obj.songinfo['duration'] - int(self.current_playing_time)
        else:
            rest_time = 0
            for thissongobj in self.queue[0:num]:
                rest_time += thissongobj.songinfo['duration']
                return rest_time + (self.current_song_obj.songinfo['duration'] - int(self.current_playing_time()))

    def reset(self):
        """Reset player when loop ended"""
        self.time_to_delay = 300 # 30s delayed in case of no song play
        self.current_song_obj = None # Current Song object
        self.current_player = None # Current Song Player
        self.current_player_time_started = 0 # To record time when song was started
        self.current_player_total_paused = 0 # To record total pause time
        self.current_player_time_paused = 0 # To record time paused
        self.time_to_delay = 300
        self.first_song_getting_added = False

    def skip(self):
        """Skip current song"""
        self.skp= True
        #Stop
        if self.is_playing():
            self.stop()
        # Creates problem when repeat = On

    def how_many_listening(self):
        """Returns how many are listening to the song"""
        return len(self.vc.channel.voice_members)-1

    def askip_ret_pass(self, mid):
        if mid not in self.skip_people:
            self.skip_people.append(mid)
            if (len(self.skip_people) / self.how_many_listening()) * 100 >= 30:
                return True
            else:
                return False
        else:
            return None

    def add_song_to_queue(self, song_object):
        """Add Song object to queue"""
        self.queue.append(song_object)
        return len(self.queue)

    def is_queue_empty(self):
        """Checks if queue empty or not"""
        if self.queue == []:
            return True
        else:
            return False

    def is_playing(self):
        """Checks if something is playing or not"""
        if self.current_player is None:
            return False
        else:
            return not self.current_player.is_done()

    def pause(self):
        """Pauses the current song."""
        if self.is_playing():
            #Playing
            self.current_player.pause()
            self.current_player_time_paused = time.time()
            self.is_paused = True

    def stop(self):
        """Stops the current song."""
        if not self.current_player is None:
            self.current_player.stop()
            self.justskipped = True

    def resume(self):
        """Resumes the current song."""
        if self.is_paused == True:
            #Not playing
            self.current_player.resume()
            self.current_player_total_paused += time.time() - self.current_player_time_paused
            self.current_player_time_paused = 0
            self.is_paused = False

    def add_next(self):
        """Adds next song to self.current_player_obj"""
        if self.repeat == True and self.skp== False:
            # Only condition when the song must not change
            return
        else:
            # The song must change
            try:
                if self.shuffle == True:
                # Must shuffle
                    if len(self.queue) >= 1:
                    # Songs exist in queue
                        import random
                        self.current_song_obj = self.queue.pop(random.randrange(len(self.queue)))
                        del random
                    else:
                        raise IndexError
                else:
                    # No shuffle
                    self.current_song_obj = self.queue.pop(0)

                    def del_reac():
                        self.shoulddelreact = False
                for e in self.reac:
                    try:
                        if self.npmsg is not None:
                            self.client.loop.create_task(self.client.remove_reaction(self.npmsg, e, self.server.me))
                            self.client.loop.create_task(asyncio.sleep(0.1))
                    except:
                        pass
                        self.npmsg = None

                del_reac()

                self.current_player_time_started = time.time() # To record time when song was started
                self.current_player_total_paused = 0 # To record total pause time
                self.current_player_time_paused = 0 # To record time paused

            except IndexError:
                # Queue ended
                self.reset()

    async def np_sync(self):
        # Show current song when songs change
        current_song_info = self.current_song_info()
        embed = discord.Embed()
        embed.title = current_song_info['title'].strip().title()
        embed.url = current_song_info['webpage_url']
        embed.color = 654814
        embed.set_thumbnail(url = current_song_info['thumbnail'])
        embed.set_author(name = "Playing Now >")
        embed.description = "{}\nRequested by `{}`".format("" if self.shuffle==False else ":twisted_rightwards_arrows: **ON**",self.current_song_obj.requester.name)
        #Sending this embed
        self.npmsg = await self.client.send_message(self.channel, embed = embed)

        # Reaction Stuff
        # Play/Pause button, Track_next, Repeat one, Twisted rightwards arrow, speaker, loud sound, hearts
        reacting_to = ["\U000023ed", "\U0001f502", "\U0001f500", "\U00002665"]
        self.reac = reacting_to
        for e in reacting_to:
            await self.client.add_reaction(self.npmsg, e)

            self.shoulddelreact = True
            await asyncio.sleep(20)

            if self.shoulddelreact:
                for e in reacting_to:
                    try:
                        if self.npmsg is not None:
                            await self.client.remove_reaction(self.npmsg, e, self.server.me)
                            await asyncio.sleep(0.4)
                    except:
                        pass
                    self.npmsg = None

    def get_np_show_inf_sync(self):
        """json-load and check if snp data is already there"""
        import json
        with open("snpinfo.json", "r") as snpinfo:
            try:
                snpinf = json.load(snpinfo)
            except json.decoder.JSONDecodeError:
                # File not found/isn't json-compatible
                snpinf = {}
                if self.server in snpinf.keys():
                    self.show_current = snpinf[self.server]
                else:
                    self.show_current = False

    def save_whoever_is_listening_and_what(self):
        import json
        with open("listener_records.json", "r") as lr:
            try:
                lr = json.load(lr)
            except json.decoder.JSONDecodeError:
                lr = {}
        members = self.vc.channel.voice_members
        for thismember in members:
            if thismember.id == self.server.me.id:
                continue
            elif thismember.id in lr.keys():
                songshelistened = lr[thismember.id]
                currenturl = self.current_song_obj.songinfo['webpage_url']
                #{songname, songurl, count} will be stored
                entry_found = False
                for songdict in songshelistened:
                    if songdict['songurl'] == currenturl:
                        entry_found = True
                        count_of_times_song_heard = songdict['count']
                        songshelistened.remove(songdict)
                        songdict['songname'] = self.current_song_obj.songinfo['title']
                        songdict['songurl'] = currenturl
                        songdict['count'] = count_of_times_song_heard + 1
                        lr[thismember.id].append(songdict)
                        break
                if entry_found == False:
                #Entry wasn't found
                    lr[thismember.id].append({'songname' : self.current_song_obj.songinfo['title'], 'songurl' : self.current_song_obj.songinfo['webpage_url'], 'count' : 1})
            else:
                lr[thismember.id] = []
                lr[thismember.id].append({'songname' : self.current_song_obj.songinfo['title'], 'songurl' : self.current_song_obj.songinfo['webpage_url'], 'count' : 1})

        with open("listener_records.json", "w") as lrf:
            json.dump(lr, lrf)

    async def seeksong(self, formatted_time, time_in_s):
        """Seek the song to some time ahead/back"""
        # Use: before_options="-ss 00:00:30"
        cur_song_obj = self.current_song_obj
        url = self.current_song_obj.get_song_url()
        pl = await self.vc.create_ytdl_player(url, ytdl_options = {'quiet':True}, after = self.add_next, before_options = "-ss {}".format(formatted_time))
        self.current_player.pause()
        self.current_player = None
        self.current_player = pl
        self.current_player.volume = self.volume
        self.current_player.start()
        self.current_song_obj = cur_song_obj
        self.current_player_time_started = time.time() - time_in_s
        self.current_player_total_paused = 0
        self.current_player_time_paused = 0

    async def song_player_task(self, ctx):
        """Play the song in this task"""
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
        while True:
            # To play songs and listen continuously for new songs added.

            # First song to self.current_player_object
            if len(self.queue) == 1 and self.current_song_obj is None :
                # Current Song is the first song object added.
                self.current_song_obj = self.queue.pop(0)
                pass

            # For new songs in queue
            if not self.is_playing() and not self.current_song_obj is None:
                # Player not playing anything
                # This means we need to play the next song

                # URL of the song
                url = self.current_song_obj.get_song_url()
                # Creating the song player
                if self.current_song_obj is not None:
                    # Starting the song player
                    #self.current_player.start()
                    with YoutubeDL(ytdl_format_options) as ydl:
                        info = ydl.extract_info(url, download=False)
                    voice.play(FFmpegPCMAudio(info['formats'][0]['url'], **FFMPEG_OPTIONS))
                    voice.is_playing()
                    print("Playing {}".format(self.current_song_obj.songinfo['title'].strip().title()))
                    self.current_player_time_started = time.time()

                    # 2 minutes delayed in case of disconnect because of no members
                    self.time_to_delay = 500

                    # await self.client.loop.run_in_executor(None, self.get_np_show_inf_sync)
                    # if self.show_current == True and (self.repeat != True or self.justskipped == True):
                    #     await self.client.loop.create_task(self.np_sync())

                self.justskipped = False
                self.skp= False
                self.skip_people = []
                self.first_song_getting_added = False

            def handle_disconnection():
                members = self.vc.members

                if len(members) > 1 and self.disconnect_timer != 0 and not (self.is_queue_empty() and not self.is_playing()):
                    self.should_disconnect = False
                    self.disconnect_timer = 0

                if len(members) == 1:
                # Nobody is hearing this song. That one member is the bot itself.
                    if self.disconnect_timer == 0:
                        self.disconnect_timer = time.time()
                    elif (time.time() - self.disconnect_timer) > self.time_to_delay:
                        self.should_disconnect = True

                if self.is_queue_empty() and not self.is_playing():
                    if self.disconnect_timer == 0:
                        self.disconnect_timer = time.time()
                    elif (time.time() - self.disconnect_timer) > self.time_to_delay:
                        self.should_disconnect = True

            handle_disconnection()

            # So that everything works properly
            await asyncio.sleep(3)