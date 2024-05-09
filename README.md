# godfield-flash

日本語版「README」については、[こちらをご覧ください。](https://github.com/Igoorx/godfield-flash/blob/master/README_JP.md)

This repository contains a historical backup of the flash version of the game "God Field" and a server emulator I wrote for it.

I did this server emulator back in 2016 when the flash version was still online, I decided to open-source it now since it was gathering dust in my HD and I really do not want this to vanish. The emulator is pretty much working, but still has some minor bugs and some lacking things.
This do not mean that this project is abandoned, I still want to update this server emulator and make it more reliable and accurate to the original game, if you want to help me, fell free to open a issue or do a pull request!

## Known issues

This server emulator is not nearly perfect, but it works! (as shown in the video below), but here is some issues that I can remember at the moment:

- The artifacts distribution may not be not how it should be (needs research).
- Bots are not very smart, they just thrown the artifacts that he can use at the moment. (And was programmed to)
- The "Fog" curse isn't implemented correctly yet.
- The client backup may not be complete.
  - The backup was done by playing the game and downloading what was requested by the game, so maybe I didn't get everything, and I surely didn't get files from disabled game modes.

https://user-images.githubusercontent.com/14041768/159081100-ff837b56-2b9d-4c80-a722-9e6e32924994.mp4

## Flash is Dead! Now What?

This repository contains the old God Field game that was originally written in Flash. Unfortunately, Flash is no longer supported by most browsers. However, it is still possible to run God Field using the following methods:

1. Use [Ruffle](https://github.com/ruffle-rs/ruffle), a Flash emulator that recently got pretty decent support for God Field.
2. Use a browser that supports Flash.
3. Run the game's SWF file directly via Flash Projector. [You can download the Flash Projector here.](https://fpdownload.macromedia.com/pub/flashplayer/updaters/32/flashplayer_32_sa.exe)

## Requirements

To run the server emulator, you will need **Python 3.9+**. Install all dependencies using `requirements.txt`. Not sure how? [Click here to learn more about the requirements file.](https://pip.pypa.io/en/stable/user_guide/#requirements-files)

## Quick Setup

First, add the following lines to your `hosts` file:

```
127.0.0.1 www.godfield.net
127.0.0.1 static.godfield.net
127.0.0.1 training.godfield.net
127.0.0.1 enfreefight.godfield.net
127.0.0.1 freefight.godfield.net
127.0.0.1 enfreefightprivate.godfield.net
127.0.0.1 freefightprivate.godfield.net
```

*Note: Be sure to remove these entries later; otherwise, you will be unable to reach the official God Field site.*

Next, execute the script `webserver.py` in the `client-files` folder. To execute the script `server.py` in the `server-src` folder, run the command `server.py --ws` if you are okay with using the Ruffle emulator; otherwise, run `server.py` directly.

You're now ready to open the game! Simply navigate to `http://www.godfield.net/en.html` in your web browser, and the game should run using Ruffle. If you prefer to use Adobe Flash Player, you can navigate to `http://www.godfield.net/og_en.html` in a browser that still supports it. Alternatively, you can use the [Flash Projector](https://fpdownload.macromedia.com/pub/flashplayer/updaters/32/flashplayer_32_sa.exe). Just run the executable and press CTRL+O; a window should appear. In this window, just input `http://www.godfield.net/game/godfield.swf` in the `Location` text field and click `OK`.

## Remarks

- I only wrote the server emulator (and an PT-BR translation of the game). All rights about the client files go to [@guuji](https://twitter.com/guuji).
- I'm not the creator of any of the files in the `helpers` folder, but I have modified some of them a little.
