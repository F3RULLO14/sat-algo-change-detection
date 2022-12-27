import os
import sys
import json
import argparse
import numpy as np

from osgeo import gdal, osr
import rasterio as rio
from rasterio.mask import mask


def __write(fn, arr, trans, crs='EPSG:4326', nodata=None):
    try:
        if os.path.exists(fn):
            os.remove(fn)

        r_dataset = rio.open(fn, 'w', driver='GTiff',
                             height=arr.shape[0],
                             width=arr.shape[1],
                             nodata=nodata,
                             count=1,
                             dtype=str(arr.dtype),
                             crs={'init': crs},
                             transform=trans)

        r_dataset.write(arr, indexes=1)
        r_dataset.close()
    except Exception as e:
        print('Unable to write data to GeoTiff!')
        print(e)
        

def __parse_geojson(fn: str = ''):
    f = open(fn)
    data = json.load(f)
    features = []

    for feature in data['features']:
        features.append(feature['geometry'])

    f.close()
    return features


def __warp(fn_in, crs='EPSG:4326'):
    fn_out = '{}-warp.tif'.format(fn_in.split('.')[0])
    
    if os.path.exists(fn_out):
        return fn_out
    
    if type(crs) is int:
        proj = osr.SpatialReference()
        proj.ImportFromEPSG(crs)
        crs = proj.ExportToWkt()
        
    if type(fn_in) is str:
        fn_in = gdal.Open(fn_in)

    gdal.Warp(fn_out, fn_in, dstSRS=crs, format='GTiff', resampleAlg='near')
    return fn_out


def __crop(fn, geoms):
    with rio.open(fn, crs='EPSG:4326') as src:
        out_image, out_transform = mask(src, geoms, crop=True, nodata=0)
        
    if (out_image.ndim == 3):
        out_image = out_image[0, :, :]
    
    return out_image.astype('f4'), out_transform


def __conform_arrays(arr_dst, arr_src):
    if arr_dst.shape == arr_src.shape:
        return arr_src
    
    width_dif = arr_dst.shape[0] - arr_src.shape[0]
    height_dif = arr_dst.shape[1] - arr_src.shape[1]
    return arr_src[:width_dif, :height_dif]


def __determine_difference_between_arrays(a, b):
    c = np.zeros(shape=(a.shape[0], a.shape[1]))
    x = a.shape[0]
    y = a.shape[1]

    for i in range(0, x):
        for j in range(0, y):
            av = a[i, j]

            try:
                bv = b[i, j]
            except:
                continue

            if bv.any():
                c[i, j] = av / bv

    return np.log10(c, out=c, where=c != 0)


def evaluate_geotiff_differences(fn_previous: str = '', fn_latest: str = '', geojson_area: dict = {}, fn_out: str = '', crs: str = 'EPSG:4326'):

    # Pull out the geoms of the area intended to detect change on
    print('Parsing Area of Interest...')
    geoms = __parse_geojson(geojson_area)
    
    # Warp the ground coordinate projection to lat/lon
    print('Warping GeoTiffs to lat/lon coordinate system...')
    fn_previous_warped = __warp(fn_previous, crs)
    fn_latest_warped = __warp(fn_latest, crs)
    
    # Crop the tifs to desired geoms extracted above
    print('Cropping out data of area from GeoTiffs...')
    arr_pr, trans_pr = __crop(fn_previous_warped, geoms)
    arr_la, trans_la = __crop(fn_latest_warped, geoms)
    
    # Conform the previous array data to the latest data
    print('Conforming data arrays...')
    arr_pr = __conform_arrays(arr_la, arr_pr)
    
    # determine difference between the two
    print('Determining differences...')
    arr_difs = __determine_difference_between_arrays(arr_la, arr_pr)
    arr_difs_cl = np.clip(arr_difs, -1.0, 1.0)
    
    print('Writing output to file...')
    __write(fn_out, arr_difs_cl, trans_la, crs)


if __name__ == "__main__":
    print('Started program.\n')
    
    print('Reading arguments...')
    parser = argparse.ArgumentParser(prog='ChangeDetection')
    parser.add_argument('fn_input_previous')
    parser.add_argument('fn_input_latest')
    parser.add_argument('fn_area')
    parser.add_argument('fn_output')
    parser.add_argument('--crs', default='EPSG:4326')
    args = parser.parse_args()
    
    fn_previous = args.fn_input_previous
    fn_latest = args.fn_input_latest
    geojson_area = args.fn_area
    fn_out = args.fn_output
    crs = args.crs

    print(sys.version)
    print(f'GDAL={gdal.__version__}')
    print(f'Rasterio={rio.__version__}\n')
    
    print('Arguments: previous \'{}\' latest \'{}\' area \'{}\' out \'{}\' crs \'{}\'\n'.format(fn_previous, fn_latest, geojson_area, fn_out, crs))

    # python src/app.py sample/s1a-iw-grd-vv-20220705.tiff sample/s1a-iw-grd-vv-20221220.tiff sample/feature_collection.json output/result_vv.tif
    print('Processing...')
    evaluate_geotiff_differences(fn_previous, fn_latest, geojson_area, fn_out, crs)
    print('Complete!')