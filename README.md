# Territorial Inequality
This project develops a reproducible workflow for constructing spatial measures of state presence across subnational territories in Africa. The project uses geospatial data on physical and economic infrastructure from the US Geological Survey compilation of Mineral Industries and Related Infrastructure. These measures are calculated at the electoral constituency level using shapefiles. The resulting measures capture variation in state presence both within and across countries and their territories.

--- 

# Start Here

1. Create the project environment and install the required dependencies.

   ```bash
   make init
   ```

2. Load in the data. 

Option 1:
The data are stored using Git LFS. If you are using Git LFS for the first time, install it following the instructions for your machine.

macOS:

```bash
brew install git-lfs
git lfs install
```
Windows:
```bash
choco install git-lfs
git lfs install
```
Then fetch the data.

```bash
git lfs pull
```

Option 2:

Download the data from the [USGS website](https://www.sciencebase.gov/catalog/item/607611a9d34e018b3201cbbf). Download the file named "Africa_GIS.gbd.zip". From [constituency shapefiles](https://github.com/bengelsma/Constituencies) download or pull the "AfricaConstituencies.zip" file.

To pull the file into the repository workspace, use:

```bash
git remote add constituencies https://github.com/bengelsma/Constituencies.git
git fetch constituencies
git checkout constituencies/main -- AfricaConstituencies.zip
```

3. Unzip files into the local repository. 

```bash
   unzip -q Africa_GIS.gdb.zip 
   unzip -q Shapefiles.zip 
```

---

# Basic workflow

The workflow consists of the following steps:

1. Load infrastructure data. To see all available layers in the GIS data, use:
```python
layers = fiona.listlayers(gdb_dat)
print("Available layers:", layers)
```
To select a specific layer, use:
```python
roads = gpd.read_file(gdb_dat, layer="AFR_Infra_Transport_Road")
```

2. Use functions to calculate a specific infrastructure measure for a single country. The function `transportation_density` takes as input a country name and infrastructure layer name and returns a constituency-level measure of density (km/km^2) for the specified layer. The function does the following: 
- Standardize coordinate reference systems (CRSs) between GIS layer and country shapefile.
- Perform spatial joins between infrastructure and constituency boundaries.
- Calculate constituency-level measures of infrastructure density.
- Merge the measures with the corresponding constituency shapefile.
- Return a new shapefile for the specified country.

Open [Workflow.ipynb](Workflow.ipynb) for a guided notebook walkthrough.

As the user works along, tests can be run to confirm the code is working as expected. Use the following to confirm whether calculations are behaving as expected:

```
make test

```

