# The Tower tourney results
- python3.12
- install dependencies: `pip install -r requirements.txt`

- `pip install -e .` to install the app,
- `pip install -e thetower` to install the django stuff,
- `pip install -e discord_bot` to install the discord bot,

- streamlit run with: `streamlit run components/pages.py`
- django admin run with: `cd thetower/dtower && DEBUG=true python manage.py runserver`

- `db.sqlite3` goes to `thetower/dtower` folder
- `uploads` csvs folder go to `thetower/dtower`:


## Testing
- `pytest`
