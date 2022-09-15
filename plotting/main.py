from concurrent.futures import ThreadPoolExecutor

from bokeh.model import Model
from bokeh.models import Div
from bokeh.server.server import Server
from tornado.ioloop import IOLoop

from plotting.night_reward import generate_night_rewards_plot
from plotting.footprint import generate_footprint_plot
from plotting.visits import generate_visit_plot

worker_pool = ThreadPoolExecutor(4)
figure_cache = dict()

NIGHT_REWARD_PLOT = 'night_reward'
FOOTPRINT_PLOT = 'footprint'
VISIT_PLOT = 'visit'

plots = {
    NIGHT_REWARD_PLOT: generate_night_rewards_plot,
    FOOTPRINT_PLOT: generate_footprint_plot,
    VISIT_PLOT: generate_visit_plot
}


def _set_fig(name, generator):
    figure_cache[name] = generator()


def generate_plots():
    for name, generator in plots.items():
        # Clear the old plot from the cache
        if name in figure_cache:
            del figure_cache[name]

        # Generate the new plot asynchronously
        worker_pool.submit(_set_fig, name, generator)


def reset_figure_document(figure):
    # See https://stackoverflow.com/a/67047128
    for model in figure.select({'type': Model}):
        prev_doc = model.document
        model._document = None
        if prev_doc:
            try:
                prev_doc.remove_root(model)
            except RuntimeError:
                pass


def render_figure(name, doc):
    # Check if the plot has been generated or not
    if name in figure_cache:
        # Make sure that the previous document has been removed from the figure
        reset_figure_document(figure_cache[name])
        # Add the plot to the document
        doc.add_root(figure_cache[name])
    else:
        # Mention that the figure is still being generated
        doc.add_root(Div(text=f"The {name} figure is being generated, please reload the page shortly..."))


def night_reward(doc):
    render_figure(NIGHT_REWARD_PLOT, doc)


def footprint(doc):
    render_figure(FOOTPRINT_PLOT, doc)


def visit(doc):
    render_figure(VISIT_PLOT, doc)


# Generate all initial plots asynchronously
worker_pool.submit(generate_plots)

# Start the bokeh server
server = Server(
    {
        '/night_reward': night_reward,
        '/footprint': footprint,
        '/visit': visit
    },
    io_loop=IOLoop(),
    allow_websocket_origin=["127.0.0.1:5000"]
)
server.start()
server.io_loop.start()
