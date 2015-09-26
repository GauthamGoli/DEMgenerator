from django.contrib.gis.db import models
from django.contrib.gis.geos import Point,GEOSGeometry
from django.contrib.gis.measure import Distance,D
from geopy.distance import distance
import re

class aoi(models.Model):
    lat = models.FloatField()
    lng = models.FloatField()
    alt = models.FloatField(default=0.0)
    coords = models.PointField(geography=True)
    objects= models.GeoManager()


class LineOi(models.Model):
    name = models.CharField(max_length=50)
    line_feature = models.LineStringField()
    objects = models.GeoManager()

    def __unicode__(self):
        return self.name


class subLineOi(models.Model):
    name = models.CharField(max_length=50)
    line_feature = models.LineStringField()
    objects = models.GeoManager()

    @property
    def length(self):
        match = re.search(r'\[ \[ (?P<lng1>\d+\.\d+), (?P<lat1>\d+\.\d+) \], \[ (?P<lng2>\d+\.\d+), (?P<lat2>\d+\.\d+) \]', self.line_feature.geojson)
        return Distance(m=distance((match.group('lat1'),match.group('lng1')),(match.group('lat2'),match.group('lng2'))).meters)

    def intermDistance(self, point):
        """
        :param point: intersectionPointGeometry.wkt
        :return: distance from start of subline to the given point
        """
        lng,lat = point.strip('POINT ').strip('()').split()
        point = (lat,lng)
        match = re.search(r'\[ \[ (?P<lng1>\d+\.\d+), (?P<lat1>\d+\.\d+) \], \[ (?P<lng2>\d+\.\d+), (?P<lat2>\d+\.\d+) \]', self.line_feature.geojson)
        return Distance(m=distance((match.group('lat1'), match.group('lng1')), point).meters)

    def __unicode__(self):
        return str(self.pk)+' '+self.name



