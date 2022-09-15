# Vera Rubin Observatory Pre Night Briefing app

## Setup
1. Create and activate new virtual environment. Run `python -m venv venv && source venv/bin/activate`
2. Install the requirements Run `pip install -r requirements.txt`
3. Make sure that `rubin_sim` files are installed locally. Run `rs_download_data`
4. Update `plotting/settings.py` to point to the relevant files on your filesystem

## Running

The project consists of two separate processes, a Bokeh server, and a Flask server.

The Bokeh server is responsible for generating and caching all the plots and delivering them to the flask application on demand, while the Flask server is responsible for rendering the website and other web related activities and data calculations.

To run the project, both servers must be started:

1. Start the Bokeh server. From the project root run `bash scripts/start_bokeh.sh`
2. In another terminal start the Flask server. From the project root run `python -m flask --debug run`

## Update deps

To update requirements or make changes. Make the changes required to `requirements.in`, and then run `pip-compile requirements.in > requirements.txt` to regenerate the `requirements.txt` file.
