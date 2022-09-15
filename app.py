from bokeh.embed import server_document
from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def home():
    night_reward_script = server_document('http://127.0.0.1:5006/night_reward')
    footprint_script = server_document('http://127.0.0.1:5006/footprint')
    visit_script = server_document('http://127.0.0.1:5006/visit')

    html = render_template(
        'index.html',
        night_reward_script=night_reward_script,
        footprint_script=footprint_script,
        visit_script=visit_script
    )
    return html


if __name__ == '__main__':
    app.run()
