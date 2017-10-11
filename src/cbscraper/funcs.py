import errno
import json
import jsonpickle
import logging
import os
import shutil
import subprocess
from operator import itemgetter

import natsort
import math
import time

# FUNCTIONS

def loggerSetup(log_file):

    #Reset logging handlers
    logging.getLogger().handlers = []

    #log_format_str = "[%(asctime)s:%(levelname)s:%(filename)s:%(lineno)d:%(funcName)s] %(message)s"
    log_format_str = "[%(levelname)s:%(filename)s:%(lineno)d:%(funcName)s] %(message)s"
    fmt = logging.Formatter(log_format_str, datefmt='%H:%M:%S')

    # console log handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)
    logging.getLogger().addHandler(console_handler)

    # file log handler
    if log_file is not None:
        silentRemove(log_file)
        file_handler = logging.FileHandler(log_file, encoding="utf8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)
        logging.getLogger().addHandler(file_handler)

    # root logger
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info("Starting at: " + time.strftime("%Y-%m-%d"))

def setup(log_file, output_file):
    loggerSetup(log_file)
    if output_file:
        silentRemove(output_file)
    # Initialize JSON pickle
    iniJSONPickle()

def isNan(num):
    return isinstance(num, float) and math.isnan(num)

def remDir(dir):
    # Remove folder
    if os.path.isdir(dir):
        shutil.rmtree(dir)
    # Independently of wheter it already existed or not
    os.makedirs(dir, exist_ok=True)


def sortDFColumns(frame, first_cols=[]):
    """
    Sort the columns of a dataframe
    :param frame: The pandas.DataFrame
    :param first_cols: A list of columns to put first
    :return: The sorted DataFrame
    """

    # Build a dict col->cardinal number
    col_map = dict()
    for i, c in enumerate(first_cols):
        if c not in frame:
            raise Exception("{} is not in the DataFrame ({})".format(c, list(frame)))
        col_map[c] = i+1

    # Rename columns
    frame.rename(columns=col_map, inplace=True)

    # Sort columns
    frame = frame.reindex_axis(natsort.natsorted(frame.columns, alg=natsort.ns.IGNORECASE), axis=1)

    # Rename columns back
    inv_map = {v:k for k,v in col_map.items()}
    frame.rename(columns=inv_map, inplace=True)

    return frame


def column(matrix, i):
    f = itemgetter(i)
    return map(f, matrix)


def silentRemove(filename):
    try:
        os.remove(filename)
    except OSError as e:  # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occurred


# Print iterations progress
def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
    # Print New Line on Complete
    if iteration == total:
        print()


def csv2stata(infile):
    stata_exe = "C:\Program Files (x86)\Stata13\StataMP-64.exe"

    in_base = os.path.basename(infile)
    in_name = os.path.splitext(in_base)[0]
    do_file = in_name + ".do"

    do_cont = 'import delimited using "' + in_base + '", delimiters(",") bindquotes(strict) \n'
    do_cont += 'save "' + in_name + '" \n'  # very import the last new line

    with open(do_file, 'w') as file:
        file.write(do_cont)

    subprocess.call([stata_exe, "/e", "do", do_file])


def iniJSONPickle():
    jsonpickle.set_preferred_backend('simplejson')
    jsonpickle.set_encoder_options('simplejson', indent=4, sort_keys=True, ensure_ascii=False)


def readJSONFile(file, fatal_on_not_found=True, default_return=None, fatal_on_decode_error=True):
    try:
        fileh = open(file, 'r', encoding="utf-8")
    except FileNotFoundError:
        if fatal_on_not_found:
            msg = "File not found '" + file + "'"
            #logging.critical(msg)
            raise Exception(msg)
        else:
            return default_return
    else:
        # logging.debug(cont)
        cont = fileh.read()
        fileh.close()
        try:
            obj = jsonpickle.decode(cont)
        except json.decoder.JSONDecodeError:
            if fatal_on_decode_error:
                logging.critical("Decode error in '" + file + "'")
                raise
            else:
                return default_return
        else:
            return obj


# filename DOES INCLUDE EXTENSION
def saveJSON(data, filename, overwrite=True):
    if not overwrite and os.path.isfile(filename):
        return False
    data_str = jsonpickle.encode(data)
    with open(filename, 'w', encoding="utf-8") as fileh:
        fileh.write(data_str)
    return True


def myTextStrip(str):
    return str.replace('\n', '').strip()


def jsonPretty(dict_data):
    return json.dumps(dict_data, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)
