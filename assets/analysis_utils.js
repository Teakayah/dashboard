/**
 * DataDashboard Analysis Utilities
 * Reusable logic for perform common analysis on report pages.
 */

window.DataDashboard = window.DataDashboard || {};

window.DataDashboard.utils = {
    /**
     * Calculates the percentage growth between the first and last data points in a series.
     * Useful for determining the overall trend of a time-series metric.
     *
     * @param {Array<{x: string|number, y: number}>} data - The normalized data array. Requires at least 2 points.
     * @returns {number|null} The growth as a percentage, or null if insufficient data or starting value is 0.
     */
    calculateGrowth: function(data) {
        if (!data || data.length < 2) return null;
        const start = data[0].y;
        const end = data[data.length - 1].y;
        if (start === 0) return null;
        return ((end - start) / Math.abs(start)) * 100;
    },

    /**
     * Identifies statistical outliers in a dataset using the 1.5 * Interquartile Range (IQR) method.
     * This helps pinpoint anomalous spikes or drops in data visualizations.
     *
     * @param {Array<{x: string|number, y: number}>} data - The normalized data array. Requires at least 4 points.
     * @returns {Array<{x: string|number, y: number}>} An array of the outlier data points.
     */
    findOutliers: function(data) {
        if (!data || data.length < 4) return [];
        const values = data.map(d => d.y).sort((a, b) => a - b);
        const q1 = values[Math.floor(values.length / 4)];
        const q3 = values[Math.floor(values.length * 3 / 4)];
        const iqr = q3 - q1;
        const min = q1 - 1.5 * iqr;
        const max = q3 + 1.5 * iqr;
        return data.filter(d => d.y < min || d.y > max);
    },

    /**
     * Generates a basic statistical summary (average, min, max, count) for a data series.
     * Provides quick context for users without requiring them to inspect the raw dataset.
     *
     * @param {Array<{x: string|number, y: number}>} data - The normalized data array.
     * @returns {{avg: number, max: number, min: number, count: number}|null} The summary statistics, or null if no data.
     */
    getSummary: function(data) {
        if (!data || data.length === 0) return null;
        let sum = 0;
        let min = Infinity;
        let max = -Infinity;
        for (let i = 0; i < data.length; i++) {
            const val = data[i].y;
            sum += val;
            if (val < min) min = val;
            if (val > max) max = val;
        }
        const avg = sum / data.length;
        return { avg, max, min, count: data.length };
    }
};

window.DataDashboard.ui = {
    initToolbar: function() {
        if (document.getElementById('analysis-toolbar')) return;

        const toolbar = document.createElement('div');
        toolbar.id = 'analysis-toolbar';
        toolbar.style = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            padding: 12px;
            display: flex;
            gap: 8px;
            z-index: 1000;
            border: 1px solid #eee;
            font-family: sans-serif;
        `;

        const title = document.createElement('div');
        title.textContent = 'Quick Insights:';
        title.style = 'font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: #999; margin-bottom: 4px; width: 100%;';
        
        const wrapper = document.createElement('div');
        wrapper.style = 'display: flex; flex-direction: column;';
        wrapper.appendChild(title);

        const btnContainer = document.createElement('div');
        btnContainer.style = 'display: flex; gap: 6px;';

        const actions = [
            { label: '📊 Summary', fn: this.showSummary },
            { label: '📈 Growth', fn: this.showGrowth },
            { label: '⚠️ Outliers', fn: this.showOutliers },
            { label: '📥 Export', fn: this.exportData }
        ];

        actions.forEach(action => {
            const btn = document.createElement('button');
            btn.textContent = action.label;
            btn.style = `
                padding: 6px 10px;
                border-radius: 6px;
                border: 1px solid #ddd;
                background: #f9f9f9;
                font-size: 0.75rem;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.2s;
            `;
            btn.onmouseover = () => btn.style.background = '#eee';
            btn.onmouseout = () => btn.style.background = '#f9f9f9';
            btn.onclick = () => action.fn();
            btnContainer.appendChild(btn);
        });

        wrapper.appendChild(btnContainer);
        toolbar.appendChild(wrapper);
        document.body.appendChild(toolbar);
    },

    /**
     * Heuristically searches global state (`window.DATA` or `window.RAW`) for the active time-series data
     * and normalizes it into a standard `{x, y}` format required by the utility functions.
     *
     * This normalization is necessary because different pages use varying object shapes
     * (e.g., `{year, value}`, `{date, pop}`, `{date, level}`).
     *
     * @returns {Array<{x: string|number, y: number}>|null} The normalized data series, or null if no valid series is found.
     */
    getActiveData: function() {
        // Attempt to find data from common global variables
        const source = window.DATA || window.RAW;
        if (!source) return null;

        // Extract the first available time-series array found in the object
        // This is a heuristic; more specific logic can be added per page type.
        let series = null;
        const findSeries = (obj) => {
            if (Array.isArray(obj) && obj.length > 0 && (obj[0].year || obj[0].date)) {
                series = obj;
                return true;
            }
            if (typeof obj === 'object' && obj !== null) {
                for (let key in obj) {
                    if (findSeries(obj[key])) return true;
                }
            }
            return false;
        };

        findSeries(source);
        return series ? series.map(d => ({ x: d.year || d.date, y: d.value || d.pop || d.level })) : null;
    },

    showSummary: function() {
        const data = window.DataDashboard.ui.getActiveData();
        if (!data) return alert('No active data series found on this page.');
        const stats = window.DataDashboard.utils.getSummary(data);
        alert(`Statistical Summary:\n- Average: ${stats.avg.toFixed(2)}\n- Peak: ${stats.max.toFixed(2)}\n- Low: ${stats.min.toFixed(2)}\n- Data Points: ${stats.count}`);
    },

    showGrowth: function() {
        const data = window.DataDashboard.ui.getActiveData();
        if (!data) return alert('No active data series found on this page.');
        const growth = window.DataDashboard.utils.calculateGrowth(data);
        if (growth === null) return alert('Insufficient data for growth calculation.');
        alert(`Total Growth across the period: ${growth.toFixed(2)}%`);
    },

    showOutliers: function() {
        const data = window.DataDashboard.ui.getActiveData();
        if (!data) return alert('No active data series found on this page.');
        const outliers = window.DataDashboard.utils.findOutliers(data);
        if (outliers.length === 0) return alert('No significant statistical outliers detected (1.5 * IQR method).');
        alert(`Detected ${outliers.length} Outliers:\n` + outliers.map(o => `${o.x}: ${o.y}`).join('\n'));
    },

    exportData: function() {
        const source = window.DATA || window.RAW;
        if (!source) return alert('No data found to export.');
        const blob = new Blob([JSON.stringify(source, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `datadashboard_export.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
};

// Auto-init when script is loaded
window.addEventListener('load', () => window.DataDashboard.ui.initToolbar());
