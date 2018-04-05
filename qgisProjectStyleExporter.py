"""
Script to export QGIS styles from current project 
(for layer in valid groups ie. upper case letters) to:

* SLD
* QML
* GeoServer style configuration files
* and a QGIS library containing all symbols.


Update the outputDir variable before starting the script.

In order to apply changes in GeoServer, user need to reload the configuration.
"""

from lxml import etree

from qgis.core import *
from qgis.utils import *

import re
import os
 
# Export all map layers style to SLD format
layers = iface.legendInterface().layers()

# Directory to store style
outputDir = "/data/app/geoserver-2.13.0/data_dir/"
styleOutputDir = outputDir + "styles/"
layerOutputDir = outputDir + "workspaces/iwrmstyledlayer/iwrmstyledlayer/"
# GeoServerDir ? GeoServerDir : 

# QGIS Library file name
libraryName = "IWRM.xml"


nbLayers = 0
nbLayersExported = 0
nbWarnings = 0
nbErrors = 0
hasInvalidGroup = False
msgValidGroup = "  A valid group is composed of one or more upper case letters."

gsStyleConfigFile = """<style>
  <id>StyleInfoImpl--{0}</id>
  <name>{1}</name>
  <filename>{2}</filename>
</style>"""

gsFeatureTypeTpl = """<featureType>
  <id>FeatureTypeInfoImpl--{0}</id>
  <name>{0}</name>
  <nativeName>{1}</nativeName>
  <namespace>
    <id>NamespaceInfoImpl--7d8338e5:1628f6f25e9:-7ff2</id>
  </namespace>
  <title>{0}</title>
  <keywords>
    <string>{0}</string>
  </keywords>
  <nativeCRS>GEOGCS[&quot;WGS 84&quot;, 
  DATUM[&quot;World Geodetic System 1984&quot;, 
    SPHEROID[&quot;WGS 84&quot;, 6378137.0, 298.257223563, AUTHORITY[&quot;EPSG&quot;,&quot;7030&quot;]], 
    AUTHORITY[&quot;EPSG&quot;,&quot;6326&quot;]], 
  PRIMEM[&quot;Greenwich&quot;, 0.0, AUTHORITY[&quot;EPSG&quot;,&quot;8901&quot;]], 
  UNIT[&quot;degree&quot;, 0.017453292519943295], 
  AXIS[&quot;Geodetic longitude&quot;, EAST], 
  AXIS[&quot;Geodetic latitude&quot;, NORTH], 
  AUTHORITY[&quot;EPSG&quot;,&quot;4326&quot;]]</nativeCRS>
  <srs>EPSG:4326</srs>
  <nativeBoundingBox>
    <minx>-82.47284044546662</minx>
    <maxx>-82.07999719029031</maxx>
    <miny>22.90907962744465</miny>
    <maxy>23.14681623369057</maxy>
    <crs>EPSG:4326</crs>
  </nativeBoundingBox>
  <latLonBoundingBox>
    <minx>-82.47284044546662</minx>
    <maxx>-82.07999719029031</maxx>
    <miny>22.90907962744465</miny>
    <maxy>23.14681623369057</maxy>
    <crs>EPSG:4326</crs>
  </latLonBoundingBox>
  <projectionPolicy>FORCE_DECLARED</projectionPolicy>
  <enabled>true</enabled>
  <metadata>
    <entry key="cachingEnabled">false</entry>
  </metadata>
  <store class="dataStore">
    <id>DataStoreInfoImpl--7d8338e5:1628f6f25e9:-7ff1</id>
  </store>
  <maxFeatures>0</maxFeatures>
  <numDecimals>0</numDecimals>
  <overridingServiceSRS>false</overridingServiceSRS>
  <skipNumberMatched>false</skipNumberMatched>
  <circularArcPresent>false</circularArcPresent>
</featureType>"""


gsLayerTpl="""<layer>
  <name>{0}</name>
  <id>LayerInfoImpl--{0}</id>
  <type>VECTOR</type>
  <defaultStyle>
    <id>StyleInfoImpl--{1}</id>
  </defaultStyle>
  <styles class="linked-hash-set">
    <style>
      <id>StyleInfoImpl--{1}</id>
    </style>
  </styles>
  <resource class="featureType">
    <id>FeatureTypeInfoImpl--{0}</id>
  </resource>
  <attribution>
    <logoWidth>0</logoWidth>
    <logoHeight>0</logoHeight>
  </attribution>
</layer>"""

qgisLibStyleTpl = """<!DOCTYPE qgis_style>
<qgis_style version="1">
  <symbols>{0}</symbols>
</qgis>"""



symbolList = ""
validGroupPattern = r'^[A-Z]+$'

root = QgsProject.instance().layerTreeRoot()

for layer in layers:
    nbLayers += 1
    name = layer.name()
    styleName = name
    
    # Check if style is a sub one
    if "-" in name:
        s = name.split("-")
        name = s[0]
        
    group = root.findLayer(layer.id()).parent().name()
    layerId = "{0}-{1}".format(group, styleName)
    styleId = "{0}-{1}".format(group, styleName)
    print "Processing layer '{0}' with style '{1}' ...".format(layerId, styleId)
    
    # Do not export layer which are not in a valid group
    # A valid group is composed of upper case letters only
    if re.match(validGroupPattern, group) == None:
        print "  WARNING: Only layers in a valid group will be exported. Layer {0} was not exported.".format(name)
        hasInvalidGroup = True
        nbWarnings += 1
        continue
        
    # Save style in a file in QGIS and SLD format    
    outputName = "{0}{1}".format(styleOutputDir, styleId)
    qgsStyleFileName = "{0}{1}".format(outputName, ".qml");
    layer.saveNamedStyle(qgsStyleFileName)
    layer.saveSldStyle("{0}{1}".format(outputName, ".sld"))
    
    # Concatenate styles to build QGIS library
    tree = etree.parse(qgsStyleFileName)

    for s in tree.xpath("//symbols/symbol"):
        s.set('name', styleId)
        symbolList += etree.tostring(s)

    # Save XML file to declare SLD config file
    gsStyleConfigFileContent = gsStyleConfigFile.format(styleId, styleId, styleId + ".sld")
    with open("{0}{1}".format(outputName, ".xml"), "w") as gsStyleConfigFileInst:
        gsStyleConfigFileInst.write(gsStyleConfigFileContent)
        
    print "  Style '{0}' exported as QML, SLD and added to library.".format(styleId)


    # Configure GeoServer layer - one layer per styles
    # There is no support of setting a list of style for the same layer
    layerConfigDir = "{0}{1}/".format(layerOutputDir, styleId)
    directory = os.path.dirname(layerConfigDir)
    try:
        os.stat(directory)
    except:
        os.mkdir(directory)       


    gsFeatureTypeContent = gsFeatureTypeTpl.format(layerId, name)
    with open("{0}{1}".format(layerConfigDir, "featuretype.xml"), "w") as gsFeatureTypeFileInst:
        gsFeatureTypeFileInst.write(gsFeatureTypeContent)
    
    gsLayerContent = gsLayerTpl.format(layerId, styleId)
    with open("{0}{1}".format(layerConfigDir, "layer.xml"), "w") as gsFeatureTypeFileInst:
        gsFeatureTypeFileInst.write(gsLayerContent)
    
    print "  Layer '{0}' added to GeoServer configuration.".format(layerId)


    nbLayersExported += 1


# Write style lybrary
with open("{0}{1}".format(outputDir, libraryName), "w") as qgsLibStyleFile:
    qgsLibStyleFile.write(qgisLibStyleTpl.format(symbolList))

# TODO: reload GS config


# Report help or messages
print "---------------"
print "Summary report:"
print " * {0} layer(s) and style(s) processed.".format(nbLayers)
print " * {0} layer(s) and style(s) exported ({1}%).".format(nbLayersExported, nbLayersExported * 100 / nbLayers)
print " * {0} warning(s).".format(nbWarnings)
if hasInvalidGroup:
    print msgValidGroup
print " * {0} error(s).".format(nbErrors)



