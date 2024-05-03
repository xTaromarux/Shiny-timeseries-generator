from palmerpenguins import load_penguins
from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_widget  
from pathlib import Path
from shared import restrict_width
import pandas as pd
import seaborn as sns
import matplotlib
import functools
import plotly.express as px

from timeseries_generator import (
    Generator,
    HolidayFactor,
    LinearTrend,
    RandomFeatureFactor,
    WeekdayFactor,
    WhiteNoise,
)
from timeseries_generator.external_factors import (
    CountryGdpFactor,
    EUIndustryProductFactor,
)


penguins = load_penguins()
app_dir = Path(__file__).parent
df = pd.read_csv(app_dir / "GDP_per_capita_countries.csv")
unique_values = df.iloc[:, 0].unique()
first_column_header = df.columns[0]
feature_dict = {}
factor_list = []
plot = reactive.value(pd.DataFrame())
update_state = reactive.value(False)
holiday_factor_instance = reactive.value()

app_ui = ui.page_sidebar(
    ui.sidebar(

        ui.div(
            ui.input_numeric(
                "base_amount_input", 
                "Input a base amount", 
                1000, min=0, max=100000000000000000000),  

            ui.h6(
                {"class": "fw-bold"},
                "Input features"),
                    
            ui.div(
                ui.input_checkbox(
                    "features_from_csv_checkbox",
                    first_column_header.split()[0].lower(),
                    False),
                    
                id="div_for_data_from_csv",
            ),

            # ui.div(
            #     ui.input_checkbox(
            #         "more_features_checkbox", 
            #         "add more feature(s)", 
            #         False),
                
            #     id="div_for_more_features",
            # ),
        ),
        
        ui.accordion(
            ui.accordion_panel(
                "Select factor for each feature",
                ui.div(
                    # ui.input_checkbox(
                    #     "checkbox_factor_for_more_features",
                    #     "Product".lower(),
                    #     False),
                    # ui.input_selectize(  
                    #     "selectize_with_factor_options_for_more_features",  
                    #     "select factor for [product]",  
                    #     ["random_factor", "country_factor", "line_factor"],  
                    #     multiple=True
                    # ),
                    
                    id="div_for_factors_section",
                ),
            ),
            ui.accordion_panel(
                "Add other factor",
                ui.div(
                    id = "holiday_factor_scale_div"
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
                        "eu_economics_factor_checkbox", 
                        "Add EU economics factor", 
                        False),

                    ui.input_slider(
                        "eu_economics_factor_slider", 
                        "", 
                        1, 20, 10),
                ),
                
                ui.input_checkbox(
                    "random_noise_checkbox", 
                    "Add random noise", 
                    False),
                    ),
            
            
            id="acc_items", 
            multiple=True
        ),
        
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
                end="2020-12-31",
                width="100%"),  
            
            id="div_for_features_to_aggregate",
            class_="col-md-78 col-lg-78 py-4 mx-auto"
        ),
        
        ui.div(
            ui.h5(
                "Generated time series data",
                class_= "fw-bold"
            ), 
            
            ui.input_selectize(  
                "selectize_with_all_active_features",  
                "Choose features to aggregate",  
                [],
                width="100%",  
                multiple=True
            ),
            output_widget("hist", width="100%"),
            
            ui.output_data_frame("generator"),
            
            class_="col-md-78 col-lg-78 py-4 mx-auto"
        ),
        
        
        sm=10,
        md=10,
        lg=8,
    ),
)

def server(input, output, session):
    
    def generatorDataFrame():
        base_amount = input.base_amount_input()
        start_date = input.daterange()[0]
        end_date= input.daterange()[1]
        
        g: Generator = Generator(
        factors=set(factor_list),
        features=feature_dict,
        date_range=pd.date_range(start_date, end_date),
        base_value=base_amount,
        )
        newVal = g.generate()
        plot.set(newVal)
    
    def objects_with_data_from_csv():
        result = {}
        for index, value in enumerate(unique_values):
            result.update({value : value})
        return result
 
    def update_data():
        result = not(update_state.get())
        update_state.set(result)

    def default_factors():   
        factor_list.clear()
        
        random_noise_checkbox = input.random_noise_checkbox()
        if random_noise_checkbox:   
            factor_list.append(WhiteNoise())   
            
        eu_economics_factor_checkbox = input.eu_economics_factor_checkbox()
        eu_economics_factor_slider = input.eu_economics_factor_slider()
        if eu_economics_factor_checkbox:   
            factor_list.append(EUIndustryProductFactor(intensive_scale=eu_economics_factor_slider))         
                        
        weekend_factor_scale_checkbox = input.weekend_factor_scale_checkbox()
        weekend_factor_scale_slider = input.weekend_factor_scale_slider()
        if weekend_factor_scale_checkbox:   
            factor_list.append(WeekdayFactor(intensity_scale=weekend_factor_scale_slider))  
       
    def holiday_factor():
        holiday_factor_scale_checkbox = input.holiday_factor_scale_checkbox()
        holiday_factor_scale_slider = input.holiday_factor_scale_slider()
        if holiday_factor_scale_checkbox:   
            if first_column_header.split()[0].lower() in feature_dict:
                holiday_factor_instance.set(HolidayFactor(
                    country_list=feature_dict[first_column_header.split()[0].lower()], 
                    country_feature_name = first_column_header.split()[0].lower(),
                    holiday_factor=holiday_factor_scale_slider
                ))
            else:
                holiday_factor_instance.set(HolidayFactor(
                country_list=["Netherlands"], 
                country_feature_name = first_column_header.split()[0].lower(),
                holiday_factor=holiday_factor_scale_slider
            ))
            factor_list.append(holiday_factor_instance.get())                  
    
    def option_selectize_with_factor():
        option_selectize_with_factor = input.selectize_with_factor_options_from_csv()
        for factor in option_selectize_with_factor:
            if factor == 'line_factor':
                for feat_val in feature_dict[first_column_header.split()[0].lower()]:
                    coef = input.linear_slope_of_feature_from_csv()
                    feat_val_linear_trend_dict = {}
                    feat_val_linear_trend_dict[feat_val] = {
                        "coef": coef,
                        "offset": 0,
                    }
                factor_list.append(LinearTrend(
                        feature=first_column_header.split()[0].lower(),
                        feature_values=feat_val_linear_trend_dict,
                        col_name=f"lin_trend_{first_column_header.split()[0].lower()}",
                    ))
                
            if factor == 'random_factor':
                factor_list.append(RandomFeatureFactor(
                        feature=first_column_header.split()[0].lower(),
                        feature_values=feature_dict[first_column_header.split()[0].lower()],
                        col_name=f"random_feature_factor_{first_column_header.split()[0].lower()}",
                    ))
                
            if factor == 'country_factor':
                factor_list.append(CountryGdpFactor(country_list=feature_dict[first_column_header.split()[0].lower()]))            

    def input_linear_slope_of_feature_from_csv():
        options_from_selectize = input.selectize_with_factor_options_from_csv()
        if 'line_factor' in options_from_selectize:
                ui.remove_ui("#inserted_input_linear_slope_of_feature_from_csv")

                input_linear_slope_of_feature_from_csv = ui.input_numeric(
                            "linear_slope_of_feature_from_csv", 
                            "Linear slope of "+first_column_header.split()[0].lower(), 
                            1, min=0, max=100000000000000000000),
                ui.insert_ui(
                    ui.div({"id": "inserted_input_linear_slope_of_feature_from_csv"}, input_linear_slope_of_feature_from_csv),
                    selector="#div_for_factors_section",
                    where="beforeEnd",
                )
        else:
            ui.remove_ui("#inserted_input_linear_slope_of_feature_from_csv")

    @reactive.effect 
    @reactive.event(input.weekend_factor_scale_checkbox,
                    input.eu_economics_factor_checkbox,
                    input.random_noise_checkbox,
                    input.weekend_factor_scale_slider,
                    input.eu_economics_factor_slider,
                    ignore_init=False,
                    ignore_none=False)      
    def _():
        default_factors()
        update_data()
    
    @reactive.effect 
    @reactive.event(input.holiday_factor_scale_checkbox,
                    input.holiday_factor_scale_slider,
                    input.weekend_factor_scale_checkbox,
                    input.eu_economics_factor_checkbox,
                    input.random_noise_checkbox,
                    input.weekend_factor_scale_slider,
                    input.eu_economics_factor_slider,
                    ignore_init=False,
                    ignore_none=False)      
    def _():
        default_factors()
        holiday_factor()
        update_data()
    
    @reactive.effect 
    @reactive.event(input.selectize_with_factor_options_from_csv,
                    ignore_init=False,
                    ignore_none=False)      
    def _():
        input_linear_slope_of_feature_from_csv()
        update_data()
     
    @reactive.effect 
    @reactive.event(input.weekend_factor_scale_checkbox,
                    input.eu_economics_factor_checkbox,
                    input.random_noise_checkbox,
                    input.weekend_factor_scale_slider,
                    input.eu_economics_factor_slider,
                    input.selectize_with_factor_options_from_csv,
                    input.holiday_factor_scale_checkbox,
                    input.holiday_factor_scale_slider,
                    ignore_init=False,
                    ignore_none=False)      
    def _():
        default_factors()
        holiday_factor()
        option_selectize_with_factor()   
        update_data()
        
    @reactive.effect 
    @reactive.event(input.weekend_factor_scale_checkbox,
                    input.eu_economics_factor_checkbox,
                    input.random_noise_checkbox,
                    input.weekend_factor_scale_slider,
                    input.eu_economics_factor_slider,
                    input.selectize_with_factor_options_from_csv,
                    input.holiday_factor_scale_checkbox,
                    input.holiday_factor_scale_slider,
                    input.linear_slope_of_feature_from_csv,
                    ignore_init=False,
                    ignore_none=False)      
    async def _():
        default_factors()
        holiday_factor()
        option_selectize_with_factor()   
        update_data()

    @render_widget 
    @reactive.event(input.features_from_csv_checkbox,
                    input.selectize_with_all_active_features,
                    input.base_amount_input,
                    update_state,
                    ignore_init=False,
                    ignore_none=False)
    def hist():
        selectize_with_all_active_features = list(input.selectize_with_all_active_features())
        generatorDataFrame()
        DF_SALE = plot.get()
        if len(selectize_with_all_active_features) >= 1:
            print(selectize_with_all_active_features)
            group_feat_l = selectize_with_all_active_features.copy()
            group_feat_l.insert(0, "date")
            DF_VIS = DF_SALE.groupby(group_feat_l)["value"].sum().reset_index()
        else:
            DF_VIS = DF_SALE
            
        if "date" in DF_VIS.columns and "value" in DF_VIS.columns:
            DF_PLOT = DF_VIS[["date", "value"]]

        if len(selectize_with_all_active_features) > 0:
            color_col = "-".join(selectize_with_all_active_features)
            DF_PLOT[color_col] = functools.reduce(
                lambda x, y: x + "-" + y, (DF_VIS[feat] for feat in selectize_with_all_active_features)
            )
            base = px.line(DF_PLOT, x="date", y="value", color=color_col)

        else:
            base = px.line(DF_PLOT, x="date", y="value")
        return base 
        
    @render.data_frame
    @reactive.event(input.features_from_csv_checkbox,
                    input.selectize_with_all_active_features,
                    input.base_amount_input,
                    update_state,
                    ignore_init=False,
                    ignore_none=False)
    def generator():
        return plot.get()

    @reactive.effect
    @reactive.event(input.features_from_csv_checkbox,
                    ignore_init=False,
                    ignore_none=False)
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
            input.holiday_factor_scale_checkbox.value = False
            factor_list.remove(holiday_factor_instance.get())   

            ui.remove_ui("#inserted_input_selectize_with_data_from_csv")     
            ui.remove_ui("#inserted_input_linear_slope_of_feature_from_csv")
            ui.remove_ui("#inserted_selectize_with_factor_options_from_csv")
            ui.remove_ui("#inserted_checkbox_factor_for_features_from_csv")
            ui.remove_ui("#inserted_holiday_factor_scale_checkbox")
            ui.remove_ui("#inserted_holiday_factor_scale_slider")

            ui.update_selectize(
                "selectize_with_all_active_features",
                choices=[],
                selected=[],
                server=False,
                ) 
            
    @reactive.effect
    @reactive.event(input.selectize_with_options_from_csv)
    def _():
        selectize_with_options_from_csv = input.selectize_with_options_from_csv()
        if len(selectize_with_options_from_csv) >= 1:
            feature_dict[first_column_header.split()[0].lower()] = selectize_with_options_from_csv
                    
            holiday_factor_scale_checkbox = ui.input_checkbox(
                        "holiday_factor_scale_checkbox", 
                        "Holiday factor scale", 
                        False),
            holiday_factor_scale_slider = ui.input_slider(
                        "holiday_factor_scale_slider", 
                        "", 
                        1, 10, 2),
            checkbox_factor_for_features_from_csv = ui.input_checkbox(
                        "checkbox_factor_for_features_from_csv",
                        first_column_header.split()[0].lower(),
                        False),
            
            ui.insert_ui(
                ui.div({"id": "inserted_holiday_factor_scale_checkbox"}, holiday_factor_scale_checkbox),
                selector="#holiday_factor_scale_div",
                where="beforeBegin",
            )
            ui.insert_ui(
                ui.div({"id": "inserted_holiday_factor_scale_slider"}, holiday_factor_scale_slider),
                selector="#holiday_factor_scale_div",
                where="beforeBegin",
            )
            ui.insert_ui(
                ui.div({"id": "inserted_checkbox_factor_for_features_from_csv"}, checkbox_factor_for_features_from_csv),
                selector="#div_for_factors_section",
                where="beforeBegin",
            )
            
            ui.update_selectize(
                "selectize_with_all_active_features",
                choices=[],
                selected=[],
                server=False,
                )
            ui.update_selectize(
                "selectize_with_all_active_features",
                choices=[first_column_header.split()[0].lower()],
                selected=[first_column_header.split()[0].lower()],
                server=False,
                )    
        else:
            input.holiday_factor_scale_checkbox.value = False
            factor_list.remove(holiday_factor_instance.get())   

            ui.remove_ui("#inserted_input_linear_slope_of_feature_from_csv")
            ui.remove_ui("#inserted_selectize_with_factor_options_from_csv")
            ui.remove_ui("#inserted_checkbox_factor_for_features_from_csv")
            ui.remove_ui("#inserted_holiday_factor_scale_checkbox")
            ui.remove_ui("#inserted_holiday_factor_scale_slider")

            ui.update_selectize(
                "selectize_with_all_active_features",
                choices=[],
                selected=[],
                server=False,
                ) 
            
    @reactive.effect
    @reactive.event(input.checkbox_factor_for_features_from_csv)
    def _():
        checkbox_factor_for_features_from_csv = input.checkbox_factor_for_features_from_csv()
        
        if checkbox_factor_for_features_from_csv:
            selectize_with_factor_options_from_csv = ui.input_selectize(  
                        "selectize_with_factor_options_from_csv",  
                        "select factor for ["+first_column_header.split()[0].lower()+"]",  
                        ["random_factor", "country_factor", "line_factor"],  
                        multiple=True
                    ),
            ui.insert_ui(
                ui.div({"id": "inserted_selectize_with_factor_options_from_csv"}, selectize_with_factor_options_from_csv),
                selector="#div_for_factors_section",
                where="beforeEnd",
            )
        else:
            ui.remove_ui("#inserted_selectize_with_factor_options_from_csv")
            ui.remove_ui("#inserted_input_linear_slope_of_feature_from_csv")

    def generate_value_for_feature_list():
        input_with_more_features = input.input_feature_list()
        result=[]
        for i in range(3):
            result.append(input_with_more_features + "_" + str(i))
        return result
    
    @reactive.effect
    @reactive.event(input.input_feature_list)
    def _():
        input_with_more_features = input.input_feature_list()
        input_result = ""
        if input_with_more_features:
            result = generate_value_for_feature_list()
            for i, feature in enumerate(result):
                if i < len(result) - 1:
                    input_result += feature + ", "
                else:
                    input_result += feature
                    
            ui.update_text("input_value_of_feature_list", value=input_result)
    
    @reactive.effect
    def _():
        more_features_checkbox = input.more_features_checkbox()
        
        if more_features_checkbox:
            input_with_more_features = ui.input_text(
            "input_feature_list", 
            "Input feature list (must separate by comma)", 
            "product"),
            input_with_value_of_more_features = ui.input_text(
            "input_value_of_feature_list", 
            "Input values of feature ["+  +"] (must separate by comma)", 
            "product_0,product_1,product_2"),
            ui.insert_ui(
                ui.div({"id": "inserted_input_with_more_features"}, input_with_more_features),
                selector="#div_for_more_features",
                where="beforeEnd",
            )
            ui.insert_ui(
                ui.div({"id": "inserted_input_with_value_of_more_features"}, input_with_value_of_more_features),
                selector="#div_for_more_features",
                where="beforeEnd",
            )
        else:
            ui.remove_ui("#inserted_input_with_more_features")
            ui.remove_ui("#inserted_input_with_value_of_more_features")
            
    
    def out_out():
        list_of_more_features = input.Input_feature_list().split(",")
        for index in range(len(list_of_more_features)):
            feature = list_of_more_features[index]
            return str(feature)        
    
    # @reactive.effect
    def _():
        more_features_checkbox = input.more_features_checkbox()
        if more_features_checkbox:            
            input_values_of_feature = ui.input_text(
            f"Input_values_of_feature_", 
            f"Input values of feature {out_out()} (must separate by comma)", 
            "product"),
            ui.insert_ui(
                ui.div({"id": f"Input_values_of_feature_"}, input_values_of_feature),
                selector="#div_for_more_features",
                where="beforeEnd",
            )
        else:
            ui.remove_ui(f"#Input_values_of_feature_")     
     
    
app = App(app_ui, server)