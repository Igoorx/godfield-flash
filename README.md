# godfield-flash

日本語版「README」については、[こちらをご覧ください。](https://github.com/Igoorx/godfield-flash/blob/master/README_JP.md)

This repository contains a historical backup of the flash version of the game "God Field" and a server emulator I wrote for it.

I did this server emulator back in 2016 when the flash version was still online, I decided to open-source it now since it was gathering dust in my HD and I really do not want this to vanish. The emulator is pretty much working, but still has some minor bugs and some lacking things.
This do not mean that this project is abandoned, I still want to update this server emulator and make it more reliable and accurate to the original game, if you want to help me, fell free to open a issue or do a pull request!

## Known issues

This server emulator is not nearly perfect, but it works! (as shown in the video below), but here is some issues that I can remember at the moment:

- The artifacts distribution may not be not how it should be (needs research).
- Bots are not very smart, they just thrown the artifacts that he can use at the moment. (And was programmed to)
- FOG effect doesn't get removed even if you remove the harm.
- The client backup may not be complete.
  - The backup was done by playing the game and downloading what was requested by the game, so maybe I didn't get everything, and I surely didn't get files from disabled game modes.

https://user-images.githubusercontent.com/14041768/159081100-ff837b56-2b9d-4c80-a722-9e6e32924994.mp4

## Requirements

To run the server emulator, you will need <b>Python 3.9+</b>. You can install all dependencies using the `requirements.txt`, don't know how? [Click here to see more about the requirements file.](https://pip.pypa.io/en/stable/user_guide/#requirements-files)

## Flash is dead! Now what?

This repository contains the old GodField that was written in Flash, however flash isn't supported by most browsers anymore, but don't worry, it is still possible to run GodField if you use some browser that still has support for it or if you run the game's swf directly via Flash Projector.
[You can download the Flash Projector here.](https://fpdownload.macromedia.com/pub/flashplayer/updaters/32/flashplayer_32_sa.exe)

## Quick set-up

To get into the game, you need a webserver running in port 80 with both `static.godfield.net` and `www.godfield.net` folder contents, if you need help to set-up a webserver or do not even knows what it is, [click here, this surely will help you](https://stackoverflow.com/questions/45584453/how-to-create-a-simple-http-webserver-in-python). (Make sure to change the PORT to 80)
After, you need to add these lines to your hosts file:

```
127.0.0.1 www.godfield.net
127.0.0.1 static.godfield.net
127.0.0.1 training.godfield.net
127.0.0.1 enfreefight.godfield.net
127.0.0.1 freefight.godfield.net
127.0.0.1 enfreefightprivate.godfield.net
127.0.0.1 freefightprivate.godfield.net
```

With that, just run the server emulator in python and then open the link `http://www.godfield.net/en.html` in a browser that still supports Flash. Alternatively you can use the [Flash Projector](https://fpdownload.macromedia.com/pub/flashplayer/updaters/32/flashplayer_32_sa.exe), just open it and press CTRL+O, a window should appear, in this window you just have to input `http://www.godfield.net/game/godfield.swf` in the `Location` text field and press the button `OK`.

## Remarks

- I only wrote the server emulator (and an PT-BR translation of the game). All rights about the client files go to [@guuji](https://twitter.com/guuji).
- I'm not the creator of any of the files in the `helpers` folder, but I have modified some of them a little.
