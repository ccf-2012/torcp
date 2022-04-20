import os
import time
import shutil
import argparse


def dropEmptyFolders(directory):
    """Verify that every empty folder removed in local storage."""
    for diritem in os.listdir(directory):
        isEmpty = True
        dirpath = os.path.join(directory, diritem)
        for dir, dirs, files in os.walk(dirpath):
            if not dirs and not files:
                print('\033[33mDelete empty folder: %s\033[0m ' % dir)
                if not ARGS.dryrun:
                    if ARGS.sleep:
                        time.sleep(ARGS.sleep)
                    os.rmdir(dir)
            for fn in files:
                fullfilepath = os.path.join(dir, fn)
                filename, fileext = os.path.splitext(fn)
                if fileext.lower() in KEEPEXTS:
                    print('\033[32mNot Empty: %s\033[0m ' % fullfilepath)
                    isEmpty = False
                else:
                    if os.path.isfile(fullfilepath):
                        print('\033[33mDelete file: %s\033[0m ' % fullfilepath)
                        if not ARGS.dryrun:
                            if ARGS.sleep:
                                time.sleep(ARGS.sleep)
                            os.remove(fullfilepath)
        if isEmpty and os.path.isdir(dirpath):
            print('\033[31mrmtree: %s\033[0m ' % dirpath)
            if not ARGS.dryrun:
                if ARGS.sleep:
                    time.sleep(ARGS.sleep)
                shutil.rmtree(dirpath)
                # passs


def dropEmptyFolers2(directory):
    folders = list(os.walk(directory))[1:]

    for folder in folders:
        # folder example: ('FOLDER/3', [], ['file'])
        if not folder[2]:
            os.rmdir(folder[0])

def makeKeepExts():
    global KEEPEXTS
    KEEPEXTS = ['.mkv', '.mp4', '.ts', '.iso']
    if ARGS.keep_ext:
        argExts = ARGS.keep_ext.split(',')
        for ext in argExts:
            ext = ext.strip()
            if ext:
                if ext[0] == '.':
                    KEEPEXTS.append(ext)
                else:
                    KEEPEXTS.append('.' + ext)

def loadArgs():
    parser = argparse.ArgumentParser(
        description=
        'DeleteEmptyFolders: The script scan folders in FOLDER and delete if the sub-folders are empty.'
    )
    parser.add_argument('FOLDER', help='The directory to be scaned.')
    parser.add_argument('-e',
                        '--keep-ext',
                        help='folders will be delete if files lefted with extention not in (\'srt,ass\').')
    parser.add_argument('--sleep',
                        type=int,
                        help='sleep x seconds after operation.')
    parser.add_argument('--dryrun',
                        action='store_true',
                        help='print message instead of real delete.')

    global ARGS
    ARGS = parser.parse_args()
    ARGS.FOLDER = os.path.expanduser(ARGS.FOLDER)
    makeKeepExts()

def main():
    loadArgs()
    dropEmptyFolders(ARGS.FOLDER)


if __name__ == '__main__':
    main()
