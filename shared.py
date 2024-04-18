from pathlib import Path

from shiny import ui

app_dir = Path(__file__).parent


# Helper function to restrict width of content
def restrict_width(*args, sm=None, md=None, lg=None, pad_y=5, **kwargs):
    cls = "mx-auto"
    if sm:
        cls += f" col-sm-{sm}"
    if md:
        cls += f" col-md-{md}"
    if lg:
        cls += f" col-lg-{lg}"

    return ui.div(*args, {"class": cls}, {"class": f"py-{pad_y}"}, **kwargs)

