# DataDashboard

A modern, interactive hub for navigating and conducting data analysis. This project serves as a central interface for viewing pre-built visualizations and exploring arbitrary datasets locally.

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
*   **Testing**: Comprehensive test suite using `pytest` and Playwright.

## 🚀 Getting Started

### Prerequisites
*   Python 3.9+

### Installation
1.  Clone the repository:
    ```bash
    git clone https://github.com/Teakayah/dashboard.git
    cd dashboard
    ```
2.  Install dependencies (for data updates):
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure environment variables (required for AI descriptions):
    ```bash
    cp .env.example .env
    ```
    *(Note: If you do not have Ollama installed locally, you can skip this and use `python3 deployment/refresh.py --no-descriptions` when updating data).*

### Usage
*   **View Dashboard**: Open `index.html` in any modern browser.
*   **Run Analysis**: Use the `Analytical Drop-Zone` (`dropzone.html`) to explore your own datasets.
*   **Update Data**: Run `python3 deployment/refresh.py` to rebuild all analysis pages from source data.

## 🧪 Development & Testing
Run the full test suite to verify data extraction and UI integrity:
```bash
pytest
```

---
*Built with Python & DuckDB · Auto-generated via GitHub Actions*
