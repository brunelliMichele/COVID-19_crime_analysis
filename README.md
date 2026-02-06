# COVID-19 and Crime in Italy

An interactive geospatial analysis of how the COVID-19 pandemic reshaped the spatial distribution and intensity of crimes across Italian provinces, regions and macro-areas (2014-2023).

## Quick Start

### Using Docker (Recommended)

```bash
git clone https://github.com/brunelliMichele/COVID-19_crime_analysis.git
cd COVID-19_crime_analysis
docker-compose up --build -d
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/brunelliMichele/COVID-19_crime_analysis.git
cd COVID-19_crime_analysis

# Create virtual environment
python3 -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app/app.py
```

> **Note:** On first run, the app will automatically download data from ISTAT API. This may take 3-5 minutes.

## Project Structure

```
OVID-19_crime_analysis/
├── app/
│   ├── app.py                 # Main Streamlit application
│   ├── utils.py               # Utility functions and constants
│   └── pages/
│       ├── home.py            # Homepage with key findings
│       ├── 01_variation_maps.py    # Crime variation maps
│       ├── 02_moran.py        # Spatial autocorrelation analysis
│       └── 03_lisa_transitions.py  # LISA cluster transitions
├── scripts/
│   ├── fetch_data_istat.py    # Download data from ISTAT API
│   ├── clean_data.py          # Data cleaning and processing
│   └── build_shapes.py        # Build Italian shapefiles
├── data/
│   ├── raw/                   # Raw CSV files from ISTAT
│   ├── processed/             # Cleaned parquet files
│   └── shapes/                # Italian administrative boundaries
├── literature/                # Reference papers and documents
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Features

### 1. Spatial Distribution of Crime Changes
Interactive choropleth maps showing percentage variation in crime rates compared to the pre-COVID baseline (2014-2019).

- **View modes:** Single period or compare all periods
- **Geographic levels:** Provinces (NUTS-3), Regions(NUTS-2), Macro-areas (NUTS-1)
- **Data types:** Absolute crime or rates per 100,000 inhabitants

### 2. Spatial Autocorrelation Analysis
Moran's I analysis to detect spatial clustering pattern across three periods.

- **Global Moran's I:** Measures overall spatial autocorrelation
- **Moran Scatter Plot:** Visualizes local spatial patterns
- **Temporal comparison:** Pre-COVID vs During COVID vs Post-COVID

### 3. LISA Cluster Transitions
Track how hot spots and cold spots shifted between periods.

- **Transition maps:** Visualize cluster changes
- **Transition matrix:** Quantify movements between cluster types
- **Side-by-Side comparison:** Compare LISA maps across periods

## Data Sources

- **Crime Data:** [ISTAT](https://www.istat.it/dati/banche-dati/) - Italian National Institute of Statistics
    - Datasets:
        1. ```delittips_1_YYYY.csv``` -> crimes reported to police forces by type and location (YYYY = year)
        2. ```delittips_9_YYYY.csv``` -> criminality rate by type and location (YYYY = year)
    - API: SDMX Web Service
- **Geographic Boundaries:** [Eurostat](https://ec.europa.eu/eurostat/web/nuts/overview)
    - NUTS 2006 classification
    - Levels:
        1. Macro-areas (for Italy -> North-East, North-West, Center, South, Islands)
        2. Regions
        3. Provinces

## Technologies

- **Data Processing:** pandas, geopandas, pyarrow
- **Spatial Analysis:** libpysal, esda
- **Visualization:** Plotly, Streamlit
- **Deployment:** Docker

## Author

**Michele Brunelli**

University of Trento - Master's Degree in Data Science

Course: Geospatial Analysis and Representation for Data Science (2025-2026)