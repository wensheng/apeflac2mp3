# apeflac2mp3
Bulk convert APE, FLAC files with or without cue file to mp3.

## Usage

(Modify config.ini to change the location of ffmpeg.exe if you're on Windows.)

Convert a directory of APE/FLAC's to mp3's:

    python apeflac2mp3.py source_dir dest_dir
    
If it finds CUE files in source_dir, it will use them to split APE/FLAC, otherwise it will convert each APE/FLAC file to one mp3 file.

You can also specify one CUE file or one music file as input.

    python apeflac2mpe.py example1.cue
    python apeflac2mpe.py example2.flac
    
If you omit the dest_dir, it put output files in the current directory.
