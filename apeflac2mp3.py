# coding: utf-8

import sys
import os
import platform
import argparse
from multiprocessing import cpu_count
from configparser import ConfigParser
from concurrent.futures import ProcessPoolExecutor

if sys.version_info[0] != 3:
    sys.exit("Only Python 3 is supported.")
system = platform.system()
if system == 'Windows':
    sname = 'win'
elif system == 'Darwin':
    sname = 'mac'
elif system == 'Linux':
    sname = 'linux'
else:
    sys.exit("Unknown sytem, can't continue.")

cfg = ConfigParser()
cfg.read(os.path.join(os.path.realpath(os.path.dirname(__file__)), 'config.ini'))

ffmpeg_path = cfg.get(sname, 'ffmpeg')
supported_exts = cfg.get('options', 'supported_exts').split(',')
use_multiprocessing = cfg.getboolean('options', 'multiprocessing')
# Ask for confirmation before process_dir()
prompt_to_continue = cfg.get('options', 'prompt_to_continue')
# ffmpeg args
bitrate = cfg.get('options', 'bitrate')
nostats = cfg.getboolean('options', 'nostats')


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
        if nostats:
            cmd += ' -nostats'
        cmd += ' -i "%s"' % os.path.join(cue_dir, current_file)
        cmd += ' -ss %.2d:%.2d:%.2d' % (int(track['start']) / 60 / 60,
                                        int(track['start']) / 60 % 60,
                                        int(track['start']) % 60)

        if 'duration' in track:
            cmd += ' -t %.2d:%.2d:%.2d' % (int(track['duration']) / 60 / 60,
                                           int(track['duration']) / 60 % 60,
                                           int(track['duration']) % 60)
        cmd += ' ' + ' '.join(
            '-metadata %s="%s"' % (k, v) for (k, v) in metadata.items())
        cmd += ' -ab %s' % bitrate
        cmd += ' ' + ' '.join('-metadata %s="%s"' % (k, v) for (k, v) in metadata.items())
        filename = '%.2d - %s.mp3' % (int(track['track']),
                                      # track['artist'].replace(":", "-"),
                                      track['title'].replace(":", "-"))
        cmd += ' "%s"' % os.path.join(outdir, filename)

        cmds.append(cmd)

    return cmds


def process_cue(incue, outdir):
    cmds = parse_cue(incue, outdir)
    if use_multiprocessing:
        with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
            for cmd in cmds:
                executor.submit(
                    os.system,
                    cmd
                )
    else:
        for cmd in cmds:
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


def validate_path(path, isdir_only=False):
    """
    Exit if the path is not a valid file or directory.
    """
    if isdir_only:
        if not os.path.isdir(path):
            print('Error: Invalid directory ' + path)
            sys.exit(1)
    else:
        if not os.path.isfile(path) and not os.path.isdir(path):
            print('Error: Invalid path ' + path)
            sys.exit(1)


def try_mkdir(directory):
    """
    Try os.mkdir and exit if it fails.
    """
    try:
        os.mkdir(directory)
    except PermissionError as e:
        print('%s is possibly an invalid directory.'
              '\nError message: ' + e)
        sys.exit(1)
    except Exception as e:
        print('Error while making %s: %s' % (directory, e))
        sys.exit(1)


def prompt_user(message):
    """
    Prompt user to continue the script or exit.
    """
    a = input('%s (y = yes) ' % str(message))
    if a == 'y' or a == 'Y':
        return
    sys.exit()


def process_dir(indir, outdir, same_dir=False):
    """
    Recursively go through directory.
    If it find cue files, it will process them.
    Otherwise it will convert files of known formats (supported_exts) to mp3.

    Creates subdirectories in the outdir unless same_dir is True.
    The subdirectories will have the same directory tree as the indir's.
    """
    basedir = os.path.basename(indir)

    if not same_dir:
        if not os.path.exists(outdir):
            try_mkdir(outdir)
        outbasedir = os.path.basename(outdir)
        if basedir != outbasedir:
            outdir = os.path.join(outdir, basedir)
        if not os.path.exists(outdir):
            try_mkdir(outdir)

    if prompt_to_continue:
        prompt_user('Output directory = %s\nContinue?' % outdir)
    current_outdir = outdir
    for root, dirs, files in os.walk(indir):
        if not same_dir:
            if os.path.basename(root) not in outdir:
                in_subtree = root.split(basedir)[1][1:]
                current_outdir = os.path.join(outdir, in_subtree)
            if not os.path.exists(current_outdir):
                os.mkdir(current_outdir)

        cues = [f for f in files if f.endswith('.cue')]
        if cues:
            for cue in cues:
                process_cue(os.path.join(root, cue), current_outdir)
        else:
            for f in files:
                name, ext = os.path.splitext(f)
                if ext in supported_exts:
                    process_onefile(os.path.join(root, f), current_outdir)


if __name__ == '__main__':
    se = supported_exts
    se.insert(len(supported_exts) - 1, 'and')
    se = ', '.join(se).replace('and,', 'and')
    parser = argparse.ArgumentParser(
        'apeflac2mp3.py',
        description='Splits .cue files and/or converts %s files to mp3. If '
                    'the input argument is a directory the output will have '
                    'the same subdirectory tree unless the -s flag is passed.'
                    % se
    )
    parser.add_argument('input', help='the directory or file to process')
    parser.add_argument('outdir', nargs='?', help='the output directory')
    parser.add_argument('-b', '--bitrate', dest='bitrate',
                        help='The bitrate of the mp3 files. Default = 320k')
    parser.add_argument('-s', '--samedir', dest='same_dir',
                        action='store_true',
                        help='put all output in one directory (outdir)')
    args = parser.parse_args()

    validate_path(args.input)

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
