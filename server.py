from flask import Flask, render_template, send_file, jsonify, request, Response
import os
import subprocess
import time

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/maps/flood')
def flood_map():
    if os.path.exists('flood_simulation_map.html'):
        return send_file('flood_simulation_map.html')
    return "Flood map not found. Run simulation first."

@app.route('/maps/route')
def route_map():
    if os.path.exists('astar_route_map.html'):
        return send_file('astar_route_map.html')
    return "Route map not found. Run pathfinding first."

@app.route('/api/report', methods=['GET'])
def get_report():
    try:
        with open('design_report.md', 'r') as f:
            content = f.read()
        return jsonify({'content': content})
    except FileNotFoundError:
        return jsonify({'content': '# Report not found\nPlease run the simulation first.'})

@app.route('/api/geojson', methods=['GET'])
def get_geojson():
    try:
        return send_file('proposed_network.geojson', as_attachment=True, download_name='proposed_drainage_network.geojson')
    except FileNotFoundError:
        return jsonify({'error': 'GeoJSON file not found. Run simulation first.'}), 404

@app.route('/api/simulate', methods=['GET'])
def run_simulation():
    intensity = request.args.get('intensity', 100)
    
    def generate():
        yield f"data: Starting simulation with intensity {intensity}...\n\n"
        
        commands = [
            ['./venv/bin/python', 'flow_simulation.py', '--intensity', str(intensity)],
            ['./venv/bin/python', 'astar_pathfinding.py'],
            ['./venv/bin/python', 'visualise_astar.py'],
            ['./venv/bin/python', 'visualise_flooding.py']
        ]
        
        for cmd in commands:
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                universal_newlines=True,
                bufsize=1
            )
            
            for line in process.stdout:
                yield f"data: {line.strip()}\n\n"
                
            process.wait()
            if process.returncode != 0:
                yield f"data: Error executing {cmd[1]}\n\n"
                return

        yield "data: SIMULATION_COMPLETE\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    print("Starting dashboard server at http://localhost:5000")
    app.run(debug=True, port=5000)
