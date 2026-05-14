"""
Centralized configuration for DataDashboard deployment and automation.
"""

from pathlib import Path

# --- Path Configuration ---
ROOT = Path(__file__).parent.parent
SRC = ROOT / 'source' / 'Stat Can'
SITE_URL = 'https://teakayah.github.io/dashboard'

# --- StatCan Tables Registry ---
TABLES = [
    {
        'id': '10100015',
        'path': SRC / 'Employment' / '10100015-eng',
        'desc': 'Government operations & balance sheet (quarterly)',
    },
    {
        'id': '10100017',
        'path': SRC / 'Employment' / '10100017-eng',
        'desc': 'Public sector operations (annual)',
    },
    {
        'id': '14100287',
        'path': SRC / 'Employment' / '14100287-eng',
        'desc': 'Labour force survey (monthly)',
    },
    {
        'id': '17100005',
        'path': SRC / 'Employment' / '17100005-eng',
        'desc': 'Population estimates (annual)',
    },
    {
        'id': '18100205',
        'path': SRC / 'Housing' / '18100205-eng',
        'desc': 'New housing price index (monthly)',
    },
]

OUR_IDS = {t['id'] for t in TABLES}

# --- Extraction Rules ---
# These define how to process specific StatCan tables into JSON.
EXTRACTION_CONFIGS = {
    '14100287': {
        'default_filters': {
            'Gender': 'Total - Gender',
            'Age group': '15 years and over',
            'Statistics': 'Estimate',
            'Data type': 'Seasonally adjusted',
        },
        'variants': {
            'empRate': {'Labour force characteristics': 'Employment rate'},
            'empJobs': {'Labour force characteristics': 'Employment'},
        }
    },
    '10100015': {
        'default_filters': {
            'GEO': 'Canada',
            'Government sectors': 'Federal government',
            'Statement of government operations and balance sheet': 'Liabilities',
        }
    },
    '10100017': {
        'default_filters': {
            'Public sector components': 'Provincial and territorial governments',
            'Display value': 'Stocks',
            'Statement of operations and balance sheet': 'Liabilities [63]',
        }
    },
    '17100005': {
        'default_filters': {
            'Gender': 'Total - gender',
            'Age group': 'All ages',
        }
    },
    '18100205': {
        'measures': ["Total (house and land)", "House only", "Land only"]
    }
}

# --- Dashboard Configuration ---
ACCENT_COLORS = [
    '#4f8ef7', '#ff6384', '#4bc0c0', '#ff9f40', '#9966ff', '#36a2eb', '#ffce56', '#2ecc71'
]

LIBRARY_PATTERNS = {
    'Chart.js': r'chart\.js|chart\.umd',
    'D3.js': r'd3(?:\.v\d+)?(?:\.min)?\.js|cdn\.jsdelivr\.net/npm/d3@',
    'Plotly': r'plotly(?:\.min)?\.js|cdn\.plot\.ly',
    'Vega': r'vega(?:-lite)?(?:\.min)?\.js',
    'DuckDB': r'duckdb',
    'Grid.js': r'gridjs',
}
