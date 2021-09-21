
# shokie-bot

Private discord bot with music playback functionality



## Features

- Parsing YouTube and Soundcloud links to playback through Discord voice channels
- Connected to a private YouTube premium account for higher quality audio
## Installation

Install required libraries with:

```bash
  pip install -U discord.py[voice] pynacl
```

Install FFmpeg, create an environment variable pointing to ./ffmpeg/bin
## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`DISCORD_TOKEN=<Bot Token>`

  
## Deployment

To deploy this project run

```
  python main.py
```

  
## Usage

All commands can be displayed by typing $help in a Discord message channel. 
## Feedback

For any bug reporting or feature requests, contact shokie#0104 on discord or sophie@tetrisconcept.net

  
## Authors

- [shokie](https://twitter.com/okiedokieshokie)
- Kisa
- Speaker
  
## Acknowledgements

 - [discordpy documentation](https://discordpy.readthedocs.io)
 - [Simplified music bot example](https://github.com/guac420)
 - [Rythm2 reverse engineering project](https://github.com/sandipndev/melody-discord-bot/blob/master/Rythm2.py)
 
## Used By

This project is used by:

- Neku's Shibuya Underground

  