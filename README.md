# roblox custom image & gif loader

a "cool" (if you even consider it cool lol) project i made for fun that lets you render any image or gif directly onto parts in roblox. instead of using decals or uploading images, it reads raw binary data and draws the image pixel by pixel using wireframehandleadornments. 

## whats in this repo
- `converter.py` - the python script to convert images/gifs into the binary data
- `WireframeRenderer` - the roblox module that actually draws the image
- `ImageExampleWithATool.rbxl` - a roblox place file with the auto render setup and a sign tool so you can see how it all works

## features
- renders images and gifs in 3d space
- supports all 6 faces (front, back, top, etc)
- automatically stops rendering when you look away to save fps
- packs data into chunks so it bypasses roblox string limits
- comes with a classic ui tool to paste data in game

## requirements
- python 3.8+
- `Pillow` library for python
- roblox studio

install the python lib if you havent already:
```bash
pip install Pillow
```

## how to use
1. run the python script (`converter.py`)
2. select an image or gif from your computer (or paste a url)
3. click "Export as .rbxmx", name it whatever you want and then save it
4. insert that .rbxmx file into roblox studio
5. put the ImageData folder inside a Part
6. if you're using the example place, just tag a Part with "ImageTarget" and the auto renderer will handle the rest. if youre using your own setup, you can just require the module and call WireframeRenderer.DrawFromFolder(Part, ImageDataFolder) from a LocalScript. since it uses wireframe adornments, it works on any part as long as it's visible to the client.

if you want to see how the roblox side is set up, just open the `ImageExampleWithATool.rbxl` file in studio. it has the auto renderer script in StarterPlayerScripts, the module in ReplicatedStorage, and a sign tool you can use to paste data in-game.

## how it works
the python script reads all the pixels, groups identical colors together, and packs them into a compact binary file. it then base64 encodes it and splits it into 190k chunks. the roblox client reads the buffer, maps the 2d coordinates to 3d vectors, and draws the lines.
