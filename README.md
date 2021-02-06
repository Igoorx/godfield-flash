# godfield-flash
Historical backup of godfield flash version and server emulator for server-side.

I did this server emulator in 2016 when this version was still online, I decided to open the source of it now because it was gathering dust in my HD and I really do not want this to vanish. The emulator is pretty much working, but still have bugs and things lacking.
This do not mean that this project is abandoned, I still want to update this server emulator and make it more reliable and accurate to the original game, if you want to help me, fell free to open a issue or do a pull request!

## Known issues
This server emulator is not nearly perfect, but it works! (as shown in the gif below), but here is some issues that I can remember at the moment:
- Sometimes the match can just stop with the server receiving a ERROR packet.
- It is common for the client-side match desynchronize with the server-side match.
- The artifacts distribution is not how it should be (needs research).
- Bots are not very smart, they just thrown the artifacts that he can use at the moment. (And was programmed to)
- Bots completely ignore harms effects.
- Bots are not replacing a disconnected player because they are not very reliable.
- Some artifacts do not have a programmed behaviour, or are not complete, for example the `String of Fate` and `Dangerous Pestle`.
- FOG effect doesn't get removed even if you remove the harm.
- Exchange is not programmed yet.
- Gods are not programmed yet.
- Client backup may not be 100% complete (maybe 95%?).

![ScreenShot](https://i.imgur.com/JjMTum8.gif)

## Requirements
To run the emulator, you need <b>Python 2.7</b>, you can install all dependencies using the `requirements.txt`. Do not know how? [Click here to see more about the requirements file.](https://pip.pypa.io/en/stable/user_guide/#id12)

## Flash is dead! Now what?
The version of GodField in this repository is written using Flash, however flash isn't supported by most browsers anymore, but it is still possible to run GodField if you use some browser that still has support for it or if you run the game's swf directly via Flash Projector.
[You can download the Flash Projector here](https://fpdownload.macromedia.com/pub/flashplayer/updaters/32/flashplayer_32_sa.exe)

## Quick set-up
To get into the game, you need a webserver running in port 80 with both `static.godfield.net` and `www.godfield.net` folder contents, if you need help to set-up a webserver or do not even knows what it is, [click here, this surely will help you](https://stackoverflow.com/questions/45584453/how-to-create-a-simple-http-webserver-in-python). (Take sure to change the PORT to 80)
Remember too to run the server emulator!
After, you need to add these lines to your hosts file:
```
127.0.0.1 www.godfield.net
127.0.0.1 freefight.godfield.net
```
With that, just open the link `http://www.godfield.net/en.html` in a browser that still supports Flash.
Alternatively you can open the [Flash Projector](https://fpdownload.macromedia.com/pub/flashplayer/updaters/32/flashplayer_32_sa.exe) and press CTRL+O, a window should appear, in this window you just have to input `http://www.godfield.net/game/godfield.swf` in the `Location` text field and press the button `OK`.

## Remarks
- I only did the server (and also a PT translation of the game), all rights about the client files go to [@guuji](https://twitter.com/guuji).
- I am not the creator of any of the files in the `helpers` folder, but I have modified some of them a little.