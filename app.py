from concurrent.futures import ThreadPoolExecutor

from bokeh.embed import server_document
from flask import Flask, render_template

from lib.astronomical_events import generate_astronomical_events

app = Flask(__name__)
worker_pool = ThreadPoolExecutor(4)
astronomical_events = None


def _set_astronomical_events():
    global astronomical_events
    astronomical_events = generate_astronomical_events()


# Generate the astronomical events
worker_pool.submit(_set_astronomical_events)


@app.route('/')
def home():
    night_reward_script = server_document('http://127.0.0.1:5006/night_reward')
    footprint_script = server_document('http://127.0.0.1:5006/footprint')
    visit_script = server_document('http://127.0.0.1:5006/visit')

    html = render_template(
        'index.html',
        night_reward_script=night_reward_script,
        footprint_script=footprint_script,
        visit_script=visit_script,
        astronomical_events=astronomical_events
    )
    return html


if __name__ == '__main__':
    app.run()
