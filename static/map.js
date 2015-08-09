function build_adapted_url($location,ending){
	return s.sprintf("%s%s",  $location.absUrl(),ending);
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

var app = angular.module('standalonemap', ['openlayers-directive', 'nya.bootstrap.select']);


app.config(function($interpolateProvider){
    $interpolateProvider.startSymbol('{[{').endSymbol('}]}');
});

app.factory('CompilerService', ['$compile', '$templateCache', '$q', '$timeout',
    function ($compile, $templateCache, $q, $timeout) {
        return {
            renderTemplateToString: function(templateName, scope) {
		            var deferred = $q.defer();
		            $timeout(function(){
		               var template = $templateCache.get(templateName);		               
		               var linkFn = $compile(template);
		               var linkedContent = linkFn(scope);
		               scope.$apply();
		               deferred.resolve( linkedContent );
		            }, 0);

		            return deferred.promise;
		    }
        }
    }]);


app.controller("defaultcontroller", [ '$scope','$http','$location', 'CompilerService', 'olData', 'olHelpers', 
	function($scope,$http,$location,CompilerService, olData, olHelpers) {	
	var json_years_promise = $http.get(build_adapted_url($location,"ps/years/?format=json"));
	json_years_promise.then(
		function(result){
			$scope.json_years = result.data;
			
		},
		function(){
			console.log("could not retrive years");
		}
	);

	$scope.year_selection_changed = function(year) {
		if(year){			
			$scope.markers.source.url = build_adapted_url($location,"ps/by_year/"+year.PR_Annee+"/?format=json&type=geojson&lat=PS_Latitude&lon=PS_Longitude");
			popup.hide();
			$scope.show_marker_details_column_was = $scope.show_marker_details_column;
			$scope.show_marker_details_column = false;
		}
	};

	$scope.show_marker_details = function(){
		$scope.show_marker_details_column=true;
		var cur_marker_url = build_adapted_url($location,"ps/item/"+$scope.cur_marker.idgpc_ps+"/?format=json&type=geojson&lat=PS_Latitude&lon=PS_Longitude");
		var cur_marker_promise = $http.get(cur_marker_url);
		cur_marker_promise.then(function(result){			
			$scope.cur_marker = result.data.properties;
			$scope.cur_marker.draft = false;			
			$scope.debug = settings.DEBUG;			
		});
		
	}

	angular.extend($scope, {
		defaults: {
			interactions: {
				mouseWheelZoom: true
			},
			events: {
                layers: [ 'click' ],
                map: [ 'click' ]
            }
		},
		markers : {
			name : 'markers', 
            source: {
                type: 'GeoJSON',
                url: build_adapted_url($location,"ps/?format=json&type=geojson&lat=PS_Latitude&lon=PS_Longitude"),
                projection: 'EPSG:3857'
            },
            style: build_style($location),

        },
        tiles : {
			name : 'tiles',
			source: {
                type: 'OSM',
                url: build_adapted_url($location,"tiles/{z}/{x}/{y}.png"),
            },
        },

	});

	$scope.$on('openlayers.layers.markers.click', function(evt, feature, olEvent) {
			$scope.$apply(function(){
				var coord = feature.getGeometry().getCoordinates();
				console.log(coord);
				$scope.cur_marker = feature.getProperties();
				$scope.cur_marker.draft = true
				var html_promise = CompilerService.renderTemplateToString('popup.html', $scope);				
				html_promise.then(function(html){
			    	popup.show(coord, html);
			    	if($scope.show_marker_details_column_was)
			    		$scope.show_marker_details();
				});
			});	
        });

	$scope.$on('openlayers.map.click', function(evt, feature, olEvent) {
			$scope.$apply(function(){
				popup.hide();
			
				$scope.show_marker_details_column_was = $scope.show_marker_details_column;
				$scope.show_marker_details_column = false;				
			});				
        });

	var popup = new ol.Overlay.Popup();
	olData.getMap().then(function(map) {
		map.addOverlay(popup);		
    });

} ]);
