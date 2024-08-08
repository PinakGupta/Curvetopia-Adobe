from flask import Flask, request, redirect, url_for, send_from_directory, render_template
from werkzeug.utils import secure_filename
import os
from implPythonCode.utils import read_csv, read_svg, polylines2svg, plot
from implPythonCode.regularization import fit_line, fit_circle
from implPythonCode.symmetry_detection import detect_symmetry
from implPythonCode.curve_completion import complete_curve

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'csv', 'svg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_file(input_path, output_svg_path):
    if input_path.lower().endswith('.csv'):
        paths_XYs = read_csv(input_path)
    elif input_path.lower().endswith('.svg'):
        paths_XYs = read_svg(input_path)
    else:
        raise ValueError("Unsupported file type")

    for path in paths_XYs:
        for points in path:
            m, c = fit_line(points)
            print(f'Line fit: y = {m}x + {c}')
            xc, yc, R = fit_circle(points)
            print(f'Circle fit: center=({xc}, {yc}), radius={R}')
            symmetry = detect_symmetry(points)
            print(f'Symmetry detected: {symmetry}')
            completed_points = complete_curve(points, occlusion_type='connected')
            print(f'Completed curve points: {completed_points}')
    
    plot_svg_path = os.path.join(app.config['OUTPUT_FOLDER'], 'plot.svg')
    plot_png_path = os.path.join(app.config['OUTPUT_FOLDER'], 'plot.png')

    plot(paths_XYs, plot_svg_path, plot_png_path)
    polylines2svg(paths_XYs, output_svg_path)
    
    return output_svg_path, plot_svg_path, plot_png_path

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)
        
        output_svg_path = os.path.join(app.config['OUTPUT_FOLDER'], filename.rsplit('.', 1)[0] + '.svg')
        plot_svg_path = os.path.join(app.config['OUTPUT_FOLDER'], 'plot.svg')
        plot_png_path = os.path.join(app.config['OUTPUT_FOLDER'], 'plot.png')
        
        output_svg_path, plot_svg_path, plot_png_path = process_file(input_path, output_svg_path)
        
        return render_template('upload.html', 
                               svg_file=url_for('uploaded_file', filename=filename.rsplit('.', 1)[0] + '.svg'),
                               plot_svg_file=url_for('uploaded_plot', ext='svg'),
                               plot_png_file=url_for('uploaded_plot', ext='png'))
    return redirect(request.url)

@app.route('/uploads/plot.<ext>')
def uploaded_plot(ext):
    if ext not in ['svg', 'png']:
        return "File not found", 404
    return send_from_directory(app.config['OUTPUT_FOLDER'], f'plot.{ext}')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True)
