import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tiwarisir.settings')

import django
django.setup()
import optparse
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import LineString
from gmap.models import LineOi,subLineOi

                # /Path/To/Shp/Files/Directory
#location_data =  "C:\\Users\\admin.admin-PC1\\Downloads\\goli\\goli\\shpfiles\\"

def main():
    parser = optparse.OptionParser("usage%prog --shapefiles <path/to/shp/directory>")
    parser.add_option('--shapefiles', dest='location_data', type='string', help='specify shape files directory')
    (options, args) = parser.parse_args()
    if (options.location_data == None):
        print parser.usage
        exit(0)
    location_data = options.location_data
    location_data = location_data.replace('\\','\\\\')
    contents = os.listdir(location_data)
    shpfiles = [fil for fil in contents if fil[-3:]=='shp']
    for shpfile in shpfiles:
        ds = DataSource(os.path.join(location_data,shpfile))
        lyr = ds[0]
        for layer in lyr:
            print 'Populating %s'%(lyr.name)
            list_of_points_on_line = list(layer.geom.coords)
            # http://gis.stackexchange.com/questions/67210/convert-3d-wkt-to-2d-shapely-geometry
            if layer.geom.geos.hasz:
                LineOi.objects.create(name=lyr.name, line_feature = LineString([xy[0:2] for xy in list_of_points_on_line]).wkt)
                for i in range(len(list_of_points_on_line)-1):
                    subLineOi.objects.create(name=lyr.name, line_feature = LineString((list_of_points_on_line[i][0:2],list_of_points_on_line[i+1][0:2])).wkt)
                continue
            else:
                LineOi.objects.create(name=lyr.name,line_feature=layer.geom.wkt)
                for i in range(len(list_of_points_on_line)-1):
                    subLineOi.objects.create(name=lyr.name, line_feature = LineString((list_of_points_on_line[i],list_of_points_on_line[i+1])).wkt)


if __name__== '__main__':
    print "Starting population script.."
    main()

        