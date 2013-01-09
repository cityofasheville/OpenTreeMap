tm.map_center_lon = -82.548525;
tm.map_center_lat = 35.595564;
tm.start_zoom = 11;
tm.add_start_zoom = 13;
tm.add_zoom = 16;
tm.edit_zoom = 16;
tm.initial_location_string = "City of Asheville";
tm.initial_species_string = "All trees";
tm.popup_minSize = new OpenLayers.Size(250,200);
tm.popup_maxSize = new OpenLayers.Size(250,450);
tm.google_bounds = new google.maps.LatLngBounds(new google.maps.LatLng(35.20,-82.59), new google.maps.LatLng(35.50, -82.4));
tm.geo_layer = "asheville_trees"
tm.geo_layer_style = ""
tm.panoAddressControl = false;



function detectmob() { 
 if( navigator.userAgent.match(/Android/i)
 || navigator.userAgent.match(/webOS/i)
 || navigator.userAgent.match(/iPhone/i)
 || navigator.userAgent.match(/iPad/i)
 || navigator.userAgent.match(/iPod/i)
 || navigator.userAgent.match(/BlackBerry/i)
 || navigator.userAgent.match(/Windows Phone/i)
 ){
    return true;
  }
 else {
    return false;
  }
}

isMobile = detectmob();

tm.init_base_map = function(div_id, controls){
    if (!div_id) {
        div_id = "map";
    };
    if (!controls) {
        if(isMobile){
	    tm.map = new OpenLayers.Map(div_id, {
            maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34, 20037508.34, 20037508.34),
            restrictedExtent: new OpenLayers.Bounds(-9352949.884372,4008577.702163,-8787275.141121,4611248.307428), 
            units: 'm',
            projection: new OpenLayers.Projection("EPSG:900913"),
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            controls: [
	   	       new OpenLayers.Control.Attribution(),
                       new OpenLayers.Control.Navigation(),
                       new OpenLayers.Control.ArgParser(),
                       new OpenLayers.Control.PanPanel(),
	               new OpenLayers.Control.TouchNavigation({
			dragPanOptions: {
				enableKinetic: isMobile
			},
			pinchZoom: new  OpenLayers.Control.PinchZoom({autoActivate: isMobile}),
			clickHandlerOptions: {
				handleSingle: function(e){ 
				var mapCoord = tm.map.getLonLatFromViewPortPx(e.xy);
				mapCoord.transform(tm.map.getProjectionObject(), new OpenLayers.Projection("EPSG:4326"));           
				tm.clckTimeOut = window.setTimeout(function() {
				singleClick(mapCoord); 
				},500); 
			       }
			}
                       }),
                       new OpenLayers.Control.ZoomPanel()]
        });
      }else{
	    tm.map = new OpenLayers.Map(div_id, {
            maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34, 20037508.34, 20037508.34),
            restrictedExtent: new OpenLayers.Bounds(-9352949.884372,4008577.702163,-8787275.141121,4611248.307428), 
            units: 'm',
            projection: new OpenLayers.Projection("EPSG:900913"),
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            controls: [
	   	       new OpenLayers.Control.Attribution(),
                       new OpenLayers.Control.Navigation(),
                       new OpenLayers.Control.ArgParser(),
                       new OpenLayers.Control.PanPanel(),
                       new OpenLayers.Control.ZoomPanel()]
        });
      };
    }
    else {
        tm.map = new OpenLayers.Map(div_id, {
            //maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34, 20037508.34, 20037508.34),
            //restrictedExtent: new OpenLayers.Bounds(-8552949.884372,4608577.702163,-7987275.141121,5011248.307428), 
            maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34, 20037508.34, 20037508.34),
            restrictedExtent: new OpenLayers.Bounds(-9352949.884372,4008577.702163,-8787275.141121,4611248.307428), 
            units: 'm',
            //projection: new OpenLayers.Projection("EPSG:900913"),
            projection: new OpenLayers.Projection("EPSG:900913"), //102100
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            controls: controls
        });
    }
    
//        tm.baseLayer = new OpenLayers.Layer.XYZ("ArcOnline", 
//            "http://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/${z}/${y}/${x}.jpg", 
//           {
//              sphericalMercator: true
//            }
//        );

//      tm.baseLayer = new OpenLayers.Layer.VirtualEarth("Streets", {
//        type: VEMapStyle.Shaded,
//        sphericalMercator: true,
//        animationEnabled: false,
//        numZoomLevels: 20,
//        MAX_ZOOM_LEVEL: 20,
//        MIN_ZOOM_LEVEL: 0
//    });
  
//    tm.aerial = new OpenLayers.Layer.VirtualEarth("Hybrid", {
//        type: VEMapStyle.Hybrid,            
//        sphericalMercator: true,
//        animationEnabled: false, 
//        numZoomLevels: 20,
//        MAX_ZOOM_LEVEL: 20,
//        MIN_ZOOM_LEVEL: 0
//    });

   tm.baseLayer = new OpenLayers.Layer.Google("Google Streets", {
        sphericalMercator: true,
        numZoomLevels: 21
    });
  
    tm.aerial = new OpenLayers.Layer.Google("Hybrid", {
        type: google.maps.MapTypeId.HYBRID,            
        sphericalMercator: true,
        numZoomLevels: 21
    });

    //tm.aerial = new OpenLayers.Layer.WMS("Hybrid", "http://imagery.nconemap.com/arcgis/services/2010_Orthoimagery/ImageServer/WMSServer",
    //   {
    //        sphericalMercator: true,
    //        layername: '2010_Orthoimagery' ,
    //        type: 'png'
    //});
    
    tm.tms = new OpenLayers.Layer.TMS('TreeLayer', 
        tm_urls.tc_url,
        {
            layername:  tm_urls.tc_layer_name,
            type: 'png',
            isBaseLayer: false,
            //opacity:0.7, causes issues with IE and bing layer. 
            wrapDateLine: true,
            attribution: "(c) AshvilleTreeMap.org"
        }
    );
    tm.tms.buffer = 0;
    tm.baseLayer.buffer = 0;
    tm.aerial.buffer = 0;
    tm.map.addLayers([tm.aerial, tm.baseLayer, tm.tms]);
    tm.map.setBaseLayer(tm.baseLayer);

        function singleClick(olLonlat) { 
            window.clearTimeout(tm.clckTimeOut); 
            tm.clckTimeOut = null; 
            var spp = jQuery.urlParam('species');
            jQuery.getJSON(tm_static + 'trees/location/',
              {'lat': olLonlat.lat, 'lon' : olLonlat.lon, 'format' : 'json', 'species':spp},
            tm.display_tree_details);
	    //alert('test');
        } 
};
