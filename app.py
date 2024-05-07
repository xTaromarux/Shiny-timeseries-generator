from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_widget  
from random import randint
from pathlib import Path
from shared import restrict_width
import pandas as pd
import functools
import plotly.express as px
import datetime

from timeseries_generator.external_factors import EUIndustryProductFactor
from timeseries_generator import (
    Generator,
    LinearTrend,
    RandomFeatureFactor,
    WeekdayFactor,
    WhiteNoise,
)

app_dir = Path(__file__).parent
df = pd.read_csv(app_dir /"timeseries_generator"/"resources"/"public_data"/ "GDP_per_capita_countries.csv")
unique_values = df.iloc[:, 0].unique()
first_column_header = df.columns[0]
feature_dict = {}
factor_list = []
options_list_for_selectize_with_factors = ["random_factor", "line_factor"]
plot = reactive.value(pd.DataFrame())
update_state_for_data_from_csv = reactive.value(False)
update_state_for_more_features = reactive.value(False)
addition_features = reactive.value(["product"])
all_available_features = reactive.value([])
number_of_rows_for_dataframe = reactive.value(1)
number_of__all_rows = reactive.value()
update_dynamic_data = reactive.value("")

app_ui = ui.accordion(
            ui.accordion_panel(
                "Shiny Time Series Syntheic Data Generator",
                ui.page_sidebar(
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
                                open = False
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
                            ui.div(
                                ui.div(
                                    ui.div(
                                        ui.input_switch("show_dataframe_switch", "Show dataframe", False),
                                        class_="row justify-content-start align-items-end",
                                    ),
                                    ui.div(
                                        ui.download_button("download_button", "Download csv file", class_="btn-primary col-7"),
                                        class_=" row justify-content-start align-items-end",
                                    ),
                                    
                                    class_="justify-content-start align-items-end col pb-3"
                                ),  
                                id="data_frame_info_div",
                                width="100%",
                                class_="row py-5",
                            ),     
                                    
                            id="visualization_div",
                            class_="col-md-78 col-lg-78 py-4 mx-auto w-100"
                        ),
                        
                        sm=10,
                        md=10,
                        lg=8,
                    ),
                ),
                class_ = "bold"
            )
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
        number_of__all_rows.set(len(newVal.values))
    
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
    
    def options_for_selectize_with_factors(factor, option, linera_value):
        
        if factor == 'line_factor':
            feat_val_linear_trend_dict = {}
            for feat_val in feature_dict[option]:
                coef = linera_value
                feat_val_linear_trend_dict[feat_val] = {
                    "coef": coef,
                    "offset": 0,
                }
            factor_list.append(LinearTrend(
                    feature=option,
                    feature_values=feat_val_linear_trend_dict,
                    col_name=f"lin_trend_{option}",
                ))
                
        if factor == 'random_factor':
            factor_list.append(RandomFeatureFactor(
                    feature=option,
                    feature_values=feature_dict[option],
                    col_name=f"random_feature_factor_{option}",
                ))           

        default_factors()

    def add_options_with_factor_from_csv():
        option_selectize_with_factor_from_csv = input.selectize_with_factor_options_from_csv()
        selectize_with_options_from_csv = input.selectize_with_options_from_csv()
        additional_features_checkbox = input.additional_features_checkbox()
        features_from_csv_checkbox = input.features_from_csv_checkbox()

        liner_value = 1
        if "line_factor" in option_selectize_with_factor_from_csv:
            liner_value = input.linear_slope_of_feature_from_csv()
        
        if additional_features_checkbox:
            
            for i, addition_feature in enumerate(addition_features.get()):
                options_from_selectize = input["selectize_with_factor_options_for_additional_feature_v"+str(i)]()

                if len(option_selectize_with_factor_from_csv) > 0 and len(options_from_selectize) > 0:
                    ui.update_selectize(
                        "selectize_with_factor_options_for_additional_feature_v"+str(i),
                        choices=options_list_for_selectize_with_factors,
                        selected=[],
                        server=False,
                        ) 
                    
                if len(options_from_selectize) > 0:
                    for feat_val in feature_dict[addition_feature]:
                        factor_list.clear()
                        for factor in options_from_selectize:
                            options_for_selectize_with_factors(factor, addition_feature, liner_value)
                            update_data_from_csv()
                            
                else:
                    for feat_val in feature_dict[addition_feature]:
                        factor_list.clear()
                        for factor in option_selectize_with_factor_from_csv:
                            options_for_selectize_with_factors(factor, addition_feature, liner_value)
                            update_data_from_csv()
                        
        elif features_from_csv_checkbox and len(selectize_with_options_from_csv) >= 1:
            factor_list.clear()
            for factor in option_selectize_with_factor_from_csv:
                options_for_selectize_with_factors(factor, first_column_header.split()[0].lower(), liner_value)
                update_data_from_csv()
        else:
            factor_list.clear()
            default_factors()
            update_data_from_csv()
            
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
    @reactive.event(input.weekend_factor_scale_checkbox,
                    input.eu_economics_factor_checkbox,
                    input.random_noise_checkbox,
                    input.weekend_factor_scale_slider,
                    input.eu_economics_factor_slider,
                    input.selectize_with_factor_options_from_csv,
                    input.additional_features_checkbox,
                    ignore_init=False,
                    ignore_none=False)      
    def _():
        add_options_with_factor_from_csv()
        update_data_from_csv()
        
    @reactive.effect 
    @reactive.event(input.weekend_factor_scale_checkbox,
                    input.eu_economics_factor_checkbox,
                    input.random_noise_checkbox,
                    input.weekend_factor_scale_slider,
                    input.eu_economics_factor_slider,
                    input.selectize_with_factor_options_from_csv,
                    input.linear_slope_of_feature_from_csv,
                    input.additional_features_checkbox,
                    ignore_init=False,
                    ignore_none=False)      
    def _():
        add_options_with_factor_from_csv()
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
     
    @render_widget 
    @reactive.event(input.selectize_with_all_active_features,
                    input.base_amount_input,
                    input.daterange,
                    update_state_for_data_from_csv,
                    update_state_for_more_features,
                    update_dynamic_data,
                    ignore_init=False,
                    ignore_none=False)
    def hist():
        selectize_with_all_active_features = list(input.selectize_with_all_active_features())
        features_from_csv_checkbox = input.features_from_csv_checkbox()
        additional_features_checkbox = input.additional_features_checkbox()

        generatorDataFrame()
        DF_SALE = plot.get()
        for i, addition_feature in enumerate(addition_features.get()):
            if (len(selectize_with_all_active_features) >= 1 and 
                first_column_header.split()[0].lower() not in feature_dict and 
                not(features_from_csv_checkbox) and 
                first_column_header.split()[0].lower() in selectize_with_all_active_features):
                selectize_with_all_active_features.remove(first_column_header.split()[0].lower())
            
            if (len(selectize_with_all_active_features) >= 1 and 
                addition_feature not in feature_dict and 
                not(additional_features_checkbox) and
                addition_feature in selectize_with_all_active_features):
                selectize_with_all_active_features.remove(addition_feature)
                 
                
            if (len(selectize_with_all_active_features) >= 1):         
                group_feat_l = selectize_with_all_active_features.copy()
                group_feat_l.insert(0, "date")
                DF_VIS = DF_SALE.groupby(group_feat_l)["value"].sum().reset_index()
            else:
                DF_VIS = DF_SALE
                
            if "date" in DF_VIS.columns and "value" in DF_VIS.columns:
                DF_PLOT = DF_VIS[["date", "value"]]

            if (len(selectize_with_all_active_features) >= 1): 
                color_col = "-".join(selectize_with_all_active_features)
                DF_PLOT[color_col] = functools.reduce(
                    lambda x, y: x + "-" + y, (DF_VIS[feat] for feat in selectize_with_all_active_features)
                )
                base = px.line(DF_PLOT, x="date", y="value", color=color_col)

            else:
                base = px.line(DF_PLOT, x="date", y="value")
        return base 
        
    @render.data_frame
    @reactive.event(input.selectize_with_all_active_features,
                    input.base_amount_input,
                    input.daterange,
                    update_state_for_data_from_csv,
                    update_state_for_more_features,
                    number_of_rows_for_dataframe,
                    update_dynamic_data,
                    ignore_init=False,
                    ignore_none=False)
    def generator(): 
        DF_SALE = plot.get().head(number_of_rows_for_dataframe.get())  
        DF_SALE['date'] = pd.to_datetime(DF_SALE['date'], unit='ns')
        DF_SALE['date'] = DF_SALE['date'].dt.strftime('%d/%m/%Y')
        return DF_SALE
    
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
            if first_column_header.split()[0].lower() in feature_dict:
                del feature_dict[first_column_header.split()[0].lower()]
            
            add_options_with_factor_from_csv()
            
            all_active_features = list(input.selectize_with_all_active_features())
            if len(all_active_features) >= 1 and first_column_header.split()[0].lower() in all_active_features:
                all_active_features.remove(first_column_header.split()[0].lower())
                
            all_available_features_temp = all_available_features.get()
            if first_column_header.split()[0].lower() in all_available_features_temp:
                all_available_features_temp.remove(first_column_header.split()[0].lower())
                all_available_features.set(all_available_features_temp)
            ui.update_selectize(
                "selectize_with_all_active_features",
                choices=all_available_features.get(),
                selected=all_active_features,
                server=False,
                ) 
            
            ui.remove_ui("#inserted_input_selectize_with_data_from_csv")     
            ui.remove_ui("#inserted_input_linear_slope_of_feature_from_csv")
            ui.remove_ui("#inserted_selectize_with_factor_options_from_csv")
            ui.remove_ui("#inserted_checkbox_factor_for_features_from_csv")
             
    @reactive.effect
    @reactive.event(input.selectize_with_options_from_csv)
    def _():
        selectize_with_options_from_csv = input.selectize_with_options_from_csv()
        if len(selectize_with_options_from_csv) == 1:
            ui.remove_ui("#inserted_selectize_with_factor_options_from_csv")
            ui.remove_ui("#inserted_input_linear_slope_of_feature_from_csv")
            
            feature_dict[first_column_header.split()[0].lower()] = selectize_with_options_from_csv

            selectize_with_factor_options_from_csv = ui.input_selectize(  
                        "selectize_with_factor_options_from_csv",  
                        "select factor for ["+first_column_header.split()[0].lower()+"]",  
                        options_list_for_selectize_with_factors,  
                        multiple=True
                    ),
            
            ui.insert_ui(
                ui.div({"id": "inserted_selectize_with_factor_options_from_csv"}, selectize_with_factor_options_from_csv),
                selector="#div_for_factors_section",
                where="beforeEnd",
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
            update_data_from_csv()
                
        elif len(selectize_with_options_from_csv) < 1:
            if first_column_header.split()[0].lower() in feature_dict:
                del feature_dict[first_column_header.split()[0].lower()]
            
            add_options_with_factor_from_csv()
            
            all_active_features = list(input.selectize_with_all_active_features())
            all_available_features_temp = all_available_features.get()
                
            if first_column_header.split()[0].lower() in all_active_features:
                all_active_features.remove(first_column_header.split()[0].lower())
                
            if first_column_header.split()[0].lower() in all_available_features_temp:
                all_available_features_temp.remove(first_column_header.split()[0].lower())
                all_available_features.set(all_available_features_temp)
                
            ui.update_selectize(
                "selectize_with_all_active_features",
                choices=all_available_features.get(),
                selected=all_active_features,
                server=False,
                ) 
                
            ui.remove_ui("#inserted_selectize_with_factor_options_from_csv")
            ui.remove_ui("#inserted_input_linear_slope_of_feature_from_csv")            
            
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
                if addition_feature in feature_dict:
                    del feature_dict[addition_feature]
                    
                add_options_with_factor_from_csv()

                if len(all_active_features) >= 1 and addition_feature in all_active_features:
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
        if additional_features_checkbox:
            
            for i, addition_feature in enumerate(addition_features.get()):
                input_result = ""
                result = generate_value_for_feature_list(addition_feature)
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
                        ["random_factor", "line_factor"],  
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
            
            for i, addition_feature in enumerate(addition_features.get()):
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
                        options_list_for_selectize_with_factors,  
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
            ui.update_selectize(
                "selectize_with_all_active_features",
                choices=all_available_features.get(),
                selected=all_active_features,
                server=False,
            )
            update_more_features()  
    
    @reactive.effect()
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
                
    @reactive.effect()
    def _():        
        for i, addition_feature in enumerate(addition_features.get()):
            options_from_selectize = input["selectize_with_factor_options_for_additional_feature_v"+str(i)]()
            features_from_csv_checkbox = input.features_from_csv_checkbox()
            if features_from_csv_checkbox and len(options_from_selectize) > 0:
                ui.update_selectize(
                            "selectize_with_factor_options_from_csv",
                            choices=options_list_for_selectize_with_factors,
                            selected=[],
                            server=False,
                            ) 
            linear_slope_of_feature = 1

            if "line_factor" in options_from_selectize:
                linear_slope_of_feature = input["input_linear_slope_of_feature_for_additional_feature_v"+str(i)]()
            
            
            if addition_feature in feature_dict:
                for feat_val in feature_dict[addition_feature]:
                    factor_list.clear()
                    if(len(options_from_selectize)>0):
                        
                        for factor in options_from_selectize:
                            options_for_selectize_with_factors(factor, addition_feature, linear_slope_of_feature)          
                            update_dynamic_data.set(addition_feature+str(randint(0, 100)))
                    else:
                        update_dynamic_data.set(addition_feature+str(randint(0, 100)))

    @reactive.effect()
    def _():
        for i, addition_feature in enumerate(addition_features.get()):
            input_value_of_additional_feature = input["input_value_of_additional_feature_v"+str(i)]()
            list_of_values = input_value_of_additional_feature.replace(" ", "").split(",")
            feature_dict[addition_feature] = list_of_values
            update_dynamic_data.set(addition_feature+str(randint(0, 100)))

    @reactive.effect
    @reactive.event(number_of__all_rows)
    def _():
        ui.remove_ui("#inserted_number_of_rows_slider")

        number_of_rows_slider = ui.input_slider("number_of_rows_slider", "Top N rows of dataframe", 1, number_of__all_rows.get(), 50),  

        ui.insert_ui(
            ui.div({"id": "inserted_number_of_rows_slider", "class_":"d-flex justify-content-start align-items-start col"}, number_of_rows_slider),
            selector="#data_frame_info_div",
            where="beforeEnd",
        )

    @reactive.effect
    @reactive.event(input.number_of_rows_slider)
    def _():
        number_of_rows_for_dataframe.set(input.number_of_rows_slider())     
          
    @reactive.effect
    @reactive.event(input.show_dataframe_switch)
    def _():
        show_dataframe_switch = input.show_dataframe_switch()
        number_of_rows_for_dataframe.set(input.number_of_rows_slider())     
        data_frame_with_data = ui.output_data_frame("generator"), 
        
        if show_dataframe_switch:
            ui.insert_ui(
                ui.div({"id": "inserted_data_frame_with_data"}, data_frame_with_data),
                selector="#visualization_div",
                where="beforeEnd",
            )            
            
        else:
            ui.remove_ui("#inserted_data_frame_with_data")
    
    @render.download(
        filename=lambda: f"Shiny_Time_Series_Syntheic_Data_{datetime.datetime.now()}.csv"
    )
    async def download_button():
        DF_SALE = plot.get().head(number_of_rows_for_dataframe.get())
        columns = ""
        for column in DF_SALE.columns:
            columns += column + ', '
        columns = columns[:-2] + "\n"
        
        # await asyncio.sleep(5)
        yield columns
        
        for value in DF_SALE.values:
            result = ""
            for j, data in enumerate(value):
                result += str(data) + ", " 
            result = result[:-2] + "\n"   
            yield result
        
app = App(app_ui, server)