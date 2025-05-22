import os.path
from flask import Flask, flash, request, redirect, url_for, render_template, send_file
from werkzeug.utils import secure_filename
import pandas as pd

UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
EXPORT_FILENAME = 'points.scr'
ALLOWED_EXTENSIONS = ['csv','txt','dxf']

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['EXPORT_FILENAME'] = EXPORT_FILENAME
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.secret_key = "secret key"  # for encrypting the session


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_file(request):
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
        filename = secure_filename(file.filename)
        # if file already exists in upload folder remove it
        if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # then save the file
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    

def set_script_file(filename):
    # if default file already exists in destination folder remove it
    if os.path.isfile(os.path.join(app.config['DOWNLOAD_FOLDER'], app.config['EXPORT_FILENAME'])):
        os.remove(os.path.join(
            app.config['DOWNLOAD_FOLDER'], app.config['EXPORT_FILENAME']))

    # define destination file with the same name with .src extension
    export_filename = filename.split(".")[0] + ".scr"

    # if destination file already exists in destination folder remove it
    if os.path.exists(os.path.join(app.config['DOWNLOAD_FOLDER'], export_filename)):
        os.remove(os.path.join(app.config['DOWNLOAD_FOLDER'], export_filename))
    
    return export_filename


def write_points(export_filename, gb):
    with open(os.path.join(app.config['DOWNLOAD_FOLDER'], export_filename), 'w') as file:
        for g in gb:
            # write line to create layer named by classsification (g[0] = list of unique classification)
            file.write(("_-layer E " + str(g[0]) + " \r"))
            # write line to create a point for each row
            for index, row in g[1].iterrows() :
                file.write('point ' + str(row['x']) + ',' + str(row['y']) + "\r")


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

""" @app.route('/', methods=['POST']) """
""" @app.route('/home', methods=['POST'])
def upload_file_home():
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
        # If allowed file
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # if file already exists in upload folder remove it
            if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # then save the file
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # create dataframe
            df = pd.read_csv(os.path.join(
                app.config['UPLOAD_FOLDER'], filename))

            # if default file already exists in destination folder remove it
            if os.path.isfile(os.path.join(app.config['DOWNLOAD_FOLDER'], app.config['EXPORT_FILENAME'])):
                os.remove(os.path.join(
                    app.config['DOWNLOAD_FOLDER'], app.config['EXPORT_FILENAME']))

            # define destination file with the same name with .src extension
            export_filename = filename.split(".")[0] + ".scr"

            # if destination file already exists in destination folder remove it
            if os.path.exists(os.path.join(app.config['DOWNLOAD_FOLDER'], export_filename)):
                os.remove(os.path.join(app.config['DOWNLOAD_FOLDER'], export_filename))

            # if columns distance, altitude and classification are in dataframe
            if "distance" in df and "altitude" in df and "classification" in df:
                # filtre dataframe columns
                df = df[['distance', 'altitude', 'classification']]
                with open(os.path.join(app.config['DOWNLOAD_FOLDER'], export_filename), 'a') as the_file:
                    # group by classification
                    gb = df.groupby('classification')
                    for g in gb:
                        # write line to create layer named by classsification (g[0] = list of unique classification)
                        the_file.write(("_-layer E " + str(g[0]) + " \r"))
                        # write line to create a point for each row
                        for index, row in g[1].iterrows() :
                            the_file.write('point ' + str(row['distance']) + ',' + str(row['altitude']) + "\r")
            else:
                flash('File not well formatted', 'danger')
                return redirect(request.url)

        return redirect('/downloadfile/' + export_filename)

    return render_template('upload.html') """

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

@ app.route('/lidar', methods=['POST'])
def upload_lidar():
    if request.method == 'POST':
        filename = upload_file(request)
        export_filename = set_script_file(filename)
        print(os.path.join(app.config['UPLOAD_FOLDER'], filename))

         # create dataframe
        df = pd.read_csv(os.path.join(
            app.config['UPLOAD_FOLDER'], filename))
        # if columns distance, altitude and classification are in dataframe
        if "distance" in df and "altitude" in df and "classification" in df:
            # filtre dataframe columns
            df = df[['distance', 'altitude', 'classification']]
            df.rename(columns={'distance':'x', 'altitude':'y'}, inplace=True)
            # group by classification
            gb = df.groupby('classification')
            write_points(export_filename, gb)

        else:
            flash('File not well formatted', 'danger')
            return redirect(request.url)

        return redirect('/downloadfile/' + export_filename)

    return render_template('upload_lidar.html')

@ app.route('/profil')
def profil():
    return render_template('upload_profil.html')

@ app.route('/dxf2kml')
def dxf2kml():
    return render_template('upload_dxf2kml.html')

@ app.route('/vc_lidar')
def vc_lidar():
    return render_template('upload_vc_lidar.html')

@ app.route('/vc_lidar', methods=['POST'])
def upload_vc_lidar():
    if request.method == 'POST':
        filename = upload_file(request)
        
        export_filename = set_script_file(filename)
        
        # create dataframe
        df = pd.read_csv(os.path.join(
            app.config['UPLOAD_FOLDER'], filename))
        # if columns distance, altitude and classification are in dataframe
        if " mileage" in df and " z" in df and " classification" in df:
            # filtre dataframe columns
            df = df[[' mileage', ' z', ' classification']]
            df.rename(columns={' mileage':'x', ' z':'y', ' classification':'classification'}, inplace=True)
            print(df.columns)
            # group by classification
            gb = df.groupby('classification')
            write_points(export_filename, gb)

        else:
            flash('File not well formatted', 'danger')
            return redirect(request.url)

        return redirect('/downloadfile/' + export_filename)

    return render_template('upload_vc_lidar.html')

@ app.route('/help')
def about():
    return render_template('help.html')

if __name__ == '__main__':
    app.run(debug=True)
