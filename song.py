class Song:
    """
    Holds everything you need about a song
    """

    def __init__(self, songname, requester, songinfo):
        """
        Params:
        songname - name of song
        requester - ctx.author
        """
        self.songname = songname
        self.requester = requester
        self.songinfo = songinfo
        self.dedicatedto = None
        self.dedicationinfo = None

    def get_song_url(self):
        return self.songinfo['webpage_url']