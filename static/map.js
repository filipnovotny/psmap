function build_adapted_url($location,ending){
	return s.sprintf("%s://%s%s%s/%s", $location.protocol(),$location.host(),$location.port()==80?"":":"+$location.port(),$location.path(),ending);
}

function make_marker_style($location, name){
    return new ol.style.Style({
				image: new ol.style.Icon({
		                anchor: [0.5, 1],
		                anchorXUnits: 'fraction',
		                anchorYUnits: 'fraction',
		                scale : 1,
		                src: build_adapted_url($location,s.sprintf('static/img/%s.png',name))
		        })
		    });
}

function build_style($location){
	return function _build_style(feature){
		var props = feature.getProperties();
		if(settings.DEBUG){
			var style = make_marker_style($location,settings.MARKER_LABELS[props.PS_Confiance]);
		}else{
			var style = make_marker_style($location,"marker_blue");	
		}
		
		return [style];
	}
}
var app = angular.module('standalonemap', ['openlayers-directive']);
app.config(function($interpolateProvider){
    $interpolateProvider.startSymbol('{[{').endSymbol('}]}');
});

app.controller("defaultcontroller", [ '$scope','$http','$location','olData', 'olHelpers', function($scope,$http,$location,olData, olHelpers) {
	angular.extend($scope, {
			defaults: {
				interactions: {
					mouseWheelZoom: true
				},
				events: {
                    layers: [ 'mousemove', 'click' ]
                }
			},
			markers : {
				name : 'markers', 
	            source: {
	                type: 'GeoJSON',
	                url: build_adapted_url($location,"ps/?format=json&type=geojson&lat=PS_Latitude&lon=PS_Longitude"),
	            },
	            style: build_style($location),

	        },

		});
	var popup = new ol.Overlay.Popup();
	olData.getMap().then(function(map) {
		map.addOverlay(popup);
		$scope.$on('openlayers.layers.markers.click', function(evt, feature, olEvent) {
				var coord = map.getEventCoordinate(olEvent);
				var props = feature.getProperties();
			    popup.show(coord, props.PS_Nom);
            });
        });
} ]);
