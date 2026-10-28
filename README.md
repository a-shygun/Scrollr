# Scrollr

Scrollr is a calm, personal feed for the photos and videos you choose to keep. Browse a visual grid, or switch to the single-post stream for hands-free playback. Swipe left to like, swipe right to hide, and open any post for its details.

**Live app:** [scrollr.amirshygun.ir](https://scrollr.amirshygun.ir/)

## Your library

Scrollr uses the repository's `data/` folder as its default library, both locally and on the hosted app. The included demo media is indexed automatically. Put media in `data/` or organize it into subfolders; subfolder names become categories, while files directly in `data/` appear under **General**.

When running locally, use the **+** button to select another folder on that computer. This selection is saved in the ignored `.library_path` file and replaces the active library until you choose **Use demo library**. Hosted deployments always use the bundled `data/` library. Additional local media stays ignored by Git unless you explicitly add it to a deployment.

## Run locally

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
./bin/scrollr
```

Scrollr opens in your browser and indexes the active library on startup. After changing files in that library, refresh the index with:

```sh
DJANGO_DEBUG=true python manage.py sync_library
```

## Deploy

The included `render.yaml` configures deployment on Render. Create a Blueprint from this repository. Hosted runs use the bundled `data/` path; only media included in the deployed source is available to the hosted app. On Render's free plan, votes may reset when the service restarts or is redeployed.
