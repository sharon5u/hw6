"""Start the free public demo; local web_app.py behavior is unchanged."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def ensure_demo_store(seed, destination):
    if (destination / 'chroma.sqlite3').exists():
        return
    if not (seed / 'chroma.sqlite3').exists():
        raise RuntimeError('Seed database missing. Run python render_setup.py first.')
    temporary = destination.with_name(destination.name + '.initializing')
    if temporary.exists():
        shutil.rmtree(temporary)
    shutil.copytree(seed, temporary)
    if destination.exists():
        destination.rmdir()  # Only replace an empty directory.
    temporary.rename(destination)


def main():
    seed = ROOT / 'render_seed'
    if not (seed / 'chroma.sqlite3').exists():
        subprocess.run([sys.executable, str(ROOT / 'render_setup.py')], check=True)
    destination = ROOT / 'render_demo_store'
    ensure_demo_store(seed, destination)
    from web_app import create_server
    port = int(os.environ.get('PORT', '10000'))
    origin = os.environ.get('RENDER_EXTERNAL_URL', '').rstrip('/') or None
    server = create_server(port, destination, host='0.0.0.0', public_origin=origin, demo=True)
    print(f'Pantry Pal demo listening on 0.0.0.0:{port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
