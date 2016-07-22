"""
example usage:
>>> canvas = qgis.utils.iface.mapCanvas()
>>> layer_a = canvas.layer(0) # polygon layer
>>> layer_b = canvas.layer(1) # line layer
>>> from split_polygons import split_polygons
>>> split_polygons(layer_a, layer_b, "/home/username/Desktop/output.shp")
"""

def split_polygons(layer_a, layer_b, output_path):
    provider_a = layer_a.dataProvider() # polygon data provider
    provider_b = layer_b.dataProvider() # line data provider
    attrs_a = provider_a.attributeIndexes() # get all attributes
    provider_a.select(attrs_a)
    attrs_b = provider_b.attributeIndexes() # get all attributes
    provider_b.select(attrs_b)

    feat_a = QgsFeature()
    feat_b = QgsFeature()
    out_feat = QgsFeature()
    index = QgsSpatialIndex() # create spatial index on line layer
    while provider_b.nextFeature(feat_b):
        index.insertFeature(feat_b)

    # specify output
    writer = QgsVectorFileWriter(output_path, "System",
        provider_a.fields(), provider_a.geometryType(), provider_a.crs())

    # loop through each polyon feature, grab all intersecting lines (I've only 
    # tested this with one line per polygon)
    # split the polygon along the line feature
    # retain split features, and difference each of these split features with 
    # the original feature to ensure all parts of the polygon are represented 
    # in the final output
    in_feat = QgsFeature()
    provider_a.select(attrs_a)
    while provider_a.nextFeature(feat_a): # for each polygon feature
        geom_a = QgsGeometry(feat_a.geometry())
        attrs = feat_a.attributeMap()
        intersects = index.intersects(geom_a.boundingBox()) # get all intersecting line features
        out_feat.setAttributeMap(attrs)
        for feat_id in intersects: # for each intersecting line feature
            provider_b.featureAtId(int(feat_id), feat_b , True, attrs_b )
            geom_b = QgsGeometry(feat_b.geometry())
            if geom_b.intersects(geom_a):
                success, splits, topo = geom_a.splitGeometry(geom_b.asPolyline(), True) # split polygon by line
                if success == 0:
                    tmp_geom = QgsGeometry(geom_a)
                    for geom in splits: # for each new geometry
                        out_feat.setGeometry(geom)
                        writer.addFeature(out_feat) # add to output layer (with attributes of original feature)
                        tmp_geom = QgsGeometry(tmp_geom.difference(geom))
                    # not quite sure why, but only parts of the split are returned?
                    # so we difference the original feature with the new parts, and
                    # output the resultant feature if it hasn't been completely differnced
                    if not tmp_geom.isGeosEmpty():
                        out_feat.setGeometry(tmp_geom)
                        writer.addFeature(out_feat)
    del writer
