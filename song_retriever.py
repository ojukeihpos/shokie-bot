import youtube_dl as ytdl

class SongDL:
    def __init__(self, songname):
        """grab song name, no download"""
        self.songname= songname
    
    def editsongname(self):
        """don't touch this"""
        s = self.songname.split(' ')
        snf = s[0].strip().capitalize()
        for x in s[1:]:
            snf += "_" + x.strip().capitalize()
        self.songnameed = snf

    def download(self, bitrate):
        """download in specified bitrate, go for the best one"""
        outtmpl = self.songnameed + '.%(ext)s'
        ytdl_format_options = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
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
        with ytdl.YoutubeDL(ytdl_format_options) as ydl:
            info_dict = ydl.extract_info(self.songname, download=True)
            return info_dict['entries'][0]

    def main(self, bitrate = 192):
        """
        Returns: dict with basic data of youtube video
        """
        self.editsongname()
        entries = self.download(str(bitrate))
        req_items = {
            'view_count' : entries['view_count'],
            'id' : entries['id'],
            'description' : entries['description'],
            'thumbnail' : entries['thumbnail'],
            'uploader' : entries['uploader'],
            'like_count' : entries['like_count'],
            'dislike_count' : entries['dislike_count'],
            'title' : entries['title'],
            'webpage_url' : entries['webpage_url'],
            'filename' : self.songnameed + ".mp3",
            'duration' : entries['duration']
        }
        return req_items