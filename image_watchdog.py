'''
breadboard_python_watchdog.py
=============================
This lets you watch a folder for new single images and upload the metadata to Breadboard. 
Usage:

python3 breadboard_python_watchdog.py [WATCHFOLDER]

where [WATCHFOLDER] is the folder your camera program writes images to.

'''

import os
import time
import datetime
import shutil
import posixpath
import sys
from breadboard import BreadboardClient
import warnings
import pandas as pd
from measurement_directory import *


warnings.filterwarnings(
    "ignore", "Your application has authenticated using end user credentials")
warnings.filterwarnings(
    "ignore", "Could not find appropriate MS Visual C Runtime")
bc = BreadboardClient(config_path='API_CONFIG_fermi1.json')


def getFileList(folder=os.getcwd()):
    # Get a list of files in a folder
    if not os.path.exists(folder):
        raise ValueError("Folder '{}' doesn't exist".format(folder))
    # Folder contents
    filenames = [filename for filename in os.listdir(folder)]
    # Output
    paths = [os.path.join(folder, f) for f in filenames]
    return (filenames, paths)


def get_newest_run_dict(run_id_guess=bc._send_message('get', '/runs/', params={'lab': 'fermi1'}).json()['results'][0]['id']):
    while True:
        run_dict = bc._send_message(
            'get', '/runs/' + str(run_id_guess) + '/', params={'lab': 'fermi1'}).json()
        if 'runtime' not in run_dict.keys():
            new_run_dict = bc._send_message(
                'get', '/runs/' + str(run_id_guess - 1) + '/').json()
            new_run_dict_clean = {'runtime': new_run_dict['runtime'],
                                  'run_id': new_run_dict['id'],
                                  **new_run_dict['parameters']}
            return new_run_dict_clean, run_id_guess - 1
        run_id_guess += 1


def rename_file(filename):
    # appends a timestamp to files with redudant names to avoid overwriting
    bare_name = filename[0:len(filename) - 4]
    today = datetime.datetime.today()
    time_now = datetime.datetime.strftime(today, '%H%M%S')
    extension = filename[-4:len(filename)]
    rename = '{bare_name}_{time_now}{extension}'.format(bare_name=bare_name,
                                                        time_now=time_now,
                                                        extension=extension)
    warnings.warn(filename + ' exists here already. Saving as ' + rename)
    return rename


def main():
    # Global settings
    # bc = BreadboardClient(config_path='API_CONFIG.json') # enter your path to the API_config
    refresh_time = 1  # seconds

    """Name the set of runs"""

    measurement_dir = measurement_directory(warn=True)
    log_filepath = measurement_dir + r'\\image_log.csv'

    watchfolder = os.getcwd() + '\images'  # feed the program your watchfolder
    print("\n\n Watching this folder for changes: " + watchfolder + "\n\n")

    names_old, paths_old = getFileList(watchfolder)
    df_log = None
    if os.path.exists(log_filepath):
        df_log = pd.read_csv(log_filepath)
    n_images_per_run = int(
        input('How many images arrive per run? (e.g. 3 for triple imaging sequence) '))
#     ready = False
#     while not ready:
#         save_to_BEC1_server = input('copy images to BEC1 server? [y/n] ')
#         if save_to_BEC1_server == 'y':
#             ready = True
#             print('saving to BEC1 server...')
#         elif save_to_BEC1_server == 'n':
#             ready = True
#             print('saving only a local copy...')
#         else:
#             print('input not parsed')

    names, _ = getFileList(watchfolder)
    if len(names) > 0:
        move_misplaced_images()
    old_run_id = None
    old_list_bound_variables = None
    # Main Loop
    while True:
        # Get a list of all the images in the folder
        names, paths = getFileList(watchfolder)
        new_names = sorted(names)

        # check if a new image has come in
        if len(new_names) > 0:
            if len(new_names) < n_images_per_run:
                # waiting for all images from  newest run
                continue
            else:
                output_filenames = []
                new_names = sorted(new_names)
                for filename in new_names[0:n_images_per_run]:
                    print(filename)
                    done_moving = False
                    while not done_moving:
                        try:
                            # prevent python from corrupting file, wait for writing to disk to finish
                            filesize_changing = True
                            old_filesize = 0
                            while filesize_changing:
                                if os.path.getsize(os.path.join(r'images\\', filename)) == old_filesize:
                                    filesize_changing = False
                                else:
                                    old_filesize = os.path.getsize(
                                        os.path.join(r'images\\', filename))
                                    time.sleep(0.2)
                            # prevent overwriting data
                            old_filename = filename
                            new_filepath = os.path.join(
                                measurement_dir, filename)
                            if os.path.exists(new_filepath):
                                filename = rename_file(filename)
                                new_filepath = os.path.join(
                                    measurement_dir, filename)
            #                     if save_to_BEC1_server:
            #                         new_filepath_BEC1server = 'foo' #TODO set BEC1 server filepath
            #                         shutil.copyfile(os.path.join(r'images\\', old_filename), new_filepath_BEC1server)
                            shutil.move(os.path.join(
                                r'images\\', old_filename), new_filepath)
                            done_moving = True
                            output_filenames.append(filename)
                        except:
                            time.sleep(0.5)

            # associate new image with latest run parameters in local log

            new_row_dict, run_id_guess = get_newest_run_dict()
            if new_row_dict['run_id'] == old_run_id and old_run_id is not None:
                raise ValueError(
                    'run_id did not update between shots, check on control PC if cicero breadboard logger is on.')
#             if old_list_bound_variables is not None:
#                 if set(new_row_dict['ListBoundVariables']) != set(old_list_bound_variables):
#                     warnings.warning('List bound variables changed in Cicero. Check if new run should be started.')

            for filenum in range(n_images_per_run):
                new_row_dict['filename' +
                             str(filenum)] = output_filenames[filenum]
            new_row_dict['notes'] = ' '
            new_row_dict['badshot'] = False
            if df_log is None:
                for key in new_row_dict.keys():
                    new_row_dict[key] = [new_row_dict[key]]
                df_log = pd.DataFrame(new_row_dict)
            else:
                if os.path.exists(log_filepath):
                    df_log = pd.read_csv(log_filepath)
                df_log = df_log.append(new_row_dict, ignore_index=True)
            df_log.to_csv(log_filepath, index=False)

            # # Write to Breadboard
            # try:
            #     resp = bc.post_images(
            #                 image_names = os.path.splitext(output_filename)[0],
            #                 filepath = output_filepath,
            #                 image_times = [dt],
            #                 auto_time = False # Add more information here
            #                 )
            #     if resp.status_code!=200:
            #         print(resp.text)
            # except: pass
            # names_old = names
            names_old, _ = getFileList(watchfolder)
            print('New file(s): ' + str(output_filenames) +
                  ' associated with run parameters \n')
            print(new_row_dict['runtime'])
            listboundvars = new_row_dict['ListBoundVariables']
            try:
                for var in listboundvars:
                    print(var + ':' + str(new_row_dict[var]))
            except:
                print('bug: first shot formatting issues')

            old_run_id = new_row_dict['run_id']
            old_list_bound_variables = new_row_dict['ListBoundVariables']

        # Wait before checking again
        time.sleep(refresh_time)


main()
