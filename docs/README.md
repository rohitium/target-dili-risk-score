# DILI Risk Score Checker

An interactive web application for checking Drug-Induced Liver Injury (DILI) risk scores for drug targets.

## Features

- **Interactive Search**: Search for any target by symbol (e.g., CYP3A4, ABCB1, SLC22A1)
- **Risk Assessment**: View detailed risk scores and categories (Low/Medium/High)
- **Visual Analytics**: Charts and progress bars showing risk distribution
- **Detailed Metrics**: Drug count, high-risk drug count, DILI risk ratio, and network scores
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices

## Data Sources

The risk scores are computed using:
- **OpenTargets**: Drug-target associations and liver injury evidence
- **FDA DILIrank**: Drug-induced liver injury severity data
- **Pathway Commons**: Target-target network for guilt-by-association
- **OpenFDA**: Drug approval and withdrawal status

## Usage

1. Enter a target symbol in the search box
2. Click "Search" or press Enter
3. View the comprehensive risk assessment results
4. Explore detailed metrics and visualizations

## Sample Targets

Try searching for these well-known drug targets:
- **CYP3A4**: Cytochrome P450 3A4 (major drug metabolizing enzyme)
- **ABCB1**: P-glycoprotein (drug transporter)
- **SLC22A1**: Organic cation transporter 1
- **UGT1A1**: UDP-glucuronosyltransferase 1A1
- **SLCO1B1**: Organic anion transporting polypeptide 1B1

## Technical Details

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Bootstrap 5, custom CSS with animations
- **Charts**: Chart.js for interactive visualizations
- **Data**: JSON format for fast client-side processing
- **Hosting**: GitHub Pages for reliable, free hosting

## Risk Score Methodology

The DILI risk score combines:
1. **Direct Evidence**: Drug-target associations with DILI severity weights
2. **Network Evidence**: Guilt-by-association from target-target networks
3. **Normalization**: Features scaled to [0,1] range
4. **Categorization**: Risk levels assigned using quantiles

## Development

To update the data:
1. Run the main pipeline: `make run`
2. Convert data: `cd docs && python convert_data.py`
3. Commit and push changes

The web app will automatically use the latest data from the pipeline. 