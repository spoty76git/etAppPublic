// Detect mobile and adjust Plotly graphs
window.addEventListener('DOMContentLoaded', function () {
    function isMobile() {
        return window.innerWidth <= 768;
    }

    // Adjust Plotly graphs on mobile
    function adjustGraphsForMobile() {
        if (isMobile()) {
            // Wait for graphs to load
            setTimeout(function () {
                var plots = document.getElementsByClassName('js-plotly-plot');
                for (var i = 0; i < plots.length; i++) {
                    Plotly.relayout(plots[i], {
                        'xaxis.tickfont.size': 10,
                        'yaxis.tickfont.size': 10,
                        'title.font.size': 14,
                        'margin.l': 40,
                        'margin.r': 20,
                        'margin.t': 60,
                        'margin.b': 40
                    });
                }
            }, 1000);
        }
    }

    // Run on load and resize
    adjustGraphsForMobile();
    window.addEventListener('resize', adjustGraphsForMobile);
});