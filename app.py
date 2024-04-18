import plotly.express as px
from palmerpenguins import load_penguins
from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_widget  
from pathlib import Path
from shared import restrict_width

import pandas as pd
import seaborn as sns

penguins = load_penguins()
app_dir = Path(__file__).parent
df = pd.read_csv(app_dir / "GDP_per_capita_countries.csv")
unique_values = df.iloc[:, 0].unique()
first_column_header = df.columns[0]

app_ui = ui.page_sidebar(
    ui.sidebar(


        ui.input_numeric(
            "base_amount", 
            "Input a base amount", 
            1000, min=0, max=100000000000000000000),  

        ui.h6(
            {"class": "fw-bold"},
            "Input features"),
        
                ui.hr(),
        
        ui.div(
            ui.input_checkbox(
                "features_from_csv_checkbox",
                first_column_header.split()[0],
                False),
                
            id="div_for_data_from_csv",
        ),

        ui.div(
            ui.input_checkbox(
                "more_features_checkbox", 
                "Add more feature(s)", 
                False),
            
            id="div_for_more_features",
        ),

        ui.h6(
            {"class": "fw-bold"},
            "Select factor for each feature"),
        
        ui.div(
            ui.input_checkbox(
                "holiday_factor_scale_checkbox", 
                "Holiday factor scale", 
                False),

            ui.input_slider(
                "holiday_factor_scale_slider", 
                "", 
                1, 10, 1),
        ),
        
        ui.div(
            ui.input_checkbox(
                "weekend_factor_scale_checkbox", 
                "Weekend factor scale", 
                False),

            ui.input_slider(
                "weekend_factor_scale_slider", 
                "", 
                1, 10, 1),
        ),
        
        ui.div(
            ui.input_checkbox(
                "EU_economics_factor_checkbox", 
                "Add EU economics factor", 
                False),

            ui.input_slider(
                "EU_economics_factor_slider", 
                "", 
                1, 20, 10),
        ),
        
        ui.input_checkbox(
            "random_noise_checkbox", 
            "Add random noise", 
            False),

        width=300
    ),

    restrict_width(
        ui.h1(
            "Shiny Time Series Syntheic Data Generator",
            class_="text-lg-center text-left fw-bold",
        ),
        
        ui.div(
            ui.h5(
                "Input start date and end date",
                class_= "fw-bold"
                ),
            ui.input_date_range(
                "daterange", 
                "From date", 
                start="2020-01-01",
                width="100%"),  
            
            id="div_for_features_to_aggregate",
            class_="col-md-78 col-lg-78 py-4 mx-auto"
        ),
        
        ui.div(
            ui.h5(
                "Generated time series data",
                class_= "fw-bold"
                ), 
            
            class_="col-md-78 col-lg-78 py-4 mx-auto"
        ),
        
        sm=10,
        md=10,
        lg=8,
    ),
    ui.output_plot("hist"),
)

def server(input, output, session):

    def objects_with_data_from_csv():
        result = {}
        for index, value in enumerate(unique_values):
            result.update({"Row"+str(index) : value})
        return result

    @reactive.effect
    def _():
        features_from_csv_checkbox = input.features_from_csv_checkbox()

        if features_from_csv_checkbox:
            input_with_data_from_csv = ui.input_selectize(  
                "selectize_with_options_from_csv",  
                "Choose "+first_column_header.split()[0],  
                objects_with_data_from_csv(),  
                multiple=True
            ),
            ui.insert_ui(
                ui.div({"id": "inserted_input_selectize_with_data_from_csv"}, input_with_data_from_csv),
                selector="#div_for_data_from_csv",
                where="beforeEnd",
            )
        else:
            ui.remove_ui("#inserted_input_selectize_with_data_from_csv")

    @reactive.effect
    def _():
        more_features_checkbox = input.more_features_checkbox()
        
        if more_features_checkbox:
            input_with_more_features = ui.input_text(
            "Input_feature_list", 
            "Input feature list (must separate by comma)", 
            "product"),
            ui.insert_ui(
                ui.div({"id": "inserted_input_with_more_features"}, input_with_more_features),
                selector="#div_for_more_features",
                where="beforeEnd",
            )
        else:
            ui.remove_ui("#inserted_input_with_more_features")
            
    @render_widget  
    def plot():  
        scatterplot = px.histogram(
            data_frame=penguins,
            x="body_mass_g",
            nbins=input.n(),
        ).update_layout(
            title={"text": "Penguin Mass", "x": 0.5},
            yaxis_title="Count",
            xaxis_title="Body Mass (g)",
        )

        return scatterplot  
    
    @render.plot
    def hist():
        hue = "species" if input.species() else None
        sns.kdeplot(df, x=input.var(), hue=hue)
        if input.show_rug():
            sns.rugplot(df, x=input.var(), hue=hue, color="black", alpha=0.25)

app = App(app_ui, server)