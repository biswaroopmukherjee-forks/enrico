import os
import datetime
import shutil


def measurement_directory(warn=False):
    # name the run test if you want test files to be cleaned up later
    measurement_name = input('Enter name for this set of runs:')
    today = datetime.datetime.today()
    month = datetime.datetime.strftime(today, '%m')
    date = datetime.datetime.strftime(today, '%y%m%d')
    if not os.path.exists(month):
        os.mkdir(month)
    if not os.path.exists(r'{month}\{date}'.format(month=month, date=date)):
        os.mkdir(r'{month}\{date}'.format(month=month, date=date))
    ready = False
    while not ready:
        measurement_dir = r'{month}\{date}\{measurement_name}'.format(
            month=month, date=date, measurement_name=measurement_name)
        # breakpoint()
        if not os.path.exists(measurement_dir):
            os.mkdir(measurement_dir)
            ready = True
        else:
            if warn:
                unpause = input(
                    'WARNING: measurement name already exists. Are you unpausing a previously paused measurement? [y/n] ')
                if unpause == 'y':
                    ready = True
                elif unpause == 'n':
                    measurement_name = input(
                        'Enter different name for this set of runs: ')
                else:
                    print('input not parsed')
            else:
                ready = True

    return measurement_dir


def move_misplaced_images():
    today = datetime.datetime.today()
    month = datetime.datetime.strftime(today, '%m')
    date = datetime.datetime.strftime(today, '%y%m%d')
    time_now = datetime.datetime.strftime(today, '%H%M%S')
    misplaced_filepath = month + r'\\' + date + r'\\misplacedimages' + time_now
    shutil.move(r'images', misplaced_filepath)
    print('moved misplaced file(s) to {path}'.format(path=misplaced_filepath))
    os.mkdir(r'images')


def todays_measurements():
    # name the run test if you want test files to be cleaned up later
    today = datetime.datetime.today()
    month = datetime.datetime.strftime(today, '%m')
    date = datetime.datetime.strftime(today, '%y%m%d')
    if not os.path.exists(r'{month}\{date}'.format(month=month, date=date)):
        os.mkdir(r'{month}\{date}'.format(month=month, date=date))
        ValueError('No datasets saved today.')
    month_date_dir = r'{month}\{date}\\'.format(
        month=month, date=date)
    return os.listdir(month_date_dir)
