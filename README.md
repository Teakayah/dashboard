# DataDashboard

A modern, interactive hub for navigating and conducting data analysis. This project serves as a central interface for viewing pre-built visualizations and exploring arbitrary datasets locally.

## ⚠️ Known Issues & Status

This project is actively being refactored. Please read [`TODO.md`](TODO.md) before contributing to understand current critical bugs (like DuckDB-Wasm initialization issues and accessibility contrast) and to avoid regressing them.

## ✨ Key Features

### 🔍 Interactive Discovery
*   **Modern Dashboard**: A clean, card-based interface with real-time search and tag filtering.
*   **Rich Previews**: Automatic Open Graph (OG) image generation and social sharing optimization.
*   **Unified UI**: Consistent theme, navigation, and accessibility across all analysis pages.

### 📥 Analytical Drop-Zone
*   **Local-First SQL**: Drop CSV, JSON, or Parquet files to query them instantly using **DuckDB-Wasm**.
*   **Zero-Server ETL**: All processing happens in your browser—no data is uploaded to a server.
*   **Smart Previews**: Automatic correlation detection and chart generation for dropped datasets.
*   **Query Recipes**: Pre-built SQL templates to jumpstart your data exploration.

### 📱 Progressive Web App (PWA)
*   **Offline Capable**: Installable on desktop and mobile with offline support via Service Workers.
*   **Theme Engine**: Responsive design with automatic Dark Mode support.

## 🛠 Tech Stack
*   **Database**: [DuckDB-Wasm](https://duckdb.org/docs/api/wasm) for high-performance in-browser SQL.
*   **Visualization**: [Chart.js](https://www.chartjs.org/) and [Grid.js](https://gridjs.io/).
*   **ETL Pipeline**: Python-based automation for StatCan data extraction and HTML injection.
*   **Testing**: Test suite using `pytest` and Playwright covering both Python deployment scripts and front-end UI/accessibility suites.

## 📊 Pre-built Analyses
*   **[Canadian Labour & Fiscal Dashboard](employment_rate_canada.html)**: Displays Statistics Canada's seasonally adjusted employment rate data for Canadian provincial governments.
*   **[NHPI — Big-6 City Comparison](nhpi_big6_comparison.html)**: Comparison of the New Housing Price Index (NHPI) across six major Canadian cities using Statistics Canada data.
*   **[Ottawa-Gatineau Flood Risk](flood_risk_gatineau_ottawa.html)**: Interactive flood risk dashboard for Ottawa-Gatineau: Station 02KF005 level simulator, historical flood peaks, snowpack (SWE) risk, and flood zone map.

## 🔄 Contribution Workflow
This project uses a two-branch development and release workflow:
*   **`integration`**: Local development and target for feature PRs. Pushing or opening a PR runs `.github/workflows/ci.yml` (Python + Playwright tests).
*   **`main`**: Published to GitHub Pages. Updated via human-reviewed PR merge from `integration` (when `main` is updated, `.github/workflows/deploy.yml` regenerates production artifacts and fast-forwards `integration` to keep both branches in sync).

## 🚀 Getting Started

### Prerequisites
*   Python 3.9+

### Installation
1.  Clone the repository:
    ```bash
    git clone https://github.com/Teakayah/dashboard.git
    cd dashboard
    ```
2.  Install dependencies (for data extraction and testing):
    ```bash
    python3 -m pip install -r requirements.txt
    playwright install
    playwright install-deps
    ```
3.  Configure environment variables (required for AI descriptions):
    ```bash
    cp .env.example .env
    ```
    *(Note: If you do not have Ollama installed locally, you can skip this and use `python3 deployment/refresh.py --no-descriptions` when updating data).*

### Usage
*   **View Dashboard**: Open `index.html` in any modern browser.
*   **Run Analysis**: Use the `Analytical Drop-Zone` (`dropzone.html`) to explore your own datasets.
*   **Pre-built Analysis Pages**:
    *   `employment_rate_canada.html`: Analyzes Canadian employment rates over time.
    *   `nhpi_big6_comparison.html`: Compares New Housing Price Indices across six major Canadian cities.
    *   `flood_risk_gatineau_ottawa.html`: Visualizes flood risk assessment data for the Gatineau-Ottawa region.
*   **Update Data**: Run `python3 deployment/refresh.py` to rebuild all analysis pages from source data.

## 🧪 Development & Testing
Run the test suite to verify data extraction and UI components.
Always use `python3 -m pytest` rather than the global `pytest` command to ensure the local environment and Playwright dependencies resolve correctly:
```bash
python3 -m pytest
```

---
*Built with Python & DuckDB · Auto-generated via GitHub Actions*

