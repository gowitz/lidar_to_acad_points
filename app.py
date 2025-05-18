import os.path
from flask import Flask, flash, request, redirect, url_for, render_template, send_file
from werkzeug.utils import secure_filename
import pandas as pd

UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
EXPORT_FILENAME = 'points.scr'
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['EXPORT_FILENAME'] = EXPORT_FILENAME
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
app.secret_key = "secret key"  # for encrypting the session


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@app.route('/home')
def upload_form():
    return render_template('home.html')

@app.route('/', methods=['POST'])
@app.route('/home', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash('Wrong file type, only .txt or .csv file', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            df = pd.read_csv(os.path.join(
                app.config['UPLOAD_FOLDER'], filename))

            if os.path.isfile(os.path.join(app.config['DOWNLOAD_FOLDER'], app.config['EXPORT_FILENAME'])):
                os.remove(os.path.join(
                    app.config['DOWNLOAD_FOLDER'], app.config['EXPORT_FILENAME']))

            export_filename = filename.split(".")[0] + ".scr"

            if os.path.exists(os.path.join(app.config['DOWNLOAD_FOLDER'], export_filename)):
                os.remove(os.path.join(app.config['DOWNLOAD_FOLDER'], export_filename))
                
            if "distance" in df and "altitude" in df and "classification" in df:
                df = df[['distance', 'altitude', 'classification']]
                with open(os.path.join(app.config['DOWNLOAD_FOLDER'], export_filename), 'a') as the_file:
                    gb = df.groupby('classification')
                    for g in gb:
                        the_file.write(("_-layer E " + str(g[0]) + " \r"))
                        for index, row in g[1].iterrows() :
                            the_file.write('point ' + str(row['distance']) + ',' + str(row['altitude']) + "\r")
            else:
                flash('File not well formatted', 'danger')
                return redirect(request.url)

        return redirect('/downloadfile/' + export_filename)

    return render_template('upload.html')

@app.route("/downloadfile/<export_filename>", methods=['GET'])
def download_file(export_filename):
    flash('File ' + export_filename + ' ready to download.', 'success')
    return render_template('download.html', value=export_filename)

@ app.route('/return-files/<export_filename>')
def return_files_tut(export_filename):
    file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], export_filename)
    return send_file(file_path, as_attachment=True, download_name='')

@ app.route('/lidar')
def lidar():
    return render_template('upload_lidar.html')

@ app.route('/profil')
def profil():
    return render_template('upload_profil.html')

@ app.route('/help')
def about():
    return render_template('help.html')

if __name__ == '__main__':
    app.run(debug=True)
