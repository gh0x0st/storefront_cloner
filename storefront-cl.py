#!/usr/bin/python3

import os           # https://docs.python.org/3/library/os.html
import sys          # https://docs.python.org/3/library/sys.html
import argparse     # https://docs.python.org/3/library/argparse.html
import subprocess   # https://docs.python.org/3/library/subprocess.html
import pathlib      # https://docs.python.org/3/library/pathlib.html
import socket       # https://docs.python.org/3/library/socket.html
import ipaddress    # https://docs.python.org/3/library/ipaddress.html


def banner():
    banner = '''
        >> Citrix StoreFront Cloner
        >> https://www.github.com/gh0x0st
    '''
    print(banner)


def create_phantom_script(phantom_path):
    phantom_script = '''
var page = require('webpage').create(),
  system = require('system'), address;

address = system.args[1];
page.scrollPosition= { top: 4000, left: 0}
page.open(address, function(status) {
  if (status !== 'success') {
    console.log('** Error loading url.');
  } else {
    console.log(page.content);
  }
  phantom.exit();
});
'''
    with open(phantom_path, 'w') as file:
        file.write(phantom_script)


def build_page(index_path, target_url, phantom_path):
    print(f"[*] Building out {target_url}")
    with open(index_path, "wb") as out:
        subprocess.Popen(["phantomjs", "build.js", target_url],
                         stdout=out,
                         stderr=subprocess.PIPE,
                         universal_newlines=True).communicate()
    os.remove(phantom_path)


def clean_page(index_path, target_url, action_url):
    print(f'[*] Fixing known conflicts on public pages')
    with open(index_path, 'r') as file:
        filedata = file.read()

    print('[*] Resolving root-relative links to absolute links')
    filedata = filedata.replace('href="/', 'href="'+target_url+'/')
    filedata = filedata.replace('src="/', 'src="'+target_url+'/')

    print('[*] Cleaning up unnecessary data')
    filedata = filedata.replace('ResourceManager("',
                                'ResourceManager("'+target_url)
    filedata = filedata.replace('/cgi/login', action_url)

    with open(index_path, 'w') as file:
        file.write(filedata)

    purge_strings = ['/vpn/js/rdx.js',
                     'TypeError: ']

    with open(index_path, "r") as f:
        lines = f.readlines()

    with open(index_path, "w") as f:
        for line in lines:
            if not any(purge_string in line for purge_string in purge_strings):
                f.write(line)

    print(f'[*] File saved to {index_path}')


def main():
    banner()
    # build the parser
    parser = argparse.ArgumentParser(description='A python approach to clone Citrix Storefront \
        portals for use in security awareness exercises.')

    # build arguments
    parser.add_argument('-a', '--action-url',
                        action='store',
                        type=str,
                        dest='action_url',
                        help='Path to php page for form post action')
    parser.add_argument('-t', '--target-url',
                        action='store',
                        type=str,
                        dest='target_url',
                        help='URL to Storefront page to clone')

    # cycle through argument input
    args = parser.parse_args()

    # print help and exit if no parameters are given
    if len(sys.argv) == 1:
        parser.print_help()
        example_text = '''\nexamples:
        python3 storefront-cl.py -t https://real.example.com -a '/post.php'
        '''
        print(example_text)
        sys.exit(1)

    # Write files in current working directory
    phantom_path = os.path.join(os.getcwd(), 'build.js')
    index_path = os.path.join(os.getcwd(), 'index.html')

    # Build variables from input
    action_url = args.action_url
    target_url = args.target_url

    # Get Target IP - public or private
    target_basename = os.path.basename(target_url)
    target_ip = socket.gethostbyname(target_basename)
    target_presence = ipaddress.ip_address(target_ip).is_private

    if target_presence is True:
        print('[!] This utility can only clone public facing \
         Citrix Storefront Portals.')
        sys.exit(1)

    # Check if phantomjs exists - exit if not
    file = pathlib.Path("/usr/bin/phantomjs")
    if file.exists():
        create_phantom_script(phantom_path)
        build_page(index_path, target_url, phantom_path)
        clean_page(index_path, target_url, action_url)
    else:
        print("PhantomJS is required to capture javascript generated html.\
         You can install using 'sudo apt install phantomjs'")
        sys.exit(1)


if __name__ == '__main__':
    main()
