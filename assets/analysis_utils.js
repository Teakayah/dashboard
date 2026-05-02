/**
 * DataDashboard Analysis Utilities
 * Reusable logic for perform common analysis on report pages.
 */

window.DataDashboard = window.DataDashboard || {};

window.DataDashboard.utils = {
    /**
     * Calculate compound or simple growth between two points.
     */
    calculateGrowth: function(data) {
        if (!data || data.length < 2) return null;
        const start = data[0].y;
        const end = data[data.length - 1].y;
        if (start === 0) return null;
        return ((end - start) / Math.abs(start)) * 100;
    },

    /**
     * Find outliers using 1.5 * IQR method.
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
     * Generate a statistical summary.
     */
    getSummary: function(data) {
        if (!data || data.length === 0) return null;
        const values = data.map(d => d.y);
        const sum = values.reduce((a, b) => a + b, 0);
        const avg = sum / values.length;
        const max = Math.max(...values);
        const min = Math.min(...values);
        return { avg, max, min, count: values.length };
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
