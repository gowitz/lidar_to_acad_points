import os.path
from flask import Flask, flash, request, redirect, url_for, render_template, send_file
from werkzeug.utils import secure_filename
import pandas as pd
from bokeh.plotting import figure
from bokeh.embed import components
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy
import subprocess
import json

APP_VERSION = "2.0.1 beta"
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
EXPORT_FILENAME = 'points.scr'
ALLOWED_EXTENSIONS = {'profil': 'csv','lidar': 'csv','dxf2kml': 'dxf', 'vc_lidar':'csv'}
#LIDAR_CLASSIFICATION_IGNORE = [4,5,6]
LIDAR_CLASSIFICATION_IGNORE = []
CLASSIFICATION_FILE = "static/classification_lidar_cloud_points.json"
MNT_ONLY_DEFAULT = False

with open(CLASSIFICATION_FILE, "r") as f:
    data = json.load(f)
for item in data:
    if not item['mnt']:
        LIDAR_CLASSIFICATION_IGNORE.append(int(item['classification_code']))
f.close()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['EXPORT_FILENAME'] = EXPORT_FILENAME
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.secret_key = "secret key"  # for encrypting the session

# Upload en check file section ------------------------------------------------ 
# Check allowed file extension
def allowed_file_extension(filename:str, conversion: str) -> bool:
    extension = get_file_extension(filename)
    return True if extension == ALLOWED_EXTENSIONS[conversion] else False

def get_file_extension(filename: str) -> str:
    return filename.rsplit('.', 1)[1].lower()

def check_file_to_upload(request, conversion):
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return False
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file', 'danger')
        return False
    if not allowed_file_extension(file.filename, conversion):
        flash('Wrong file type, only .' + ALLOWED_EXTENSIONS[conversion] + ' file', 'danger')
        return False
    return True

def upload_file(request: Flask) -> str:
    file = request.files['file']
    filename = secure_filename(file.filename)
    # if file already exists in upload folder remove it
    if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    # then save the file
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return filename

# Output file section ---------------------------------------------------------   
# Set output file
def set_script_file(filename: str) -> str:
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

# Write points in output file
def write_points(export_filename, gb):
    with open(os.path.join(app.config['DOWNLOAD_FOLDER'], export_filename), 'w') as file:
        for g in gb:
            # write line to create layer named by classsification (g[0] = list of unique classification)
            file.write(("_-layer E " + str(g[0]) + " \r"))
            # write line to create a point for each row
            for index, row in g[1].iterrows() :
                x = numpy.round(row['x'],3)
                y = numpy.round(row['y'],3)
                file.write('point ' + str(x) + ',' + str(y) + "\r")
    file.close()

# Write liness in output file
def write_lines(export_filename, df, mnt):
    with open(os.path.join(app.config['DOWNLOAD_FOLDER'], export_filename), 'w') as file:
        file.write("_-layer E _AJS_100_E_profil_mnt_T\r")
        file.write("\r")
        file.write("_pline\r")
        for index, row in df.iterrows() :
            file.write(str(row['distance']) + ',' + str(row['mnt']) + '\n')
        file.write("\r")
        if not mnt:
            file.write("_-layer E _AJS_100_E_profil_mms_T\r")
            file.write("\r")
            file.write("_pline\r")
            for index, row in df.iterrows() :
                file.write(str(row['distance']) + ',' + str(row['mns']) + '\n')
            file.write("\r")
    file.close()

# Plot section ---------------------------------------------------------------- 
# Plot lines
def plot_lines(export_filename, mnt):
    filename = export_filename.split(".")[0] + ".csv"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    plt.clf()
    df = pd.read_csv(file_path)

    x1 = df['distance']
    y1 = df['mnt']
    mnt_only = 'True'
    if  mnt != mnt_only:
        x2 = df['distance']
        y2 = df['mns']

    # Set graph style
    plt.style.use('default')
    # Set grid
    ax = plt.axes()        
    ax.yaxis.grid()
    # Set axis labels
    plt.ylabel('Altitude [m]')
    plt.xlabel('Distance [m]')

    #plt.scatter(x,y, c='k', s=0.1)
    plt.plot(x1, y1, c='k', label = "MNT")
    if mnt != mnt_only:
        plt.plot(x2, y2, c='g', label = "MNS")

    plt.legend()

    return plt

# Plot points
def plot_points(export_filename, mnt):
    filename = export_filename.split(".")[0] + ".csv"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    plt.clf()
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()

    if "mileage" in df and "z" in df and "classification" in df:
        df.rename(columns={'mileage':'distance', 'z':'altitude'}, inplace=True)

    mnt_only = 'True'
    if  mnt == mnt_only:
        df = df[~df.classification.isin(LIDAR_CLASSIFICATION_IGNORE)]

    x = df['distance']
    y = df['altitude']

    # Set graph style
    plt.style.use('default')
    # Set grid
    ax = plt.axes()        
    ax.yaxis.grid()
    # Set axis labels
    plt.ylabel('Altitude [m]')
    plt.xlabel('Distance [m]')

    #plt.scatter(x,y, c='k', s=0.1)
    plt.scatter(x,y, c='k', s=0.1)

    return plt



# Routes ----------------------------------------------------------------------
# home 

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route("/downloadfile/<export_filename>", methods=['GET'])
def download_file(export_filename):
    flash('File ' + export_filename + ' ready to download.', 'success')
    return render_template('download.html', value=export_filename)

# download files

@app.route("/downloadprofilefile/<export_filename>/<mnt>", methods=['GET'])
def download_profile_file(export_filename, mnt):
    flash('File ' + export_filename + ' ready to download.', 'success')

    # Get the matplotlib plot 
    plot = plot_lines(export_filename, mnt)
    plot_file_name = export_filename.split(".")[0] + ".png"

    # Save the figure in the static directory 
    plot.savefig(os.path.join('static', 'img_export', plot_file_name))

    return render_template('downloadprofil.html', value=export_filename, img=plot_file_name)

@app.route("/downloadlidarfile/<export_filename>/<mnt>", methods=['GET'])
def download_lidar_file(export_filename, mnt):
    flash('File ' + export_filename + ' ready to download.', 'success')
    # Get the matplotlib plot 
    plot = plot_points(export_filename, mnt)
    plot_file_name = export_filename.split(".")[0] + ".png"

    # Save the figure in the static directory 
    plot.savefig(os.path.join('static', 'img_export', plot_file_name))

    return render_template('downloadlidar.html', value=export_filename, img=plot_file_name)

@app.route("/downloaddxf2kml/<export_filename>", methods=['GET'])
def download_dxf2kml_file(export_filename):
    flash('File ' + export_filename + ' ready to download.', 'success')
    return render_template('downloaddxf2kml.html', value=export_filename)

@ app.route('/return-files/<export_filename>')
def return_files_tut(export_filename):
    file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], export_filename)
    return send_file(file_path, as_attachment=True, download_name='')

# Conversions

@ app.route('/lidar')
def lidar():
    return render_template('upload_lidar.html')

@ app.route('/lidar', methods=['POST'])
def upload_lidar() -> None:
    if request.method == 'POST':
        if check_file_to_upload(request, 'lidar') :
            filename = upload_file(request)
            export_filename = set_script_file(filename)
            mnt_checkbox = request.form.get('mnt')

            if mnt_checkbox == 'mnt':
                mnt = True
            else:
                mnt = MNT_ONLY_DEFAULT

            # create dataframe
            df = pd.read_csv(os.path.join(
                app.config['UPLOAD_FOLDER'], filename))
            # if columns distance, altitude and classification are in dataframe
            if "distance" in df and "altitude" in df and "classification" in df:
                # skip MNS classifications
                if mnt:
                    df = df[~df.classification.isin(LIDAR_CLASSIFICATION_IGNORE)]
                # filtre dataframe columns
                df = df[['distance', 'altitude', 'classification']]
                df.rename(columns={'distance':'x', 'altitude':'y'}, inplace=True)
                # group by classification
                gb = df.groupby('classification')
                write_points(export_filename, gb)

            else:
                flash('File not well formatted', 'danger')
                return redirect(request.url)
            #return redirect('/downloadlidarfile/' + export_filename + mnt)
            return redirect(url_for('download_lidar_file', export_filename=export_filename, mnt = str(mnt)))

    return render_template('upload_lidar.html')

@ app.route('/profil')
def profil():
    return render_template('upload_profil.html')

@ app.route('/profil', methods=['POST'])
def upload_profil():
    if request.method == 'POST':
        if check_file_to_upload(request, 'profil') :
            filename = upload_file(request)
            export_filename = set_script_file(filename)
            mnt_checkbox = request.form.get('mnt')

            if mnt_checkbox == 'mnt':
                mnt = True
            else:
                mnt = MNT_ONLY_DEFAULT

            # create dataframe
            df = pd.read_csv(os.path.join(
                app.config['UPLOAD_FOLDER'], filename))
            # if columns distance, altitude and classification are in dataframe
            if "distance" in df and "mnt" in df and "mns" in df:
                write_lines(export_filename, df, mnt)

            else:
                flash('File not well formatted', 'danger')
                return redirect(request.url)

            return redirect(url_for('download_profile_file', export_filename=export_filename, mnt = str(mnt)))
        

    return render_template('upload_profil.html')

@ app.route('/dxf2kml')
def dxf2kml():
    return render_template('upload_dxf2kml.html')

@ app.route('/dxf2kml', methods=['POST'])
def upload_dxf2kml():
    if request.method == 'POST':
        if check_file_to_upload(request, 'dxf2kml') :
            filename = upload_file(request)
            if get_file_extension(filename) == 'dxf':
                export_filename = filename.split(".")[0] + ".kml"
                input_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                output_file = os.path.join(app.config['DOWNLOAD_FOLDER'], export_filename)
                cmd = 'ogr2ogr -f KML -s_srs epsg:2056 -t_srs epsg:4326 ' + output_file + ' ' + input_file
                subprocess.call(cmd, shell=True)
            return redirect(url_for('download_dxf2kml_file', export_filename=export_filename))
    return render_template('upload_dxf2kml.html')

@ app.route('/vc_lidar')
def vc_lidar():
    return render_template('upload_vc_lidar.html')

@ app.route('/vc_lidar', methods=['POST'])
def upload_vc_lidar():
    if request.method == 'POST':
        if check_file_to_upload(request, 'vc_lidar') :
            filename = upload_file(request)
            export_filename = set_script_file(filename)
            mnt_checkbox = request.form.get('mnt')

            if mnt_checkbox == 'mnt':
                mnt = True
            else:
                mnt = MNT_ONLY_DEFAULT
            # create dataframe
            df = pd.read_csv(os.path.join(
                app.config['UPLOAD_FOLDER'], filename))
            df.columns = df.columns.str.strip()
            # if columns distance, altitude and classification are in dataframe
            if "mileage" in df and "z" in df and "classification" in df:
                # skip MNS classifications
                if mnt:
                    df = df[~df.classification.isin(LIDAR_CLASSIFICATION_IGNORE)]
                # filtre dataframe columns
                df = df[['mileage', 'z', 'classification']]
                df.rename(columns={'mileage':'x', 'z':'y'}, inplace=True)

                # group by classification
                gb = df.groupby('classification')
                write_points(export_filename, gb)

            else:
                flash('File not well formatted', 'danger')
                return redirect(request.url)

            return redirect(url_for('download_lidar_file', export_filename=export_filename, mnt = str(mnt)))

    return render_template('upload_vc_lidar.html')

# help

@ app.route('/help')
def about():
    return render_template('help.html')

@app.context_processor
def inject_app_version():
    return dict(app_version=APP_VERSION)


# Main section ----------------------------------------------------------------
 
if __name__ == '__main__':
    app.run(debug=True)
