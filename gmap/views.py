from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from gmap.models import aoi,LineOi,subLineOi
from django.contrib.gis.geos import Point,fromstr
from django.contrib.gis.measure import Distance, D
import os
import datetime
import simplejson
import urllib
import csv
import utm
from django.contrib.gis.measure import Distance
from PIL import Image
import numpy
from numpy import interp
from geopy.distance import distance
import gdal, osr
import numpy as np

ELEVATION_BASE_URL = 'https://maps.googleapis.com/maps/api/elevation/json'


@csrf_exempt
def index(request):
    if request.method == "GET":
        return render(request,'gmap/index.html')
    elif request.method == "POST":
        numpy.set_printoptions(precision=15)
        lat_left, lat_right = map(float, request.POST['lat'].split(','))
        lng_left, lng_right = map(float, request.POST['long'].split(','))
        resolution = Distance(m=float(request.POST['interval']))
        aoi.objects.all().delete()
        l = aoi(lat=lat_left, lng=lng_left, coords=fromstr('POINT(%s %s)' % (lng_left, lat_left), srid=4326))
        l.save()
        r = aoi(lat=lat_right, lng=lng_right, coords=fromstr('POINT(%s %s)' % (lng_right, lat_right), srid=4326))
        r.save()
        # assuming that only two aoi objects are in the database
        gqs = aoi.objects.all()
        if len(gqs)!=2:
            print 'check this'
            exit()

        samples = []
        for b in aoi.objects.all().distance(fromstr('POINT(%s %s)' % (l.coords.x, r.coords.y), srid=4326)):
                # samples=int(b.distance/resolution)
            samples.append(b.distance.m)
        samples_y = int(samples[0]/resolution.m)+1    # samples_y is the total number of points along vertical side of rectangle
        samples_x = int(samples[1]/resolution.m)+1    # samples_x is the total nubmer of points along horizontal side of rectangle
        alt_image = Image.new(mode="L", size=(samples_x-1, samples_y-1))
        print samples_x, samples_y
        # Crafting the response for csv
        #response = HttpResponse(content_type='text/csv')
        #response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'
        time_stamp = datetime.datetime.now().strftime('%s')
        file_name = "/home/ibmcloud/geom/static/altitude_%s.csv"%(time_stamp)
        csv_file = open(file_name,'a')
        writer = csv.writer(csv_file, delimiter=',')
        # Sending the request to google's servers
        # top letf and bottom left
        elvtn_args = {'path':"%s,%s|%s,%s"%(l.coords.y,l.coords.x,r.coords.y,l.coords.x),'sensor':'false','samples': str(samples_y),'key':'AIzaSyC_9Xk7DEorzDmF8oKzONZwQHRgQ4D-H9s'}
        url = ELEVATION_BASE_URL + '?' + urllib.urlencode(elvtn_args)
        print elvtn_args
        print url
        response_first = simplejson.load(urllib.urlopen(url))
        print response_first
        # top right and bottom right
        elvtn_args1 = {'path':"%s,%s|%s,%s"%(l.coords.y,r.coords.x,r.coords.y,r.coords.x),'sensor':'false','samples': str(samples_y),'key':'AIzaSyC_9Xk7DEorzDmF8oKzONZwQHRgQ4D-H9s'}
        url1 = ELEVATION_BASE_URL + '?' + urllib.urlencode(elvtn_args1)
        print elvtn_args1
        response_second = simplejson.load(urllib.urlopen(url1))
        print response_second
        response_first['results'].pop()
        response_second['results'].pop()
        for resultset, resultset2 in zip(response_first['results'],response_second['results']):
            print 'r'
            elvtn_args_intermediate = {'path':"%s,%s|%s,%s"%(resultset['location']['lat'], resultset['location']['lng'], resultset2['location']['lat'], resultset2['location']['lng']), 'samples': str(samples_x), 'key' : 'AIzaSyC_9Xk7DEorzDmF8oKzONZwQHRgQ4D-H9s'}
            url_intermediate = ELEVATION_BASE_URL + '?' + urllib.urlencode(elvtn_args_intermediate)
            response_intermediate = simplejson.load(urllib.urlopen(url_intermediate))
            #response_intermediate['results'].pop(0)
            response_intermediate['results'].pop()
            for resultset_intermediate in response_intermediate['results']:
                aoi.objects.create(lat=resultset_intermediate['location']['lat'], lng=resultset_intermediate['location']['lng'], alt=resultset_intermediate['elevation'], coords=fromstr('POINT(%s %s)' % (resultset_intermediate['location']['lng'], resultset_intermediate['location']['lat']), srid=4326 ))
                print [resultset_intermediate['location']['lat'], resultset_intermediate['location']['lng'],resultset_intermediate['elevation']],'created!'
                if [resultset_intermediate['location']['lat'], resultset_intermediate['location']['lng'],resultset_intermediate['elevation']]==[0, 0, -4941.75]:
                    continue
                writer.writerow([resultset_intermediate['location']['lat'], resultset_intermediate['location']['lng'], resultset_intermediate['elevation']])
        alts = [e.alt for e in aoi.objects.order_by('pk')[2:] if e.alt != 0]
        print 'len alts',len(alts),'dims',(samples_x,samples_y)
        max_alt = max(alts)
        min_alt = min(alts)
        # print alts
        # print max_alt
        # print min_alt
        alts_actual = alts[:]
        alts = [interp(a, [min_alt, max_alt], [0, 255]) for a in alts]
        # print 'final',alts
        alt_image.putdata(alts)
        print 'saving image'
        #alt_image.save('C:\\Users\\admin.admin-PC1\\Desktop\\wgisp\\tiwaris\\static\\test.jpg')
        alt_image.save('/home/ibmcloud/geom/static/test_%s.jpg'%(time_stamp))
    
        # GeoReferencing the image
        print 'geo-referencing'

        # for storing elevation in a separate layer
        # http://gis.stackexchange.com/questions/58517/python-gdal-save-array-as-raster-with-projection-from-other-file
        # http://stackoverflow.com/questions/21015674/list-object-has-no-attribute-shape

        #dst_filename='C:\\Users\\admin.admin-PC1\\Desktop\\wgisp\\tiwaris\\static\\testf.tiff'
        dst_filename='/home/ibmcloud/geom/static/testf_%s.tiff'%(time_stamp)
        #src_ds = gdal.Open('C:\\Users\\admin.admin-PC1\\Desktop\\wgisp\\tiwaris\\static\\test.jpg')
        src_ds = gdal.Open('/home/ibmcloud/geom/static/test_%s.jpg'%(time_stamp))
        format = "GTiff"
        driver = gdal.GetDriverByName(format)

        # Open destination dataset
        #dst_ds = driver.CreateCopy(dst_filename, src_ds, 0)
        dst_ds = driver.Create(dst_filename,samples_x-1,samples_y-1,1,gdal.GDT_Float64,)
        # for conversion to UTS SOURCE: https://groups.google.com/forum/#!topic/geodjango/LPtGLwIyxco
        #pnt = Point(lng_left, lat_left ,srid=4326)
        #pnt.transform(32643)  # assuming that area lies in UTS Zone 44 for which EPSG:32644
        easting,northing,zone,code = utm.from_latlon(lat_left,lng_left)
        print easting,northing,zone,code
        # Specify raster location through geotransform array
        # (uperleftx, scalex, skewx, uperlefty, skewy, scaley)
        # Scale = size of one pixel in units of raster projection
        # this example below assumes 100x100

        gt = (easting,resolution.m,0,northing,0,resolution.m*-1)

        # Set location
        dst_ds.SetGeoTransform(gt)

        # Get raster projection
        epsg = 4326
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(epsg)
        dest_wkt = srs.ExportToWkt()
        print dest_wkt

        # Set projection
        dst_ds.SetProjection(dest_wkt)
        final_alts=[]
        final_alts_image=[]
        i=0
        for y in xrange(samples_y-1):
            final_alts.append([])
            final_alts_image.append([])
            for x in xrange(samples_x-1):
                final_alts[-1].append(alts_actual[i])
                final_alts_image[-1].append(alts[i])
                i=i+1
        alts_np = np.array(final_alts)
        alts_image_np = np.array(final_alts_image)

        #dst_ds.GetRasterBand(1).WriteArray(alts_image_np)
        dst_ds.GetRasterBand(1).WriteArray(alts_np)
        dst_ds.FlushCache()
        print os.getcwd()
        if 'static' not in os.getcwd():
            os.chdir(os.path.join(os.getcwd(),'static'))
        # http://gis.stackexchange.com/questions/116672/georeferencing-a-raster-using-gdal-and-python
        os.system('gdal_translate -of GTiff -a_ullr %s %s %s %s "testf_%s.tiff" "final_%s.tiff"'%(lng_left,lat_left,lng_right,lat_right,time_stamp,time_stamp))
        # Close files
        dst_ds = None
        src_ds = None

        return HttpResponse(str(time_stamp))


def intersection(request, name):
    if request.method == "GET":
        #oi = get_object_or_404(LineOi,name=name)
        qs = LineOi.objects.all().exclude(name=name)
        print qs
        #qs.intersection(field_name='line_feature',geom=oi.line_feature)

        # for subLines
        try:
            sublines_oi_queryset = subLineOi.objects.filter(name=name)
        except Exception as e:
            print str(e)
            HttpResponse("not %s feature found, check console for error."%name)
        print sublines_oi_queryset
        #qs_sublines = subLineOi.objects.all().exclude(name=name)
        #qs_sublines.intersection(field_name='line_feature', geom=oi.line_feature)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="intersections.csv"'
        writer = csv.writer(response)
        writer.writerow(['Latitude', 'Longitude', 'Chainage(m)', 'Feature Name'])
        for feature in qs:
            # querying again because somehow the same values are getting written in csv file
            sublines_oi_queryset = subLineOi.objects.filter(name=name)
            sublines_oi_queryset.intersection(field_name='line_feature', geom=feature.line_feature)
            na = True # to check in the end if this line is intersected by this particular feature
            chainage = Distance(m=0)
            for subline in sublines_oi_queryset:
                if hasattr(subline,'intersection') and subline.intersection.wkt!='GEOMETRYCOLLECTION EMPTY':
                    na = False
                    chainage+=subline.intermDistance(subline.intersection.wkt)
                    writer.writerow([subline.intersection.y, subline.intersection.x, str(chainage), feature.name])
                    print subline.intersection.wkt , chainage
                    chainage=chainage-subline.intermDistance(subline.intersection.wkt)
                chainage+=subline.length
            if na:
                writer.writerow(['na', 'na', 'na', feature.name])
        return response



