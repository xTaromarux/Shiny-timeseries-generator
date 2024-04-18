from pathlib import Path

import pandas as pd
import seaborn as sns

from shiny import reactive
from shiny.express import input, render, ui
import plotly.express as px
from palmerpenguins import load_penguins
from shinywidgets import output_widget, render_widget 

sns.set_theme(style="white")
df = pd.read_csv(Path(__file__).parent / "penguins.csv", na_values="NA")
species = ["Adelie", "Gentoo", "Chinstrap"]

ui.page_opts(fillable=True)


def count_species(df, species):
    return df[df["Species"] == species].shape[0]


with ui.sidebar():
    ui.input_numeric("input_base_ammount", "Input a base amount", 1, min=1, max=10000)  
    ui.input_checkbox_group("species", "Input features", species, selected=species)
    ui.input_selectize(  
        "selectize",  
        f"Choose{species}",  
        {"1A": "Choice 1A", "1B": "Choice 1B", "1C": "Choice 1C"},  
        multiple=True,  
    ) 

    ui.input_slider("mass", "Mass", 2000, 6000, 3400)


@reactive.calc
def filtered_df() -> pd.DataFrame:
    filt_df = df[df["Species"].isin(input.species())]
    filt_df = filt_df.loc[filt_df["Body Mass (g)"] > input.mass()]
    return filt_df


with ui.layout_columns():
    with ui.div(class_="col-md-10 col-lg-8 py-5 mx-auto text-lg-center text-left"):
        ui.h3("How Does Regularization Strength Affect Coefficient Estimates?")


with ui.layout_columns():
    with ui.card():
        ui.card_header("AAAAAAA")

        @render.plot
        def length_depth():
            return sns.scatterplot(
                data=filtered_df(),
                x="Bill Length (mm)",
                y="Bill Depth (mm)",
                hue="Species",
            )
