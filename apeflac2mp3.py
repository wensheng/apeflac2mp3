# coding: utf-8

import sys
import os
import platform
import argparse
from configparser import ConfigParser

if sys.version_info[0] != 3:
    exit("Only Python 3 supported")
system = platform.system()
if system == 'Windows':
    sname = 'win'
elif system == 'Darwin':
    sname = 'mac'
elif system == 'Linux':
    sname = 'linux'
else:
    exit("Unknown sytem, can't continue")

cfg = ConfigParser()
cfg.read(os.path.join(os.path.realpath(os.path.dirname(__file__)), 'config.ini'))

ffmpeg_path = cfg.get(sname, "ffmpeg")
supported_exts = ("flac", "ape", "m4a", "oga")
# ffmpeg args
bitrate = cfg.get('options', 'bitrate')


def parse_cue(cue_file, outdir):
    """
    from:https://gist.github.com/bancek/b37b780292540ed2d17d
    Parse cue file and return the ffmpeg cmd list
    Note this assumes cue file and pointed FILE are always in the same directory
    """
    cue_dir = os.path.dirname(cue_file)
    d = open(cue_file).read().splitlines()
    
    general = {}
    tracks = []
    current_file = None
    
    for line in d:
        if line.startswith('REM GENRE '):
            general['genre'] = ' '.join(line.split(' ')[2:]).replace('"', '')
        if line.startswith('REM DATE '):
            general['date'] = ' '.join(line.split(' ')[2:])
        if line.startswith('PERFORMER '):
            general['artist'] = ' '.join(line.split(' ')[1:]).replace('"', '')
        if line.startswith('TITLE '):
            general['album'] = ' '.join(line.split(' ')[1:]).replace('"', '')
        if line.startswith('FILE '):
            current_file = ' '.join(line.split(' ')[1:-1]).replace('"', '')
        
        if line.startswith('  TRACK '):
            track = general.copy()
            track['track'] = int(line.strip().split(' ')[1], 10)
    
            tracks.append(track)
    
        if line.startswith('    TITLE '):
            tracks[-1]['title'] = ' '.join(line.strip().split(' ')[1:]).replace('"', '')
        if line.startswith('    PERFORMER '):
            tracks[-1]['artist'] = ' '.join(line.strip().split(' ')[1:]).replace('"', '')
        if line.startswith('    INDEX 01 '):
            #t = map(int, ' '.join(line.strip().split(' ')[2:]).replace('"', '').split(':'))
            t = [int(a) for a in ' '.join(line.strip().split(' ')[2:]).replace('"', '').split(':')]
            tracks[-1]['start'] = 60 * t[0] + t[1] + t[2] / 100.0
    
    for i in range(len(tracks)):
        if i != len(tracks) - 1:
            tracks[i]['duration'] = tracks[i + 1]['start'] - tracks[i]['start']
    
    cmds = []
    for track in tracks:
        metadata = {
            'artist': track['artist'],
            'title': track['title'],
            'album': track['album'],
            'track': str(track['track']) + '/' + str(len(tracks))
        }

        if 'genre' in track:
            metadata['genre'] = track['genre']
        if 'date' in track:
            metadata['date'] = track['date']
    
        cmd = ffmpeg_path
        cmd += ' -i "%s"' % os.path.join(cue_dir,current_file)
        cmd += ' -ss %.2d:%.2d:%.2d' % (track['start'] / 60 / 60, track['start'] / 60 % 60, int(track['start'] % 60))

        if 'duration' in track:
            cmd += ' -t %.2d:%.2d:%.2d' % (track['duration'] / 60 / 60, track['duration'] / 60 % 60, int(track['duration'] % 60))

        cmd += ' ' + ' '.join('-metadata %s="%s"' % (k, v) for (k, v) in metadata.items())
        cmd += ' -ab %s' % bitrate
        filename = '%s-%s-%.2d.mp3' % (track['artist'].replace(":", "-"),
                                       track['title'].replace(":", "-"),
                                       track['track'])
        cmd += ' "%s"' % os.path.join(outdir, filename)
    
        cmds.append(cmd)

    return cmds


def process_cue(incue, outdir):
    cmds = parse_cue(incue, outdir)
    for cmd in cmds:
        print(cmd)
        os.system(cmd)


def process_onefile(infile, outdir):
    """
    convert a single file to mp3
    """
    filename = os.path.basename(infile)
    name, ext = os.path.splitext(filename)
    cmd = '%s -i "%s"' % (ffmpeg_path, infile)
    cmd += ' "%s.mp3"' % os.path.join(outdir, name)
    print(cmd)
    os.system(cmd)


def process_dir(indir, outdir):
    """
    Recursively go through directory.
    If it find cue files, it will process them.
    Otherwise it will convert files of known formats (supported_exts) to mp3
    """
    for root, dirs, files in os.walk(indir):
        cues = [f for f in files if f.endswith(".cue")]
        if cues:
            for cue in cues:
                process_cue(os.path.join(root, cue), outdir)
        else:
            for f in files:
                name, ext = os.path.splitext(f)
                if ext in supported_exts:
                    process_onefile(os.path.join(root, f), outdir)


if "__main__" == __name__:
    se = supported_exts
    se.insert(len(supported_exts) - 1, 'and')
    se = ', '.join(se).replace('and,', 'and')
    parser = argparse.ArgumentParser(
        'apeflac2mp3.py'
    )
    parser.add_argument('input', help='the directory or file to process')
    parser.add_argument('outdir', nargs='?', help='the output directory')
    parser.add_argument('-b', '--bitrate', dest='bitrate',
                        help='The bitrate of the mp3 files. Default = 320k')
    args = parser.parse_args()

    if args.bitrate:
        minb = 65
        maxb = 640
        if not args.bitrate.endswith('k'):
            sys.exit('Invalid bitrate %s. Example of valid bitrate: 320k'
                     % args.bitrate)
        if not minb <= int(args.bitrate[:-1]) <= maxb:
            sys.exit('Bitrate must be at least %sk and at most %sk.'
                     % (minb, maxb))
        else:
            bitrate = args.bitrate

    if not args.outdir:
        args.outdir = os.getcwd()

    if os.path.isdir(args.input):
        process_dir(args.input, args.outdir, args.same_dir)
    elif args.input.endswith('.cue'):
        process_cue(args.input, args.outdir)
    else:
        process_onefile(args.input, args.outdir)
