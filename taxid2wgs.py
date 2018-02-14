#!/usr/bin/env python3
"""
Collect and parse NCBI WGS project fasta files from a taxid

Download NCBI WGS fasta files gzipped and process them to generate
a single coherent fasta file.
"""

import argparse
import gzip
import http.client
import itertools
import os
import re
import sys
import threading
import time
from ftplib import FTP, error_temp, error_proto, error_reply

__version__ = '0.2.0'
__date__ = 'Feb 2018'

RETRY_TIMES = [0, 5, 15, 30, 60, 120]
EXCEPTS = (OSError, EOFError, error_temp, error_proto, error_reply)
FTP_SERVER = 'ftp.ncbi.nlm.nih.gov'
FSA_WGS_END = '.fsa_nt.gz'


def ansi(numcolor):
    """Return function that escapes text with ANSI color n."""
    return lambda txt: '\033[%dm%s\033[0m' % (numcolor, txt)


# pylint: disable=invalid-name
gray, red, green, yellow, blue, magenta, cyan, white = map(ansi, range(90, 98))
# pylint: enable=invalid-name

RESUME_INFO = ' '.join([
    blue('NOTE:'), gray('You can try to solve any issue and resume'), '\n\t',
    gray('the process using the'), '-r/--resume', gray(' flag.')])


def download_file(ftp, filename):
    """Download file while keeping FTP connection alive."""

    def bkg_download():
        """ Aux method to download file in background"""
        with open(filename, 'wb') as file:
            ftp.voidcmd('TYPE I')  # Binary transfer mode
            sckt = ftp.transfercmd('RETR ' + filename)
            while True:
                chunk = sckt.recv(2 ** 25)  # bufsize as a power of 2 (32 MB)
                if not chunk:
                    break
                file.write(chunk)
            sckt.close()

    thrd = threading.Thread(target=bkg_download())
    thrd.start()
    while thrd.is_alive():
        thrd.join(30)  # Seconds to wait to send NOOPs while downloading
        ftp.voidcmd('NOOP')


def main():
    """Main entry point to the script."""
    # Argument Parser Configuration
    parser = argparse.ArgumentParser(
        description='Collect NCBI WGS project fasta files from a taxid',
        epilog='%(prog)s -- {}'.format(__date__),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # shortcut
    parser.add_argument(
        '-d', '--download',
        action='store_true',
        help='Just download (not parse) the WGS project files'
    )
    parser.add_argument(
        '-e', '--reverse',
        action='store_true',
        help='Reversed (alphabetical) order for processing projects'
    )
    mode = parser.add_mutually_exclusive_group(required=False)
    mode.add_argument(
        '-f', '--force',
        action='store_true',
        help='Force downloading and recreating the final FASTA file in '
             'spite of any previous run. This will clear temporal and output '
             'files but not previous downloads.'
    )
    mode.add_argument(
        '-r', '--resume',
        action='store_true',
        help='Resume downloading without checking '
             'the server for every project'
    )
    parser.add_argument(
        '-t', '--taxid',
        action='store',
        metavar='TAXID', type=str,
        default='548681',  # Herpesvirus as test taxid
        help='NCBI taxid code to include a taxon and all underneath.'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='enable verbose mode'
    )
    parser.add_argument(
        '-V', '--version',
        action='version',
        version='%(prog)s release {} ({})'.format(__version__, __date__)
    )
    parser.add_argument(
        '-x', '--exclude',
        action='store',
        metavar='TAXID', type=str,
        default='',
        help='NCBI taxid code to exclude a taxon and all underneath.'
    )

    # Parse arguments
    args = parser.parse_args()
    just_download = args.download
    force = args.force
    resume = args.resume
    reverse = args.reverse
    taxid = args.taxid
    exclude = args.exclude

    def vprint(*a, **k):
        """Print only if verbose mode is enabled"""
        if args.verbose:
            print(*a, **k, flush=True)

    # Program header
    print('\n=-= {} =-= v{} =-= {} =-=\n'.format(
        sys.argv[0], __version__, __date__))

    # Set output and temporal filenames
    if exclude:
        fstfile = 'WGS4taxid' + taxid + '-' + exclude + '.fa'
        tmpfile = 'WGS4taxid' + taxid + '-' + exclude + '.tmp'
    else:
        fstfile = 'WGS4taxid' + taxid + '.fa'
        tmpfile = 'WGS4taxid' + taxid + '.tmp'

    # Get lists of previously downloaded and parsed files
    previous = [entry.name for entry in os.scandir() if entry.is_file()
                and entry.name.endswith(FSA_WGS_END)]
    parsed = []
    if os.path.exists(tmpfile):
        if force:
            os.remove(tmpfile)
        elif just_download:
            parsed = [proj.rstrip() for proj in open(tmpfile)]
        elif resume:
            parsed = [proj.rstrip() for proj in open(tmpfile)]
            if parsed and not os.path.isfile(fstfile):
                print(red(' ERROR!'), gray('Temp file'), tmpfile,
                      gray('exists but not the corresponding FASTA file'),
                      fstfile, gray('\nPlease correct this or run with '
                      'force flag enabled.'))
                exit(1)
        else:
            print(red(' ERROR!'), gray('Temp file'), tmpfile,
                  gray('exists but resume flag not set.\nPlease correct this '
                       'or run with download, resume or force flag.'))
            exit(2)
    elif os.path.exists(fstfile):
        if force:
            os.remove(fstfile)
        else:
            print(red(' ERROR!'), gray('FASTA file'), fstfile,
                  gray('exists (but temporal file missing).\nPlease correct '
                       'this or run with force flag enabled.'))
            exit(3)
    # Display some info
    if force:
        vprint(blue('INFO:'), gray('All cleared by flag'), yellow('force'))
    if just_download:
        vprint(blue('INFO:'), gray('"Just download" mode enabled.'))
    if reverse:
        vprint(blue('INFO:'), gray('Reversed mode enabled.'))
    if resume or (just_download and not force):
        print(len(previous), gray('WGS project files are in current dir. '
                                  'If any, we won\'t look for them.'))
        print(len(parsed), gray('WGS projects already parsed. '
                                'If any, we will ignore them.'))

    # Get WGS project list from taxid and exclude
    conn = http.client.HTTPSConnection('www.ncbi.nlm.nih.gov')
    conn.request(
        'GET', r'/blast/BDB2EZ/taxid2wgs.cgi?INCLUDE_TAXIDS=' + taxid +
               r'&EXCLUDE_TAXIDS=' + exclude
    )
    response = conn.getresponse()
    vprint(gray('NCBI server response result:'),
           response.status, response.reason)
    data = response.read()
    wgs_projects_raw = data.replace(b'WGS_VDB://',
                                    b'').rstrip().decode().split('\n')
    wgs_projects = [proj for proj in wgs_projects_raw if proj not in parsed]
    if not wgs_projects:
        print(gray('No projects to process!'), green('All done!'))
        exit(0)
    # There are projects to process. Go ahead!
    wgs_projects.sort(reverse=reverse)
    exclude_txt = (gray(' excluding tid') + exclude) if exclude else ''
    print(len(wgs_projects), gray('WGS projects to collect for tid'), taxid,
          exclude_txt, flush=True)
    basedir = '/sra/wgs_aux/'
    # Append to fasta file (main output) and temporal file (projects done)
    if just_download:
        fstfile = tmpfile = '/dev/null'  # Don't touch the real files
    with open(fstfile, 'a') as wgs, open(tmpfile, 'a') as tmp:
        processed = len(parsed)
        progress = itertools.cycle(r'-\|/')
        # Looping for projects in the WGS projects to process
        for proj in wgs_projects:
            ftp = None
            downloaded = []
            to_download = []
            skipped = True
            if resume:
                downloaded = [f for f in previous if f.startswith(proj)]
                if downloaded:
                    vprint(gray('Project'), proj, gray('in disk. Skipping...'))
                    to_download = downloaded
            if not downloaded:
                vprint('\033[90m{} of {}: Process WGS \033[0m{}\033[90m '
                       'project...\033[0m'.format(processed + 1,
                                                  len(wgs_projects), proj),
                       end='')
                filenames = []
                error = None
                for retry_time in RETRY_TIMES:
                    if retry_time:
                        print(gray(' Retrying in %s seconds...' % retry_time),
                              end='', flush=True)
                    time.sleep(retry_time)
                    try:
                        ftp = FTP(FTP_SERVER, timeout=30)
                        ftp.set_debuglevel(0)
                        ftp.login()
                        ftp.cwd(os.path.join(basedir, proj[0:2],
                                             proj[2:4], proj))
                        filenames = ftp.nlst()
                    except EXCEPTS as err:
                        print(yellow(' PROBLEM!'), end='')
                        error = err
                    except KeyboardInterrupt:
                        print(gray(' User'), yellow('interrupted!'))
                        print(RESUME_INFO)
                        exit(9)
                    else:
                        break
                else:  # Too many problems, quit
                    print(red(' FAILED!'),
                          gray('Exceeded number of attempts!'))
                    print('\033[90mError message:\033[0m', error)
                    print(RESUME_INFO)
                    exit(5)
                to_download = [f for f in filenames if f.endswith(FSA_WGS_END)]
            # Looping for files in the WGS project
            for filename in to_download:
                # Check for already downloaded
                if not force and os.path.isfile(filename):
                    vprint(gray('[%s already downloaded]' % filename), end=' ')
                else:
                    error = None
                    for retry_time in RETRY_TIMES:
                        if retry_time:
                            print(gray('\n Retrying in %s seconds...')
                                  % retry_time, end='')
                            sys.stdout.flush()
                        time.sleep(retry_time)
                        try:
                            if retry_time:
                                ftp = FTP(FTP_SERVER, timeout=30)
                                ftp.login()
                                ftp.cwd(os.path.join(basedir, proj[0:2],
                                                     proj[2:4], proj))
                            download_file(ftp, filename)
                            # ftp.retrbinary('RETR ' + filename,
                            #                open(filename, 'wb').write)
                        except EXCEPTS as err:
                            print(yellow(' PROBLEM!'), end='')
                            error = err
                        except KeyboardInterrupt:
                            print(gray(' User'), yellow('interrupted!'))
                            print(RESUME_INFO)
                            try:  # Avoid keeping in disk a corrupt file
                                os.remove(filename)
                            except OSError:
                                pass
                            exit(9)
                        else:
                            break
                    else:  # Too many problems, quit
                        try:  # Avoid keeping in disk a corrupt file
                            os.remove(filename)
                        except OSError:
                            pass
                        print(red(' FAILED!'),
                              gray('Exceeded number of attempts!'))
                        print(gray('Error message:'), error)
                        print(RESUME_INFO)
                        exit(5)
                    skipped = False
                # Decompress, parse and update headers if needed
                if just_download:
                    continue  # Avoid further processing
                with gzip.open(filename, 'rt') as filegz:
                    all_lines = []
                    try:
                        all_lines = filegz.readlines()
                        if not all_lines:
                            raise EOFError
                    except EOFError:
                        print('\n\033[91m FAILED!\033[90m Unexpected EOF '
                              'while parsing file \033[0m{}\033[90m. '
                              'Is it corrupted?\033[0m'.format(filename))
                        print(RESUME_INFO)
                        exit(4)
                    line1 = all_lines[0]
                    # Check fasta-read header format
                    if proj in line1[0:7]:  # New format: just save all
                        wgs.writelines(all_lines)
                    else:  # Old format: parse the headers
                        pattern = re.compile(r'(%s(?:\d){5,8}\.\d)\|([\w\W]*)$'
                                             % proj)
                        match = re.search(pattern, line1)
                        accession = match.group(1)
                        description = match.group(2).strip()
                        wgs.write('>%s %s\n' % (accession, description))
                        try:
                            for line in all_lines:
                                if line[0] != '>':  # Sequence line
                                    wgs.write(line)
                                else:  # Header line to parse
                                    match = re.search(pattern, line)
                                    accession = match.group(1)
                                    description = match.group(2).strip()
                                    wgs.write('>%s %s\n'
                                              % (accession, description))
                        except EOFError:
                            print('\n\033[91m FAILED!\033[90m Unexpected EOF '
                                  'while parsing file \033[0m{}\033[90m. '
                                  'Is it corrupted?\033[0m'.format(filename))
                            print(RESUME_INFO)
                            exit(3)
            # Project is done: update temporal file and console output
            if ftp:
                try:
                    ftp.quit()
                except EXCEPTS:
                    try:
                        ftp.close()
                    except EXCEPTS:
                        pass
            tmp.write(proj + '\n')
            tmp.flush()
            processed += 1
            vprint(green(' OK!'))
            if not args.verbose:
                if processed % 1 == 0:
                    print('\r\033[95m{}\033[0m [{:.2%}]\033[90m'.format(
                        next(progress), processed / len(wgs_projects_raw)),
                        end='')
                    if skipped:
                        print(' Skipping download. Parsing...\033[0m', end='')
                    elif just_download:
                        print(' Just downloading...\033[0m          ', end='')
                    else:
                        print(' Downloading and parsing...\033[0m   ', end='')
            sys.stdout.flush()
    if just_download:
        print(green('All downloaded!'))
    else:
        print(green('All OK!'))
        try:  # Remove temporal file. Not needed anymore.
            os.remove(tmpfile)
        except OSError:
            print('\033[93m WARNING!\033[90m Failed to remove temporal file '
                  '\033[0m{}\033[90m!\033[0m'.format(tmpfile))
            exit(5)


if __name__ == '__main__':
    main()
