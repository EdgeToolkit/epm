import sys

from epm.command import main, api_main


def run():
    main(sys.argv[1:])


def api_run():
    api_main(sys.argv[1:])


if __name__ == '__main__':
    run()
