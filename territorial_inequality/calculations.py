import geopandas as gpd
from pathlib import Path
from matplotlib import pyplot as plt

def load_data():
    """Return the path to the main GIS database."""
    df_main = "./Africa_GIS.gdb"
    return df_main

def road_density(country = ""):
    """Return a dataframe with road density information for each constituency in the specified country."""
    df_main = load_data()
    # create a GeoDataFrame for the roads in the current country
    # load road layer
    df = gpd.read_file(df_main, layer="AFR_Infra_Transport_Road")
    roads = df[df["Country"] == country]
    # project the roads to a projected coordinate system for area calculations
    roads_proj = roads.to_crs("ESRI:102022")
    
    # handle countries with spaces in their names by joining spaces to find the correct shapefile
    country_file = country.replace(" ", "")
    
    # load shapefile for current country and project to the same coordinate system
    country_sf = gpd.read_file(Path(".")/"Shapefiles"/country/f"{country_file}_Constituencies.shp")
    country_sf_proj = country_sf.to_crs("ESRI:102022")

    # intersect roads with constituencies 
    intersection = gpd.overlay(
        roads_proj,
        country_sf_proj,
        how="intersection")

    # create road variable length by summing the length of the roads in each constituency
    intersection["road_length"] = intersection.geometry.length
    intersection = intersection.groupby("Cons_name", as_index=False)["road_length"].sum()
    # transform from m into km
    intersection["length_km"] = intersection["road_length"] / 1000
    # select road length and constituency name columns
    intersection_sub = intersection[["road_length", "length_km", "Cons_name"]]

    # calculate constituency areas in km^2
    country_sf_proj["const_area_km2"] = country_sf_proj.geometry.area / 1_000_000

    # left join constituency areas with road lengths to get a combined dataframe
    country_combined = country_sf_proj.merge(intersection_sub, on="Cons_name", how="left")
    # calculate road density
    country_combined["road_density"] = (country_combined["length_km"] / country_combined["const_area_km2"])
    
    return country_combined
    
def transportation_density(country = "", layer = ""):
    """Calculate transportation layer density for every constituency in selected country."""
    
    # get path to main database
    df_main = load_data()
    
    # get path to layer 
    df_layer = gpd.read_file(df_main, layer = layer)
    
    # get path to country
    country_layer = df_layer[df_layer["Country"] == country]
    
    # identify the variable name based on the layer
    var = ""
    if layer == "AFR_Infra_Transport_Road":
        var = "road"
    elif layer == "AFR_Infra_Transport_Rail":
        var = "rail"
    elif layer == "AFR_Infra_Power_Transmission":
        var = "pwr"
    elif layer != "AFR_Infra_Transport_Road" and layer != "AFR_Infra_Transport_Rail" and layer != "AFR_Infra_Power_Transmission":
        return "Layer not recognized. Please use one of the following: AFR_Infra_Transport_Road, AFR_Infra_Transport_Rail, AFR_Infra_Power_Transmission"
            
    # handle countries with spaces in their names by joining spaces to find the correct shapefile
    country_file = country.replace(" ", "")
        
    # create output directory for the current country if it doesn't exist
    output_dir = Path(".")/"outputs"/"density"/country
    output_dir.mkdir(parents=True, exist_ok=True)
        
    # set output file 
    output_file = output_dir/f"{country_file}_Constituencies.shp"
    
    # set to only create once per country
    if output_file.exists():
        print("reading in existing output file", flush=True)
        country_sf = gpd.read_file(output_file)
    else:
        country_sf = gpd.read_file(Path(".")/"Shapefiles"/country/f"{country_file}_Constituencies.shp")
    
    #print("file read in successfully", flush=True)
    
    # project the roads to a projected coordinate system for area calculations
    trans_proj = country_layer.to_crs("ESRI:102022")
    country_sf_proj = country_sf.to_crs("ESRI:102022")

    #print("coordinate system projected successfully", flush=True)
    # intersect roads with constituencies 
    intersection = gpd.overlay(
        trans_proj,
        country_sf_proj,
        how="intersection")
    
    #print("intersection completed successfully", flush=True)

    # create length variable by summing the length of the selected layer/variable in each constituency
    intersection[var] = intersection.geometry.length.groupby(intersection["Cons_name"]).transform("sum")
    # transform from m into km
    intersection[var + "_km"] = intersection[var] / 1000
    # select road length and constituency name columns
    intersection_sub = intersection[[var, var + "_km", "Cons_name"]].drop_duplicates(subset="Cons_name")
    #intersection_sub = intersection[[var, var + "_km", "Cons_name"]]

    # calculate constituency areas in km^2
    country_sf_proj["const_area_km2"] = country_sf_proj.geometry.area / 1_000_000

    # left join constituency areas with road lengths to get a combined dataframe
    country_combined = country_sf_proj.merge(intersection_sub, on="Cons_name", how="left", validate ="m:1")
    # for constituencies with no infrastructure, fill in 0 for density
    country_combined[var + "_km"] = (country_combined[var + "_km"].fillna(0))
    # calculate density
    country_combined[var + "_den"] = (country_combined[var + "_km"] / country_combined["const_area_km2"])
    
    #print("density calculated successfully", flush=True)
    
    # add necessary columns to original country shapefile        
    country_sf = country_sf.merge(
    country_combined[["Cons_name", var + "_km", var + "_den"]], on="Cons_name", how="left")
    
    #print("columns added successfully", flush=True)
    
    #print("Rows:", len(country_sf), flush=True)
    #print("Columns:", country_sf.columns.tolist(), flush=True)
    #print("Memory (MB):",
      #country_sf.memory_usage(deep=True).sum() / 1024**2,
      #flush=True)
    #print("CRS:", country_sf.crs, flush=True)
    #print("Geometry types:", country_sf.geom_type.value_counts().to_dict(),
      #flush=True)
    #print("Null geometries:", country_sf.geometry.isna().sum(), flush=True)
    #print("Invalid geometries:",
      #(~country_sf.geometry.is_valid).sum(), flush=True)
    #print("Duplicate constituency names:",
      #country_sf["Cons_name"].duplicated().sum(), flush=True)
    
    # save to the output shapefile
    country_sf.to_file(output_file, engine="pyogrio") 
    print(f"Finished processing {country} for layer {layer}")

def summarize_distribution(country = "", var = ""):
    """Summarize the distribution of the selected transportation layer for a given country."""
    
    # get path to country output shapefile
    country_file = country.replace(" ", "")
    
    country_sf = gpd.read_file(Path(".")/"outputs"/"density"/country/f"{country_file}_Constituencies.shp")
    
    # subset to the selected variable
    if var == "road":
        country_var = country_sf[["road_km", "road_den"]]
    elif var == "rail":
        country_var = country_sf[["rail_km", "rail_den"]]
    elif var == "pwr":
        country_var = country_sf[["pwr_km", "pwr_den"]]
        
    return country_var.describe()

def plot_density(country = "", var = ""):
    """Plot the density of the selected transportation layer for a given country."""
    
        # get path to country output shapefile
    country_file = country.replace(" ", "")
    
    country_sf = gpd.read_file(Path(".")/"outputs"/"density"/country/f"{country_file}_Constituencies.shp")
    
    # select the density column
    columns = {
        "road": "road_den",
        "rail": "rail_den",
        "pwr": "pwr_den",}

    column = columns[var]

    ax = country_sf.plot(
        column=column,
        scheme="quantiles",
        k=5,
        legend=True,
        figsize=(10, 8),
        edgecolor="black",
        linewidth=0.3,
        missing_kwds={"color": "lightgrey", "label": "Missing data"})

    ax.set_title(f"{var.capitalize()} density in {country}")
    ax.set_axis_off()
    
    # save the plot to the output directory
    output_dir = Path(".")/"outputs"/"plots"/country
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir/f"{country_file}_{var}_density_plot.png"
    plt.savefig(output_file)
    print(f"Plot saved to {output_file}")
    
    plt.show()
    
def compare_density(country = "", var1 = "", var2 = ""):
    """Compare the density of two transportation layers for a given country."""
    
    # get path to country output shapefile
    country_file = country.replace(" ", "")
    
    country_sf = gpd.read_file(Path(".")/"outputs"/"density"/country/f"{country_file}_Constituencies.shp")
    
    # select the density columns
    columns = {
        "road": "road_den",
        "rail": "rail_den",
        "pwr": "pwr_den", 
        }

    column1 = columns[var1]
    column2 = columns[var2]
    
    # compare the two density columns in a scatter plot
    ax = country_sf.plot.scatter(
        x=column1,
        y=column2,
        alpha=0.5,
        figsize=(10, 8))
    
    
    ax.set_title(f"Comparison of {var1} and {var2} density in {country}")
    ax.set_xlabel(f"{var1.capitalize()} density")
    ax.set_ylabel(f"{var2.capitalize()} density")
    
    ax.set_xscale("log")
    ax.set_yscale("log")
    
    # save the plot to the output directory
    output_dir = Path(".")/"outputs"/"plots"/country
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir/f"{country_file}_{var1}_{var2}_density_plot.png"
    plt.savefig(output_file)
    print(f"Plot saved to {output_file}")
    
    plt.show()
    
def compare_density_quant(country="", var1="", var2=""):
    """Compare the density of two transportation layers for a given country with quantative measures."""

    # get path to country output shapefile
    country_file = country.replace(" ", "")
    country_sf = gpd.read_file(
        Path(".") / "outputs" / "density" / country / f"{country_file}_Constituencies.shp")

    # select the density columns
    columns = {
        "road": "road_den",
        "rail": "rail_den",
        "pwr": "pwr_den",}

    column1 = columns[var1]
    column2 = columns[var2]

    # select relevant columns
    comparison = country_sf[["Cons_name", column1, column2]].copy()

    # remove duplicate constituency records
    comparison = comparison.drop_duplicates(subset="Cons_name")

    # calculate difference between the two density measures
    comparison["density_diff"] = comparison[column1] - comparison[column2]

    # calculate ratio between the two density measures
    comparison["density_ratio"] = (
        comparison[column1] /
        comparison[column2].replace(0, float("nan")))

    return comparison

    
    
    
    

        
    

