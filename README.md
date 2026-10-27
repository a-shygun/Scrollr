# Yourstagram

Yourstagram is a small Django app for browsing a personal media library. It displays videos, GIFs, and photos as a feed, with search, category and media-type filters, and like/dislike buttons.

## Add your media

Your files can stay anywhere on your computer. In the app, click the **+** button and enter the path to the folder that contains your category folders and media files:

```text
data/
├── Family/
│   └── picnic.mp4
└── Travel/
    └── beach.jpg
```

Yourstagram indexes `.mp4`, `.m4v`, `.webm`, `.mov`, `.mkv`, `.avi`, `.gif`, `.jpg`, `.jpeg`, `.png`, and `.webp` files. The app remembers the folder path on this computer. Your media and folder path are not added to GitHub; you do not need to move your files into the project.

To show a few files on Render, put only files you are comfortable publishing in `demo_media/`. That folder is included in the GitHub project and used only for the online demo. The personal downloader and any link lists are separate from this app.

## Run locally

Install Python, then run these commands from the project folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
DJANGO_DEBUG=true python manage.py runserver 127.0.0.1:8080
```

Open <http://localhost:8080>, click **+**, and enter your media folder path. Click **Sync library** after adding or removing files to refresh the list.

On Ryan's Mac, the `yourstagram` shell command activates the virtual environment, starts Gunicorn, and opens the site in a browser.

## Deploy on Render

The `render.yaml` file contains the deployment settings. In Render, create a Blueprint from this GitHub repository. Render builds the app and starts Gunicorn; Nginx is not needed.

Render uses `demo_media/`, not the private local `data/` library. The free service uses temporary storage, so database votes can reset when Render restarts or redeploys.
