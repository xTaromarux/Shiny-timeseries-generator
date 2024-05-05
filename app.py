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
update_state_for_data_from_csv = reactive.value(False)
update_state_for_more_features = reactive.value(False)
holiday_factor_instance = reactive.value()
addition_features = reactive.value(["product"])
all_available_features = reactive.value([])

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

            ui.div(
                ui.input_checkbox(
                    "additional_features_checkbox", 
                    "add more feature(s)", 
                    False),
                
                id="div_for_additional_features",
            ),
        ),
        
        ui.accordion(
            ui.accordion_panel(
                "Select factor for each feature",
                ui.div(
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
 
    def update_data_from_csv():
        result = not(update_state_for_data_from_csv.get())
        update_state_for_data_from_csv.set(result)

    def update_more_features():
        result = not(update_state_for_more_features.get())
        update_state_for_more_features.set(result)

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
     
    def generate_value_for_feature_list(addition_features):
        result=[]
        for i in range(3):
            result.append(addition_features + "_" + str(i))
        return result         
    
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
        update_data_from_csv()
    
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
        update_data_from_csv()
    
    @reactive.effect 
    @reactive.event(input.selectize_with_factor_options_from_csv,
                    ignore_init=False,
                    ignore_none=False)      
    def _():
        options_from_selectize = input.selectize_with_factor_options_from_csv()
        if 'line_factor' in options_from_selectize:
                ui.remove_ui("#inserted_input_linear_slope_of_feature_from_csv")

                input_linear_slope_of_feature_from_csv = ui.input_numeric(
                            "linear_slope_of_feature_from_csv", 
                            "Linear slope of "+first_column_header.split()[0].lower(), 
                            1, min=0, max=100000000000000000000),
                ui.insert_ui(
                    ui.div({"id": "inserted_input_linear_slope_of_feature_from_csv"}, input_linear_slope_of_feature_from_csv),
                    selector="#inserted_selectize_with_factor_options_from_csv",
                    where="beforeEnd",
                )
        else:
            ui.remove_ui("#inserted_input_linear_slope_of_feature_from_csv")
        update_data_from_csv()
     
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
        update_data_from_csv()
        
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
        update_data_from_csv()

    @render_widget 
    @reactive.event(input.features_from_csv_checkbox,
                    input.selectize_with_all_active_features,
                    input.base_amount_input,
                    update_state_for_data_from_csv,
                    update_state_for_more_features,
                    ignore_init=False,
                    ignore_none=False)
    def hist():
        selectize_with_all_active_features = list(input.selectize_with_all_active_features())
        generatorDataFrame()
        DF_SALE = plot.get()
        if len(selectize_with_all_active_features) >= 1:
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
                    update_state_for_data_from_csv,
                    update_state_for_more_features,
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
            ui.remove_ui("#inserted_input_selectize_with_data_from_csv")     
            ui.remove_ui("#inserted_input_linear_slope_of_feature_from_csv")
            ui.remove_ui("#inserted_selectize_with_factor_options_from_csv")
            ui.remove_ui("#inserted_checkbox_factor_for_features_from_csv")
            ui.remove_ui("#inserted_holiday_factor_scale_checkbox")
            ui.remove_ui("#inserted_holiday_factor_scale_slider")
            all_active_features = list(input.selectize_with_all_active_features())
            if len(all_active_features) >= 1:
                all_active_features.remove(first_column_header.split()[0].lower())
            ui.update_selectize(
                "selectize_with_all_active_features",
                choices=all_available_features.get(),
                selected=all_active_features,
                server=False,
                ) 
        
            input.holiday_factor_scale_checkbox.value = False
            if holiday_factor_instance.get() in factor_list:
                factor_list.remove(holiday_factor_instance.get())  
            
    @reactive.effect
    @reactive.event(input.selectize_with_options_from_csv)
    def _():
        selectize_with_options_from_csv = input.selectize_with_options_from_csv()
        if len(selectize_with_options_from_csv) == 1:
            ui.remove_ui("#inserted_selectize_with_factor_options_from_csv")
            ui.remove_ui("#inserted_input_linear_slope_of_feature_from_csv")
            ui.remove_ui("#inserted_holiday_factor_scale_checkbox")
            ui.remove_ui("#inserted_holiday_factor_scale_slider")
            
            feature_dict[first_column_header.split()[0].lower()] = selectize_with_options_from_csv
                    
            holiday_factor_scale_checkbox = ui.input_checkbox(
                        "holiday_factor_scale_checkbox", 
                        "Holiday factor scale", 
                        False),
            holiday_factor_scale_slider = ui.input_slider(
                        "holiday_factor_scale_slider", 
                        "", 
                        1, 10, 2),
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
            
            all_active_features = list(input.selectize_with_all_active_features())
            all_active_features.append(first_column_header.split()[0].lower())
            all_available_features.set(all_available_features.get() + [first_column_header.split()[0].lower()])
            ui.update_selectize(
                "selectize_with_all_active_features",
                choices=all_available_features.get(),
                selected=all_active_features,
                server=False,
                )    
        elif len(selectize_with_options_from_csv) < 1:
            ui.remove_ui("#inserted_selectize_with_factor_options_from_csv")
            ui.remove_ui("#inserted_input_linear_slope_of_feature_from_csv")
            ui.remove_ui("#inserted_holiday_factor_scale_checkbox")
            ui.remove_ui("#inserted_holiday_factor_scale_slider")

            all_active_features = list(input.selectize_with_all_active_features())
            if first_column_header.split()[0].lower() in all_active_features:
                all_active_features.remove(first_column_header.split()[0].lower())
            ui.update_selectize(
                "selectize_with_all_active_features",
                choices=all_available_features.get(),
                selected=all_active_features,
                server=False,
                ) 
            
            input.holiday_factor_scale_checkbox.value = False
            if holiday_factor_instance.get() in factor_list:
                factor_list.remove(holiday_factor_instance.get()) 
            
        else:   
            feature_dict[first_column_header.split()[0].lower()] = selectize_with_options_from_csv
            update_data_from_csv()

    @reactive.effect
    @reactive.event(input.additional_features_checkbox)
    def _():
        additional_features_checkbox = input.additional_features_checkbox()
        
        if additional_features_checkbox:
            feature_list = ""
            
            all_active_features = list(input.selectize_with_all_active_features())
 
            for addition_feature in addition_features.get():
                feature_list += addition_feature + ", "
                all_active_features.append(addition_feature)
                
            all_available_features.set(all_available_features.get () + addition_features.get())
            ui.update_selectize(
                "selectize_with_all_active_features",
                choices=all_available_features.get(),
                selected=all_active_features,
                server=False,
                ) 
            
            input_with_additional_features = ui.input_text(
                "input_feature_list", 
                "Input feature list (must separate by comma)", 
                feature_list[:-2]
                ),
            ui.insert_ui(
                    ui.div({"id": "inserted_input_with_additional_features"}, input_with_additional_features),
                    selector="#div_for_additional_features",
                    where="beforeEnd",
                )
        else:
            all_active_features = list(input.selectize_with_all_active_features())
            for addition_feature in addition_features.get():
                if len(all_active_features) >= 1:
                    all_active_features.remove(addition_feature)
            ui.update_selectize(
                "selectize_with_all_active_features",
                choices=all_available_features.get(),
                selected=all_active_features,
                server=False,
                ) 
            
            ui.remove_ui("#inserted_input_with_additional_features")

    @reactive.effect
    @reactive.event(input.additional_features_checkbox)
    def _():
        additional_features_checkbox = input.additional_features_checkbox()
        
        for i, addition_feature in enumerate(addition_features.get()):
            
            input_result = ""
            result = generate_value_for_feature_list(addition_feature)
            for j, feature in enumerate(result):
                if j < len(result) - 1:
                    input_result += feature + ", "
                else:
                    input_result += feature
            
            if additional_features_checkbox:
            
                input_with_value_of_additional_features = ui.input_text(
                "input_value_of_additional_feature_v"+str(i), 
                "Input values of feature ["+addition_feature+"] (must separate by comma)",
                input_result 
                ),
                selectize_with_factor_options_for_additional_features = ui.input_selectize(  
                        "selectize_with_factor_options_for_additional_feature_v"+str(i),  
                        "select factor for ["+addition_feature+"]",  
                        ["random_factor", "country_factor", "line_factor"],  
                        multiple=True
                    ),
            
                ui.insert_ui(
                    ui.div({"id": "inserted_selectize_with_factor_options_for_additional_feature_v"+str(i)}, selectize_with_factor_options_for_additional_features),
                    selector="#div_for_factors_section",
                    where="beforeEnd",
                )
                ui.insert_ui(
                    ui.div({"id": "inserted_input_with_value_of_additional_feature_v"+str(i)}, input_with_value_of_additional_features),
                    selector="#div_for_additional_features",
                    where="beforeEnd",
                )
        
            else:
                ui.remove_ui("#inserted_selectize_with_factor_options_for_additional_feature_v"+str(i))
                ui.remove_ui("#inserted_input_with_value_of_additional_feature_v"+str(i))
                ui.remove_ui("#inserted_input_linear_slope_of_feature_for_additional_feature_v"+str(i)) 


    @reactive.effect
    @reactive.event(input.input_feature_list)
    def _():
        input_with_additional_features = input.input_feature_list()
        
        if input_with_additional_features:
            list_of_additional_features = input_with_additional_features.replace(" ", "").split(",")
            
            all_active_features_temp = list(input.selectize_with_all_active_features())
            all_active_features = []
            
            if first_column_header.split()[0].lower() in all_active_features_temp:
                all_active_features.append(first_column_header.split()[0].lower())
 
            for addition_feature in list_of_additional_features:
                all_active_features.append(addition_feature)
                
            all_available_features.set(all_active_features)
            ui.update_selectize(
                "selectize_with_all_active_features",
                choices=all_available_features.get(),
                selected=all_active_features,
                server=False,
            )
            

            
            for i, addition_feature in enumerate(addition_features.get()):
                ui.remove_ui("#inserted_input_with_value_of_additional_feature_v"+str(i))
                ui.remove_ui("#inserted_selectize_with_factor_options_for_additional_feature_v"+str(i))

            addition_features.set(list_of_additional_features)
            for i, addition_feature in enumerate(addition_features.get()):
                
                input_result = ""
                result = generate_value_for_feature_list(str(addition_feature))
                feature_dict[addition_feature] = result
                
                for j, feature in enumerate(result):
                    if j < len(result) - 1:
                        input_result += feature + ", "
                    else:
                        input_result += feature
                                
                input_with_value_of_additional_features = ui.input_text(
                    "input_value_of_additional_feature_v"+str(i), 
                    "Input values of feature ["+addition_feature+"] (must separate by comma)",
                    input_result 
                    ),
                selectize_with_factor_options_for_additional_features = ui.input_selectize(  
                        "selectize_with_factor_options_for_additional_feature_v"+str(i),  
                        "select factor for ["+addition_feature+"]",  
                        ["random_factor", "country_factor", "line_factor"],  
                        multiple=True
                    ),
            
                ui.insert_ui(
                    ui.div({"id": "inserted_selectize_with_factor_options_for_additional_feature_v"+str(i)}, selectize_with_factor_options_for_additional_features),
                    selector="#div_for_factors_section",
                    where="beforeEnd",
                )
                ui.insert_ui(
                    ui.div({"id": "inserted_input_with_value_of_additional_feature_v"+str(i)}, input_with_value_of_additional_features),
                    selector="#div_for_additional_features",
                    where="beforeEnd",
                )  
            update_more_features()  
    
    @reactive.effect      
    def _():
        for i, addition_feature in enumerate(addition_features.get()):
            options_from_selectize = input["selectize_with_factor_options_for_additional_feature_v"+str(i)]()
            if 'line_factor' in options_from_selectize:
                    ui.remove_ui("#inserted_input_linear_slope_of_feature_for_additional_feature_v"+str(i))

                    input_linear_slope_of_feature_for_additional_feature = ui.input_numeric(
                                "input_linear_slope_of_feature_for_additional_feature_v"+str(i), 
                                "Linear slope of "+addition_feature, 
                                1, min=0, max=100000000000000000000),
                    ui.insert_ui(
                        ui.div({"id": "inserted_input_linear_slope_of_feature_for_additional_feature_v"+str(i)}, input_linear_slope_of_feature_for_additional_feature),
                        selector="#inserted_selectize_with_factor_options_for_additional_feature_v"+str(i),
                        where="beforeEnd",
                    )
            else:
                ui.remove_ui("#inserted_input_linear_slope_of_feature_for_additional_feature_v"+str(i)) 

app = App(app_ui, server)