document.addEventListener('DOMContentLoaded', () => {
    const navItems = document.querySelectorAll('.nav-item');
    const views = document.querySelectorAll('.view');

    // Load initial report preview
    loadReportPreview();

    // Tab Switching Logic
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetId = item.getAttribute('data-target');

            // Update Nav
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // Update View
            views.forEach(view => view.classList.remove('active'));
            document.getElementById(targetId).classList.add('active');

            // If report view, fetch report
            if (targetId === 'report-view') {
                loadReport();
            }
        });
    });

    // Load Report Function
    async function loadReport() {
        const reportContainer = document.getElementById('report-content');
        try {
            // Append timestamp to prevent caching
            const response = await fetch(`/api/report?t=${new Date().getTime()}`);
            const data = await response.json();
            reportContainer.innerHTML = marked.parse(data.content);
        } catch (error) {
            reportContainer.innerHTML = '<p style="color: red">Error loading report.</p>';
            console.error('Error:', error);
        }
    }

    // Load Report Preview (Summary)
    async function loadReportPreview() {
        const previewContainer = document.getElementById('report-preview-content');
        if (!previewContainer) return;

        try {
            const response = await fetch(`/api/report?t=${new Date().getTime()}`);
            const data = await response.json();
            // Extract just the Executive Summary part or show truncated content
            // For now, let's show the whole thing but scrollable
            previewContainer.innerHTML = marked.parse(data.content);
        } catch (error) {
            previewContainer.innerHTML = '<p style="color: red">Error loading report summary.</p>';
        }
    }

    // Simulation Logic
    const slider = document.getElementById('intensity-slider');
    const intensityValue = document.getElementById('intensity-value');
    const runBtn = document.getElementById('run-simulation-btn');
    const loadingOverlay = document.getElementById('loading-overlay');

    if (slider && intensityValue) {
        slider.addEventListener('input', (e) => {
            intensityValue.textContent = e.target.value;
        });
    }

    if (runBtn) {
        runBtn.addEventListener('click', async () => {
            const intensity = slider.value;

            // Show loading and terminal
            loadingOverlay.classList.remove('hidden');
            document.getElementById('terminal-window').style.display = 'block';
            const terminalContent = document.getElementById('terminal-content');
            terminalContent.innerHTML = ''; // Clear previous logs

            runBtn.disabled = true;

            try {
                const response = await fetch(`/api/simulate?intensity=${intensity}`);
                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;

                    const text = decoder.decode(value);
                    const lines = text.split('\n\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const message = line.replace('data: ', '');

                            if (message === 'SIMULATION_COMPLETE') {
                                // Reload maps
                                const floodMap = document.querySelector('iframe[title="Flood Map"]');
                                const routeMap = document.querySelector('iframe[title="Route Map"]');
                                if (floodMap) floodMap.src = floodMap.src.split('?')[0] + '?t=' + new Date().getTime();
                                if (routeMap) routeMap.src = routeMap.src.split('?')[0] + '?t=' + new Date().getTime();

                                // Reload report if active
                                if (document.getElementById('report-view').classList.contains('active')) {
                                    loadReport();
                                }

                                // Reload preview
                                loadReportPreview();

                                alert('Simulation completed successfully!');
                            } else {
                                // Append log line
                                const div = document.createElement('div');
                                div.className = 'log-line';
                                div.textContent = message;
                                terminalContent.appendChild(div);
                                terminalContent.scrollTop = terminalContent.scrollHeight;
                            }
                        }
                    }
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred while running the simulation.');
            } finally {
                // Hide loading
                loadingOverlay.classList.add('hidden');
                runBtn.disabled = false;
            }
        });
    }
});
