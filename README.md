# apeflac2mp3
Bulk convert APE, FLAC files with or without cue file to mp3.

## Usage

First modify config.ini to specify the location of ffmpeg.

Convert a directory of APE/FLAC's to mp3's:

    python apeflac2mp3.py source_dir dest_dir
    
If it finds CUE files in source_dir, it will use them to split APE/FLAC, otherwise it will convert one APE/FLAC to one mp3 file.

You can also specify one CUE file or one music file as input.
