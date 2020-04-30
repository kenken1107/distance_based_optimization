import pprint as pp
import os
import numpy as np
from time import time
from datetime import datetime
import pandas as pd
import search_optimization_framework as opt_framework

def search_optimization_execution(PC_folder, opt_info_dict, folder_name):

    ##### Import the optimization information #####

    # Set the current directory
    os.chdir(PC_folder + "\\basedata_setting")

    # Get the file name for "basedata"
    file_name_base_data = opt_info_dict["basedata_file"]

    # Get the file name for "optimization_setting"
    file_name_optimization_setting = opt_info_dict["optimization_setting_file"]

    # Import the basedata (column name for timestamp must be "timestamp")
    basedata     = pd.read_csv(file_name_base_data, parse_dates=["timestamp"]).set_index(["timestamp"])

    # Import MVs information
    mv_tag_list = list(pd.read_excel(file_name_optimization_setting, sheet_name="MVs")["col_list"])

    # Import PVs info that is for violation checking
    pv_df = pd.read_excel(file_name_optimization_setting, sheet_name="PVs")

    # Import PVs information
    pv_tag_list = list(pv_df["col_list"])

    # Import DVs information in optimization_setting
    DVs_df       = pd.read_excel(file_name_optimization_setting, sheet_name="DVs")

    # Import periods for defining analysis space
    period       = pd.read_excel(file_name_optimization_setting, sheet_name="Opt_Settings",
                                 parse_dates=["analysis_start","analysis_end"])

    # Import how many points to be extracted after MD filtering
    n_nearest_points = pd.read_excel(file_name_optimization_setting,
                                     sheet_name="Opt_Settings")["n_nearest_points"].values[0]

    # Import definition of objective function ("Minimized" or "Maximized")
    objective_type = pd.read_excel(file_name_optimization_setting, sheet_name="Opt_Settings")["objective_type"].values[0]

    # Import objective parameter
    objective_param = pd.read_excel(file_name_optimization_setting, sheet_name="Opt_Settings")["objective_param"].values[0]

    # Import how many points to be extracted based on KPI
    n_best_points = pd.read_excel(file_name_optimization_setting, sheet_name="Opt_Settings")["n_best_points"].values[0]

    #####-Preprocess the dataset-#####

    # Define the analysis space (define the period for optimization)
    start_analysis = period["analysis_start"].values[0]
    end_analysis   = period["analysis_end"].values[0]
    df_analysis    = basedata.loc[start_analysis:end_analysis]

    # Define the search space
    n_points_ignore = int(period["n_points_ignore"].values[0])
    df_with_index   = basedata.reset_index().reset_index().set_index(["timestamp"]).copy()
    start = int(df_with_index.loc[df_analysis.index]['Unnamed: 0'].head(1).values[0])
    end   = int(df_with_index.loc[df_analysis.index]['Unnamed: 0'].tail(1).values[0])

    a = int(start-n_points_ignore)
    b = int(end+n_points_ignore)

    df_with_index2 = df_with_index.reset_index().set_index(['Unnamed: 0'])
    ignore_index = df_with_index2.iloc[a:b]["timestamp"].tolist()

    df_search = basedata.drop(ignore_index)

    ### Extract the DVs and its allowance range ###
    dv_tag_dict = {}
    for i, col in enumerate(DVs_df["col_list"]):
        dv_tag_dict[col] = DVs_df.loc[i, "allowance"]

    ### Execute optimization ###
    df_covariance = df_search[list(dv_tag_dict.keys())].cov()# For calculating inverse covariance matrix
    np_cov_inv    = np.linalg.pinv(df_covariance.values)

    for i in range(len(df_analysis)):
        # Extract each point of analysis space
        centroid = df_analysis.iloc[i]

        # Extract search space except one point
        df_search_except = df_search.copy()

        ###- Univariate Filtering for each DV -###
        df_search_filtered = opt_framework.filter_dv(centroid, df_search_except, dv_tag_dict)
        if len(df_search_filtered)<=0:
            raise ValueError("{} is too strict condition. No points after this filtering. Please relax it.".format(
                dv_tag_dict))

        ###- MD filtering for the specified DVs -###
        df_search_filtered_md = opt_framework.find_nn_with_mahalanobis(df_search_filtered, centroid, np_cov_inv,
                                                                       int(n_nearest_points), dv_tag_dict)

        ###- Select the best n-points based on KPI and average parameters -###
        df_top_n_kpi = opt_framework.take_top_n(df_search_filtered_md, n_best_points, objective_type, objective_param)
        df_top_n_kpi_mean = df_top_n_kpi.mean(axis=0)

        ###- Extract MVs, DVs, Objective along with its datapoints

        # For MVs
        MV_opt                            = df_top_n_kpi_mean[mv_tag_list]
        MV_cur                            = centroid[mv_tag_list]
        MVs_saved                         = pd.concat([MV_opt, MV_cur], axis=1)
        MVs_saved.columns                 = ["optimized", "current"]
        MVs_saved["points_aft_DV_filter"] = len(df_search_filtered)
        MVs_saved["points_aft_MD_filter"] = len(df_search_filtered_md)
        MVs_saved["points_of_averaging"]  = int(n_best_points)

        # For DVs
        DV_opt                            = df_top_n_kpi_mean[list(dv_tag_dict.keys())]
        DV_cur                            = centroid[list(dv_tag_dict.keys())]
        DVs_saved                         = pd.concat([DV_opt, DV_cur], axis=1)
        DVs_saved.columns                 = ["optimized", "current"]
        DVs_saved["points_aft_DV_filter"] = len(df_search_filtered)
        DVs_saved["points_aft_MD_filter"] = len(df_search_filtered_md)
        DVs_saved["points_of_averaging"]  = int(n_best_points)

        # For PVs
        PV_opt                            = df_top_n_kpi_mean[pv_tag_list]
        PV_cur                            = centroid[pv_tag_list]
        PVs_saved                         = pd.concat([PV_opt, PV_cur], axis=1)
        PVs_saved.columns                 = ["optimized", "current"]
        PVs_saved["points_aft_DV_filter"] = len(df_search_filtered)
        PVs_saved["points_aft_MD_filter"] = len(df_search_filtered_md)
        PVs_saved["points_of_averaging"]  = int(n_best_points)
        PVs_saved["fail"]                 = 0

        for col in pv_tag_list:
            min_prefer = pv_df[pv_df["col_list"] == col]["prefer_min"].values[0]
            max_prefer = pv_df[pv_df["col_list"] == col]["prefer_max"].values[0]
            if PV_opt[col] > max_prefer or PV_opt[col] < min_prefer:
                PVs_saved.loc[col, "fail"] = 1


        # For Objective
        objective_opt                           = df_top_n_kpi_mean[[objective_param]]
        objective_cur                           = centroid[[objective_param]]
        Objective_saved                         = pd.concat([objective_opt, objective_cur], axis=1)
        Objective_saved.columns                 = ["optimized", "current"]
        Objective_saved["points_aft_DV_filter"] = len(df_search_filtered)
        Objective_saved["points_aft_MD_filter"] = len(df_search_filtered_md)
        Objective_saved["points_of_averaging"]  = int(n_best_points)

        # For index
        index_saved = pd.DataFrame(data=[centroid.name], columns=["index"])

        ###- Export the result -###
        folder_result = PC_folder + "\\optimization_results\\" + folder_name
        if not os.path.isdir(folder_result):
            os.mkdir(folder_result)
        file_name     = "result_{0}selected_{1}averaged_".format(n_nearest_points, n_best_points)
        file_name2    = datetime.fromtimestamp(time()).strftime('%m-%d-%Y_%H-%M-%S')
        writer        = pd.ExcelWriter(folder_result + "\\" + file_name + '_' + file_name2 + '.xlsx')

        MVs_saved.to_excel(writer, 'MVs')
        DVs_saved.to_excel(writer, 'DVs')
        PVs_saved.to_excel(writer, "PVs")
        Objective_saved.to_excel(writer, 'Objective')
        index_saved.to_excel(writer, "index", index=False)
        writer.save()
        print("{0} is complete, {1} aft Univar filtering, {2} aft MD filtering".format(
            centroid.name, len(df_search_filtered), len(df_search_filtered_md)))