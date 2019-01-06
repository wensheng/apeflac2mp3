# apeflac2mp3
Bulk convert APE, FLAC files with or without cue file to mp3.

## Usage
(Modify config.ini to change the location of ffmpeg.exe if you're on Windows.)

Convert a directory of APE/FLAC's to mp3s:

    python apeflac2mp3.py input [dest_dir] [-b 192k] [-s]

### Arguments
* input: The directory or file to process
* dest_dir: The output directory
* -b bitrate: The bitrate argument passed to ffmpeg.
* -s: Put all output in the same directory. This is default if only a file is processed.

### Directory Input
If it finds CUE files in source_dir, it will use them to split APE/FLAC, otherwise it will convert each APE/FLAC file to one mp3 file. 

The output will have the same subdirectory tree as the input directory, unless the -s flag is passed.
For example:
```
$ python apeflac2mp3.py "D:/Downloads/Rick Astley" "D:/Music/Rick Astley"
...
Output #0, mp3, to 'D:/Music/Rick Astley/Whenever You Need Somebody/...:'
```
Using "D:/Music" as the dest_dir argument would also put it in "D:/Music/Rick Astley". 

If you omit the dest_dir, it puts output files in the current directory/InputDirName. If you omit the dest_dir and pass -s, it puts the output files in the current directory.

### File Input
You can also specify one CUE file or one music file as input.

    python apeflac2mpe.py example1.cue
    python apeflac2mpe.py example2.flac
    
If you omit the dest_dir, it puts output files in the current directory.

Note the name says ape and flac, but it can convert any audio formats (such as m4a, oga) as long as ffmpeg support them.
