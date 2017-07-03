# coding: utf-8

import sys
import os
import platform
if sys.version_info[0] != 3:
    exit("Only Python 3 supported")
from configparser import ConfigParser

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


def parse_cue(cue_file):
    """
    from:https://gist.github.com/bancek/b37b780292540ed2d17d
    parse cue file and return the ffmpeg cmd list
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
        #cmd += ' "%.2d.mp3"' % (track['track'])
        cmd += ' "%.2d-%s-%s.mp3"' % (track['track'],
                                      track['artist'].replace(":", "-"),
                                      track['title'].replace(":", "-"))
    
        cmds.append(cmd)

    return cmds


def process_cue(incue, outdir):
    cmds = parse_cue(sys.argv[1])
    for cmd in cmds:
        print(cmd)
        os.system(cmd)


def process_onefile(infile, outdir):
    filename = os.path.basename(infile)
    name, ext = os.path.splitext(filename)
    cmd = '%s -i "%s"' % (ffmpeg_path, infile)
    cmd += ' "%s.mp3"' % os.path.join(outdir, name)
    print(cmd)
    os.system(cmd)


def process_dir(indir, outdir):
    raise NotImplementedError



if "__main__" == __name__:
    indirfile = sys.argv[1]
    if len(sys.argv) > 2:
        outdir = sys.argv[2]
        os.makedirs(outdir, exist_ok=True)
    else:
        outdir = ""

    if os.path.isdir(indirfile):
        process_dir(indirfile, outdir)
    elif indirfile.endswith(".cue"):
        process_cue(indirfile, outdir)
    else:
        process_onefile(indirfile, outdir)
