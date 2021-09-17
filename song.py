import YTDLSource

class Song:
    __slots__ = ('source')

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