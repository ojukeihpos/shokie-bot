import asyncio
from SongQueue import SongQueue
from discord.ext import commands

from async_timeout import timeout

class VoiceError(Exception):
    pass

class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.client = bot
        self._ctx = ctx
        
        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()
        self._loop = False
        self._volume = 1
        self.skip_votes = set()
        self.audio_player = bot.loop.create_task(self.audio_player_task())
    
    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, v : bool):
        self._loop = v

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, v : float):
        self._volume = v

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()

            if not self.loop:
                try:
                    async with timeout(100):
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.client.loop.create_task(self.stop())
                    return
            
            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after = self.play_next_song)
            await self.current.source.channel.send(embed = self.current.create_embed())

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None