"""Serve API and compiled Flutter assets in one origin."""
import argparse
import logging
import os

import uvicorn

from backend.app.config import ROOT, Settings
from backend.app.main import create_app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--https', action='store_true')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    if args.https:
        os.environ['ATTENDANCE_ENVIRONMENT'] = 'evaluation'
        os.environ['ATTENDANCE_SECURE_COOKIES'] = 'true'
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    tls = {'ssl_certfile': str(ROOT / '.local/tls/localhost.pem'), 'ssl_keyfile': str(ROOT / '.local/tls/localhost.key')} if args.https else {}
    uvicorn.run(create_app(Settings.from_env()), host='127.0.0.1', port=args.port, access_log=False, **tls)


if __name__ == '__main__': main()
