import numpy as np
from scipy.interpolate import RectBivariateSpline as Spline
import pandas as pd
from pyproj import Transformer
import PySimpleGUI as sg
import os, sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Test Variables for Geoid Offset
# ---------------------------------------------------------

# lat long in section 1, expected output: -21.320
lat1 = 46.722092
lng1 = -119.593764

# lat long in section 2, expected output: -17.738
lat2 = 47.774909
lng2 = -103.038359

# lat long in section 3, expected output: -34.258
lat3 = 44.932176
lng3 = -85.050656

# lat long in section 4, expected output: -24.392
lat4 = 46.586622
lng4 = -68.946552

# lat long in section 5, expected output:
lat5 = 35.244635
lng5 = -117.594686

# lat long in section 6, expected output: -25.507
lat6 = 30.582375
lng6 = -97.876989

# lat long in section 7, expected output:
lat7 = 30.535319
lng7 = -84.822393

# lat long in section 8, expected output:
lat8 = 35.766048
lng8 = -75.888771

# ---------------------------------------------------------

'''
ASCII HEADERS

glamn      Southermost Latitude  of grid (decimal degrees)
glomn      Westernmost Longitude of grid (decimal degrees)
dla        Latitude spacing  of grid     (decimal degrees)
dlo        Longitude spacing of grid     (decimal degrees)
nla        Number of rows    of grid
nlo        Number of columns of grid
ikind      Set to "1", meaning the gridded data is "real*4"
'''


def geoid_height(latitude, longitude):

    # determine grid based on lat, lng input
    if 40 < latitude < 58 and -130 < longitude < -111:
        ascFile = resource_path('g2018u1.asc')
    elif 40 < latitude < 58 and -113 < longitude < -94:
        ascFile = resource_path('g2018u2.asc')
    elif 40 < latitude < 58 and -96 < longitude < -77:
        ascFile = resource_path('g2018u3.asc')
    elif 40 < latitude < 58 and -79 < longitude < -60:
        ascFile = resource_path('g2018u4.asc')
    elif 24 < latitude < 42 and -130 < longitude < -111:
        ascFile = resource_path('g2018u5.asc')
    elif 24 < latitude < 42 and -113 < longitude < -94:
        ascFile = resource_path('g2018u6.asc')
    elif 24 < latitude < 42 and -96 < longitude < -77:
        ascFile = resource_path('g2018u7.asc')
    elif 24 < latitude < 42 and -79 < longitude < -60:
        ascFile = resource_path('g2018u8.asc')
    else:
        print("invalid Lat, Lng")
        return

    # load .asc file into dataframe
    df = pd.read_csv(ascFile, header=None)

    # extract header values
    glamn, glomn, dla, dlo = str(df[0][0]).split()[:4]
    glomn = -360 + float(glomn)
    nla, nlo, ikind = str(df[0][0]).split()[4:]

    # calculate coordinate arrays
    lats = np.arange(float(glamn), float(glamn) +
                     float(dla)*int(nla)-.001, float(dla))
    longs = np.arange(float(glomn), float(glomn) +
                      float(dlo)*int(nlo)-.001, float(dlo))

    # calculate grid from dataframe
    df2 = df[0].str.split().replace("'", "")
    grid = []
    for i, x in enumerate(df2):
        if i > 0:
            floats = [float(y) for y in x]
            grid += floats
    grid_reshaped = np.array(grid).reshape(int(nla), int(nlo))

    # calculate bivariate spline for interpolating data
    interp = Spline(lats, longs, grid_reshaped)

    # calculate the geoid offset height in meters
    ht = interp.ev(latitude, longitude)
    return ht

# convert from a stateplane zone to lat long(WGS84, EPSG: 4326)


def sp_to_latlng(x, y, in_crs):
    # inProj = Proj(in_crs, preserve_units=True)
    # outProj = Proj(out_crs)
    transformer = Transformer.from_crs(in_crs, 4326)
    lat, lng = transformer.transform(x, y)
    return lat, lng

# convert from lat long(WGS84, EPSG: 4326) to a stateplane zone


def latlng_to_sp(lat, lng, out_crs):
    transformer = Transformer.from_crs(4326, out_crs)
    lat_out, lng_out = transformer.transform(lat, lng)
    return lat_out, lng_out

# convert ellipsoid elevation to geoid and lat lng to stateplane

# ft to meters = 0.3048
# meters to ft = 3.28084

# 46.722092
# -119.593764

def ll_geoid_ht_calc(lat, lng, ell_ht, units):
    geoid_offset_m = geoid_height(lat, lng)
    geoid_offset_ft = geoid_offset_m * 3.28084
    geoid_ht = ell_ht - geoid_offset_m
    if units == 'us-ft' or units == 'ft':
        geoid_ht = geoid_ht* 3.28084
    return geoid_ht, geoid_offset_m, geoid_offset_ft

def ll_ellipsoid_ht_calc(lat, lng, geoid_ht, units):
    geoid_offset_m = geoid_height(lat, lng)
    geoid_offset_ft = geoid_offset_m * 3.28084
    ell_ht = geoid_ht + geoid_offset_m
    if units == 'us-ft' or units == 'ft':
        geoid_ht = geoid_ht * 0.3048
        ell_ht = geoid_ht + geoid_offset_m
    return ell_ht, geoid_offset_m, geoid_offset_ft

def ne_geoid_ht_calc(north, east, ell_ht, in_crs):
    lat, lng = sp_to_latlng(east, north, in_crs)
    geoid_offset = geoid_height(lat, lng)
    geoid_ht = ell_ht - geoid_offset
    return geoid_ht

def ne_ellipsoid_ht_calc(north, east, geoid_ht, in_crs):
    lat, lng = sp_to_latlng(east, north, in_crs)
    geoid_offset = geoid_height(lat, lng)
    ell_ht = geoid_ht + geoid_offset
    return ell_ht

sg.theme('DarkAmber')

epsg_file =resource_path('epsg-sp-nad83.csv')

epsg_codes = pd.read_csv(epsg_file)

status = [(''), ('Please fill out all fields before converting.'), ('Please select StatePlane Zone and Units.')]
crs_sub = [('This is the output coordinate system for conversion to Easting Northing'), ('This is the input coordinate system for conversion from Easting Northing')]

epsg = [[sg.Listbox(list(epsg_codes['Label']), size=(
    20, 4), enable_events=False, key='_EPSG_')]]
radio_btns = [[sg.Radio('meters', 'RADIO1', key="METERS_RADIO", default=True)], [sg.Radio(
    'int feet', 'RADIO1', key="INT_FT_RADIO", default=False)], [sg.Radio('survey feet', 'RADIO1', key="US_FT_RADIO", default=False)]]
latlong = [
    [sg.Push(), sg.T('Latitude'), sg.Input(
        key='LAT', disabled_readonly_background_color='black')],
    [sg.Push(), sg.T(
        'Longitude'), sg.Input(key='LNG', disabled_readonly_background_color='black')]
]
nez = [
    [sg.Push(), sg.T('Easting'), sg.Input(key='EAST', disabled=True,
                                          disabled_readonly_background_color='black')],
    [sg.Push(), sg.T('Northing'), sg.Input(key='NORTH', disabled=True,
                                           disabled_readonly_background_color='black')]
]
elev = [
    [sg.Push(), sg.T('Elevation'), sg.Input(key='ELEV', disabled=False,
                                            disabled_readonly_background_color='black')]
]


layout = [
    [sg.Text('Input Coordinates', size=(30, 1),
             font='Lucida', justification='left')],
    [sg.Radio('Use Latitude and Longitude', 'RADIO2',
              key='LATLONG_RADIO', enable_events=True, default=True)],
    [sg.Column(latlong, element_justification='l')],
    [sg.Radio('Use Easting and Northing', 'RADIO2',
              key='NEZ_RADIO', enable_events=True, default=False)],
    [sg.Column(nez, element_justification='l')],
    [sg.Text('Input Elevation', size=(30, 1),
             font='Lucida', justification='left')],
    [sg.Text(text='Leave blank if only doing XY conversions.', size=(60, 1), text_color='white',
             key='ELEV_SUB', justification='l')],
    [sg.Radio('Ellipsoid', 'RADIO3',
              key='ELL_RADIO', enable_events=True, default=True),
     sg.Radio('Geoid', 'RADIO3',
              key='GEO_RADIO', enable_events=True, default=False)],
    [sg.Column(elev, element_justification='l')],
    [sg.Text('Select Stateplane Zone and Units', size=(
        30, 1), font='Lucida', justification='left')],
    [sg.Text(text=crs_sub[0], size=(60, 1), text_color='white',
             key='CRS_SUB', justification='l')],
    [sg.Column(epsg, element_justification='c'), sg.Column(
        radio_btns, element_justification='l')],
    [sg.Text(text=status[0], size=(50, 1), text_color='white',
             key='INDICATOR', justification='c')],
    [sg.Text('Output Values', size=(
        30, 1), font='Lucida', justification='left')],
    [sg.Push(), sg.T('Geoid Offset Meters', key='OFFSET_M_LABEL'), sg.Input(status[0], size=(50, 1), disabled=True, text_color=sg.theme_text_color(), disabled_readonly_background_color=sg.theme_text_element_background_color(),
                                                   key='OFFSET_M', justification='l')],
    [sg.Push(), sg.T('Geoid Offset Feet', key='OFFSET_FT_LABEL'), sg.Input(status[0], size=(50, 1), disabled=True, text_color=sg.theme_text_color(), disabled_readonly_background_color=sg.theme_text_element_background_color(),
                                                   key='OFFSET_FT', justification='l')],
    [sg.Push(), sg.T('X', key='X_LABEL'), sg.Input(status[0], size=(50, 1), disabled=True, text_color=sg.theme_text_color(), disabled_readonly_background_color=sg.theme_text_element_background_color(),
                                                   key='X', justification='l')],
    [sg.Push(), sg.T('Y', key='Y_LABEL'), sg.Input(status[0], size=(50, 1), disabled=True, text_color=sg.theme_text_color(), disabled_readonly_background_color=sg.theme_text_element_background_color(),
                                                   key='Y', justification='l')],
    [sg.Push(), sg.T('Z', key='Z_LABEL'), sg.Input(status[0], size=(50, 1), disabled=True, text_color=sg.theme_text_color(), disabled_readonly_background_color=sg.theme_text_element_background_color(),
                                                   key='Z', justification='l')],
    [sg.Text(text=status[0], size=(50, 1), text_color='white',
             key='WHITESPACE', justification='c')],
    [sg.Button('Ok'), sg.Button('Cancel'), sg.Button('Reset')]]
window = sg.Window('Coordinate Converter', layout, resizable=True)

while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, 'Exit'):
        break
    if values['NEZ_RADIO'] == True:
        window['CRS_SUB'].Update(value=crs_sub[1])
        window['LAT'].Update(disabled=True)
        window['LNG'].Update(disabled=True)
        window['NORTH'].Update(disabled=False)
        window['EAST'].Update(disabled=False)
    if values['LATLONG_RADIO'] == True:
        window['CRS_SUB'].Update(value=crs_sub[0])
        window['LAT'].Update(disabled=False)
        window['LNG'].Update(disabled=False)
        window['NORTH'].Update(disabled=True)
        window['EAST'].Update(disabled=True)

    if event == 'Ok' and values['_EPSG_'] and values['METERS_RADIO'] == True and values['LAT'] and values['LNG'] and values['LATLONG_RADIO'] == True:
        try:
            code = int(epsg_codes.loc[epsg_codes['Label']
                       == values['_EPSG_'][0], 'EPSG_m'].iloc[0])
            print("code: ", code)
            east, north = latlng_to_sp(
                float(values['LAT']), float(values['LNG']), code)
            window['X'].update(value=east)
            window['Y'].update(value=north)
            window['X_LABEL'].update(value='Easting m')
            window['Y_LABEL'].update(value='Northing m')
            window['INDICATOR'].update(value=status[0])
        except ValueError:
            error = "No ESPG Code for {0} in meters.".format(
                values['_EPSG_'][0])
            window['INDICATOR'].update(value=error)
            window['X'].update(value='')
            window['Y'].update(value='')
    elif event == 'Ok' and values['_EPSG_'] and values['INT_FT_RADIO'] == True and values['LAT'] and values['LNG'] and values['LATLONG_RADIO'] == True:
        try:
            code = int(epsg_codes.loc[epsg_codes['Label']
                       == values['_EPSG_'][0], 'EPSG_ft'].iloc[0])
            print("code: ", code)
            east, north = latlng_to_sp(
                float(values['LAT']), float(values['LNG']), code)
            window['X'].update(value=east)
            window['Y'].update(value=north)
            window['X_LABEL'].update(value='Easting int ft')
            window['Y_LABEL'].update(value='Northing int ft')
            window['INDICATOR'].update(value=status[0])
        except ValueError:
            error = "No ESPG Code for {0} in int feet.".format(
                values['_EPSG_'][0])
            window['INDICATOR'].update(value=error)
            window['X'].update(value='')
            window['Y'].update(value='')
    elif event == 'Ok' and values['_EPSG_'] and values['US_FT_RADIO'] == True and values['LAT'] and values['LNG'] and values['LATLONG_RADIO'] == True:
        try:
            code = int(epsg_codes.loc[epsg_codes['Label']
                       == values['_EPSG_'][0], 'EPSG_usft'].iloc[0])
            print("code: ", code)
            east, north = latlng_to_sp(
                float(values['LAT']), float(values['LNG']), code)
            window['X'].update(value=east)
            window['Y'].update(value=north)
            window['X_LABEL'].update(value='Easting usft')
            window['Y_LABEL'].update(value='Northing usft')
            window['INDICATOR'].update(value=status[0])
        except ValueError:
            error = "No ESPG Code for {0} in survey feet.".format(
                values['_EPSG_'][0])
            window['INDICATOR'].update(value=error)
            window['X'].update(value='')
            window['Y'].update(value='')
    elif event == 'Ok' and values['_EPSG_'] and values['METERS_RADIO'] == True and values['EAST'] and values['NORTH'] and values['NEZ_RADIO'] == True:
        try:
            code = int(epsg_codes.loc[epsg_codes['Label']
                       == values['_EPSG_'][0], 'EPSG_m'].iloc[0])
            print("code: ", code)
            lat, lng = sp_to_latlng(
                float(values['EAST']), float(values['NORTH']), code)
            window['X'].update(value=lat)
            window['Y'].update(value=lng)
            window['X_LABEL'].update(value='Latitude')
            window['Y_LABEL'].update(value='Longitude')
            window['INDICATOR'].update(value=status[0])
        except ValueError:
            error = "No ESPG Code for {0} in meters.".format(
                values['_EPSG_'][0])
            window['INDICATOR'].update(value=error)
            window['X'].update(value='')
            window['Y'].update(value='')
    elif event == 'Ok' and values['_EPSG_'] and values['INT_FT_RADIO'] == True and values['EAST'] and values['NORTH'] and values['NEZ_RADIO'] == True:
        try:
            code = int(epsg_codes.loc[epsg_codes['Label']
                       == values['_EPSG_'][0], 'EPSG_ft'].iloc[0])
            print("code: ", code)
            lat, lng = sp_to_latlng(
                float(values['EAST']), float(values['NORTH']), code)
            window['X'].update(value=lat)
            window['Y'].update(value=lng)
            window['X_LABEL'].update(value='Latitude')
            window['Y_LABEL'].update(value='Longitude')
            window['INDICATOR'].update(value=status[0])
        except ValueError:
            error = "No ESPG Code for {0} in int feet.".format(
                values['_EPSG_'][0])
            window['INDICATOR'].update(value=error)
            window['X'].update(value='')
            window['Y'].update(value='')
    elif event == 'Ok' and values['_EPSG_'] and values['US_FT_RADIO'] == True and values['EAST'] and values['NORTH'] and values['NEZ_RADIO'] == True:
        try:
            code = int(epsg_codes.loc[epsg_codes['Label']
                       == values['_EPSG_'][0], 'EPSG_usft'].iloc[0])
            print("code: ", code)
            lat, lng = sp_to_latlng(
                float(values['EAST']), float(values['NORTH']), code)
            window['X'].update(value=lat)
            window['Y'].update(value=lng)
            window['X_LABEL'].update(value='Latitude')
            window['Y_LABEL'].update(value='Longitude')
            window['INDICATOR'].update(value=status[0])
        except ValueError:
            error = "No ESPG Code for {0} in survey feet.".format(
                values['_EPSG_'][0])
            window['INDICATOR'].update(value=error)
            window['X'].update(value='')
            window['Y'].update(value='')
    
    elif event == 'Ok' and values['_EPSG_'] == []:
        window['INDICATOR'].update(value=status[2])

    elif event == 'Ok' and ((values['EAST'] == '' and values['NORTH'] == '' and values['NEZ_RADIO'] == True) or (values['LAT'] == '' and values['LNG'] == '' and values['LATLONG_RADIO'] == True) or (values['ELEV'] == '' and values['ELL_RADIO'] == True) or (values['ELEV'] == '' and values['GEO_RADIO'] == True)):

        window['INDICATOR'].update(status[1])

    if event == 'Ok' and values['_EPSG_'] and values['LAT'] and values['LNG'] and values['LATLONG_RADIO'] == True and values['ELL_RADIO'] ==True and values['ELEV']:
        if values['METERS_RADIO'] == True:
            units = 'm'
        elif values['INT_FT_RADIO'] == True or values['US_FT_RADIO'] == True:
            units = 'ft'
        geoid_ht, geoid_offset_m, geoid_offset_ft = ll_geoid_ht_calc(float(values['LAT']), float(values['LNG']), float(values['ELEV']), units)
        window['OFFSET_M'].update(value=geoid_offset_m)
        window['OFFSET_FT'].update(value=geoid_offset_ft)
        window['Z'].update(value=geoid_ht)
        window['Z_LABEL'].update(value='Geoid Elevation ' + units)

    elif event == 'Ok' and values['_EPSG_'] and values['LAT'] and values['LNG'] and values['LATLONG_RADIO'] == True and values['GEO_RADIO'] ==True and values['ELEV']:
        if values['METERS_RADIO'] == True:
            units = 'm'
        elif values['INT_FT_RADIO'] == True or values['US_FT_RADIO'] == True:
            units = 'ft'
        ell_ht, geoid_offset_m, geoid_offset_ft = ll_ellipsoid_ht_calc(float(values['LAT']), float(values['LNG']), float(values['ELEV']), units)
        window['OFFSET_M'].update(value=geoid_offset_m)
        window['OFFSET_FT'].update(value=geoid_offset_ft)
        window['Z'].update(value=ell_ht)
        window['Z_LABEL'].update(value='Ellipsoid Elevation m')

    elif event == 'Ok' and values['_EPSG_'] and values['NORTH'] and values['EAST'] and values['NEZ_RADIO'] == True and values['GEO_RADIO'] ==True and values['ELEV']:
        try:
            code = int(epsg_codes.loc[epsg_codes['Label']
                       == values['_EPSG_'][0], 'EPSG_usft'].iloc[0])
            lat, lng = sp_to_latlng(
                float(values['EAST']), float(values['NORTH']), code)
            if values['METERS_RADIO'] == True:
                units = 'm'
            elif values['INT_FT_RADIO'] == True or values['US_FT_RADIO'] == True:
                units = 'ft'
            ell_ht, geoid_offset_m, geoid_offset_ft = ll_ellipsoid_ht_calc(lat, lng, float(values['ELEV']), units)
            window['OFFSET_M'].update(value=geoid_offset_m)
            window['OFFSET_FT'].update(value=geoid_offset_ft)
            window['Z'].update(value=ell_ht)
            window['Z_LABEL'].update(value='Ellipsoid Elevation m')
            window['INDICATOR'].update(value=status[0])
        except ValueError:
            error = "No ESPG Code for {0} in survey feet.".format(
                values['_EPSG_'][0])
            window['INDICATOR'].update(value=error)
            window['X'].update(value='')
            window['Y'].update(value='')
    elif event == 'Ok' and values['_EPSG_'] and values['NORTH'] and values['EAST'] and values['NEZ_RADIO'] == True and values['ELL_RADIO'] ==True and values['ELEV']:
        try:
            code = int(epsg_codes.loc[epsg_codes['Label']
                       == values['_EPSG_'][0], 'EPSG_usft'].iloc[0])
            lat, lng = sp_to_latlng(
                float(values['EAST']), float(values['NORTH']), code)
            if values['METERS_RADIO'] == True:
                units = 'm'
            elif values['INT_FT_RADIO'] == True or values['US_FT_RADIO'] == True:
                units = 'ft'
            geoid_ht, geoid_offset_m, geoid_offset_ft = ll_geoid_ht_calc(lat, lng, float(values['ELEV']), units)
            window['OFFSET_M'].update(value=geoid_offset_m)
            window['OFFSET_FT'].update(value=geoid_offset_ft)
            window['Z'].update(value=geoid_ht)
            window['Z_LABEL'].update(value='Geoid Elevation ' + units)
            window['INDICATOR'].update(value=status[0])
        except ValueError:
            error = "No ESPG Code for {0} in survey feet.".format(
                values['_EPSG_'][0])
            window['INDICATOR'].update(value=error)
            window['X'].update(value='')
            window['Y'].update(value='')
    if event == 'Reset':
        window['LAT'].Update(value='')
        window['LNG'].Update(value='')
        window['NORTH'].Update(value='')
        window['EAST'].Update(value='')
        window['ELEV'].Update(value='')
        window['OFFSET_M'].update(value='')
        window['OFFSET_FT'].update(value='')
        window['X'].update(value='')
        window['Y'].update(value='')
        window['Z'].update(value='')
    if event == 'Cancel':
        raise SystemExit
window.close()
