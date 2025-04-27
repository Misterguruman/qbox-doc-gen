import argparse
import os
from lib.ResourceAnalyzer import Resource
import re

SUCCESS = '\u2705'  # Check mark
FAILURE = '\u274C'  # Cross mark

parser = argparse.ArgumentParser(description='Rename files in a directory.')
parser.add_argument('path', type=str, help='Path to the directory containing the files')
args = parser.parse_args()

def validate_args():
    if args.path == '.':
        args.path = os.getcwd()

    try:
        exists = os.path.exists(args.path)

    except (OSError, ValueError) as e:
        print(f'Error checking path: {e}')
        exit(1)

    if not os.path.exists(os.path.join(args.path, 'fxmanifest.lua')):
        print(f'{FAILURE} fxmanifest.lua found in the directory.')
        exit(1)

    print(f'Path: {args.path}')
    print(f'{SUCCESS} fxmanifest.lua found in the directory.')

if __name__ == '__main__':
    validate_args()

    resource = Resource(args.path)
    print(resource.manifest)


