import YTDLSource

class Song:
    __slots__ = ('source')

    """
    Holds info for a valid query performed by YTDLSource.py.
    Asserted that the query was valid, otherwise a Song object would never
    be instantiated.

    Attributes:
        title: Name of the song
        url: Link to the song of format 'https://www.youtube.com/watch?v=%s' % (VId) where VId is the ID of the song on YouTube
        thumbnail: Thumbnail.
        requester: The discord.context.message.author who queried for the song.
        uploader: Person who uploaded the video onto YouTube
        duration: Length of the song represented by format {}h{}m{}s
    """

    def __init__(self, source: YTDLSource):
        self.source = source

    @property
    def title(self):
        return self.source.title
    
    @property
    def url(self):
        return self.source.url
    
    @property
    def thumbnail(self):
        return self.source.thumbnail
    
    @property
    def requester(self):
        return self.source.requester
    
    @property
    def uploader(self):
        return self.source.uploader

    @property
    def duration(self):
        return self.source.duration