# Matchgame-Dashboard

This is the source code for the master thesis: "Exploring the characteristics of learner activities in matching games in
different learning contexts"

## Running locally

Either run the application through system python:

```bash
pip install -r requirements.txt
python -m flask run
```

Or build and run the docker container:

```bash
./docker-build-run.sh
```

## Deploying on a server:

Change the ``server_url`` variable in ``config/dashboard_config.py`` to the desired value.
Also change the ``baseURL`` variable in ``static/js/pygal-custom-tooltips.js`` accordingly.

Then proceed as described in section ``Running locally``.