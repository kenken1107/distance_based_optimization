import scipy.spatial.distance as distance

def filter_dv(df_analysis, df_search, dv_tag_dict):

    """Function to filter the search space based on a min&max value in analysis space
    Args:
        df_analysis(Pandas DataFrame): dataframe with each one point in analysis space with which to use for filtering
        df_search  (Pandas DataFrame): dataframe in search space
        dv_tag_dict(dictionary)      : dictionary with each dv along with its allowance range
    Returns:
        df_search_filtered(Pandas DataFrame): filtered data-points(Search space) based on +- allowance value
                                             of each point in analysis space
    """
    analysis_space_df = df_analysis.copy()
    search_space_df   = df_search.copy()
    dv_tag_list       = dv_tag_dict.keys()
    dv_allowance_list = list(dv_tag_dict.values())
    for x, tag in enumerate(dv_tag_list):
        min_val = analysis_space_df[tag] - dv_allowance_list[x]
        max_val = analysis_space_df[tag] + dv_allowance_list[x]
        df_search_filtered = search_space_df[search_space_df[tag] >= min_val]
        df_search_filtered = df_search_filtered[df_search_filtered[tag] <= max_val]
    return df_search_filtered


def find_nn_with_mahalanobis(df_search_filtered, centroid, np_covariance_inverse, n_nearest_points, dv_tag_dict):

    """Function to filter the search space based on a MD
    Args:
        df_search_filtered(Pandas DataFrame): dataframe filtered in search space
        centroid          (Pandas DataFrame): dataframe with one point in analysis space
        np_covariance_inverse(numpy)        : inverse covariance matrix of DVs of all datapoints in search space
        n_points_md          (int)          : n-nearest points to be extracted based on MD
        dv_tag_dict          (dict)         : dict of DVs along with its allowance range
    Returns:
        np_search_filtered_md:              : dataframe of n-nearest points based on MD
    """

    md_distance_list = [distance.mahalanobis(df_search_filtered[list(dv_tag_dict.keys())].values[i],
                                             centroid[list(dv_tag_dict.keys())].values,
                                             np_covariance_inverse) for i in range(len(df_search_filtered))]
    df_search_filtered["dist"] = md_distance_list
    df_search_filtered_md      = df_search_filtered.loc[df_search_filtered["dist"].nsmallest(n_nearest_points).index]

    return df_search_filtered_md


def take_top_n(df_search_filtered_md, n_best_points, objective_type, objective_param):

    if objective_type=="minimize":
        df_top_n_kpi = df_search_filtered_md.loc[df_search_filtered_md[objective_param].nsmallest(n_best_points).index]
    elif objective_type=="maximize":
        df_top_n_kpi = df_search_filtered_md.loc[df_search_filtered_md[objective_param].nlargest(n_best_points).index]
    else:
        raise ValueError("{} is not correct value for objective function".format(objective_type))

    return df_top_n_kpi
