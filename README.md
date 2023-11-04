# BDSP-Auto-Repacker

This program is intended to make development for BDSP easier and quicker.

## How does it work?

While running this program, the `scripts/` and `AssetFolder/` are constantly monitored for filechanges.

If a file change is registered, the program will run the repacker if there are no further changes for 10 seconds.

When no more filechanges were registered for 10 seconds, a repack job will be started that automatically repacks the scripts and the assets.

Afterwards, the repacked files from `EditedAssets/` and `bin/ev_script` will be moved into your chosen mod folder.

What files are updated and the wait before starting a repack can be changed in the script itself.

## Requirements

Run `pip install -r requirements.txt` to download the required python libraries.

You need a working folder structure of the two projects below.

-   [Aldo's BDSP Repacker](https://github.com/Ai0796/BDSP-Repacker)
-   [z80Rotom's ev-as](https://github.com/z80rotom/ev-as)

This script needs the following folder structure:

-   bsdp_auto_repacker.py
-   Repack.exe OR Repack.py
-   Unpack.exe OR Unpack.py
-   src/
    -   ev_as.exe OR ev_as.py
    -   ev_parse.exe OR ev_parse.py
-   EditedAssets/
-   scripts/

You also need to include all of the structure both of these tools require. See their repos for additional information

## Usage

-   Run `bdsp_auto_repacker.py`
-   Go through the setup on first launch
-   Enjoy the automation
