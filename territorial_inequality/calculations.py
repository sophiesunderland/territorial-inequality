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
        country_sf = gpd.read_file(output_file)
    else:
        country_sf = gpd.read_file(Path(".")/"Shapefiles"/country/f"{country_file}_Constituencies.shp")
    
    # project the roads to a projected coordinate system for area calculations
    trans_proj = country_layer.to_crs("ESRI:102022")
    country_sf_proj = country_sf.to_crs("ESRI:102022")

    # intersect roads with constituencies 
    intersection = gpd.overlay(
        trans_proj,
        country_sf_proj,
        how="intersection")

    # create length variable by summing the length of the selected layer/variable in each constituency
    intersection[var] = intersection.geometry.length.groupby(intersection["Cons_name"]).transform("sum")
    # transform from m into km
    intersection[var + "_km"] = intersection[var] / 1000
    # select road length and constituency name columns
    intersection_sub = intersection[[var, var + "_km", "Cons_name"]]

    # calculate constituency areas in km^2
    country_sf_proj["const_area_km2"] = country_sf_proj.geometry.area / 1_000_000

    # left join constituency areas with road lengths to get a combined dataframe
    country_combined = country_sf_proj.merge(intersection_sub, on="Cons_name", how="left")
    # for constituencies with no infrastructure, fill in 0 for density
    country_combined[var + "_km"] = (country_combined[var + "_km"].fillna(0))
    # calculate density
    country_combined[var + "_den"] = (country_combined[var + "_km"] / country_combined["const_area_km2"])
    
    # add necessary columns to original country shapefile        
    country_sf = country_sf.merge(
    country_combined[["Cons_name", var + "_km", var + "_den"]], on="Cons_name", how="left")
    
    # save to the output shapefile
    country_sf.to_file(output_file) 
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
        "pwr": "pwr_den", 
        }

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
    
    
    
    

        
    

