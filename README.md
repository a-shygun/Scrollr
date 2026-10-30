# Scrollr

Scrollr is a local photo and video viewer. Set `DATA_ROOT` in `scrollr/settings.py` to your media folder. On startup, it adds new media files to the database; existing records are left unchanged. Files in subfolders use the first folder name as their category.

## Run locally

By default, Scrollr reads media from the repository's `data/` folder. To use another folder locally, set `DATA_ROOT` in a `.env` file at the project root:

```sh
DATA_ROOT=/absolute/path/to/your/media
```

Then run:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
./bin/scrollr
```

The app opens at <http://127.0.0.1:8000>. Run `python manage.py sync_library` after adding media so new files are added to the database. Favorites are stored locally in SQLite. Render's `DATA_ROOT` points to the bundled `/app/data` folder.
