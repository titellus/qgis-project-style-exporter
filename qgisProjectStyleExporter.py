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
 
# Export all map layers style to SLD format
layers = iface.legendInterface().layers()

# Directory to store style
outputDir = "/data/app/geoserver-2.12.1/data_dir/styles/"
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
    group = root.findLayer(layer.id()).parent().name()
    layerId = "{0}-{1}".format(group, name)
    print "Processing style for layer '{0}' ...".format(layerId)
    
    # Do not export layer which are not in a valid group
    # A valid group is composed of upper case letters only
    if re.match(validGroupPattern, group) == None:
        print "  WARNING: Only layers in a valid group will be exported. Layer {0} was not exported.".format(name)
        hasInvalidGroup = True
        nbWarnings += 1
        continue
        
    # Save style in a file in QGIS and SLD format    
    outputName = "{0}{1}".format(outputDir, layerId)
    qgsStyleFileName = "{0}{1}".format(outputName, ".qml");
    layer.saveNamedStyle(qgsStyleFileName)
    layer.saveSldStyle("{0}{1}".format(outputName, ".sld"))
    
    # Concatenate styles to build QGIS library
    tree = etree.parse(qgsStyleFileName)

    for s in tree.xpath("//symbols/symbol"):
        s.set('name', layerId)
        symbolList += etree.tostring(s)

    # Save XML file to declare SLD config file
    gsStyleConfigFileContent = gsStyleConfigFile.format(name, name, name + ".sld")
    with open("{0}{1}".format(outputName, ".xml"), "w") as gsStyleConfigFileInst:
        gsStyleConfigFileInst.write(gsStyleConfigFileContent)
        
    print "  Layer '{0}' exported as QML, SLD and added to library.".format(layerId)
    nbLayersExported += 1


# Write style lybrary
with open("{0}{1}".format(outputDir, libraryName), "w") as qgsLibStyleFile:
    qgsLibStyleFile.write(qgisLibStyleTpl.format(symbolList))

# TODO: reload GS config


# Report help or messages
print "---------------"
print "Summary report:"
print " * {0} layer(s) processed.".format(nbLayers)
print " * {0} layer(s) exported ({1}%).".format(nbLayersExported, nbLayersExported * 100 / nbLayers)
print " * {0} warning(s).".format(nbWarnings)
if hasInvalidGroup:
    print msgValidGroup
print " * {0} error(s).".format(nbErrors)



