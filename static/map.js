//reload page if angular has failed to load

function check_page_load(wait_time){
	setTimeout(function(){
		if($(".nya-bs-select li").length<2){
			console.log("Page didn't load properly, retrying...");
			location.reload();
			check_page_load(wait_time*2);
		} 
	}, wait_time);
}

check_page_load(5000);

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

	$scope.debug = settings.DEBUG;
	if($.browser.msie && $.browser.versionNumber<11)
		$scope.mapHeight = (window.innerHeight-100);

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
			$scope.cur_marker.coordinates = [result.data.geometry.coordinates[0],result.data.geometry.coordinates[1]];
			$scope.cur_marker.draft = false;			
			$scope.debug = settings.DEBUG;			
		});
		
	}

	$scope.debug_update_cur_marker = function(){
		var cur_marker_url = build_adapted_url($location,"ps/item/"+$scope.cur_marker.idgpc_ps+"/?format=json");
		var payload = {
				"PS_Longitude" : $scope.cur_marker.coordinates[0],
				"PS_Latitude" : $scope.cur_marker.coordinates[1],
				"PS_Nom" : $scope.cur_marker.PS_Nom,
				"PS_Nat" : $scope.cur_marker.PS_Nat
			};
		if($scope.cur_marker.mark_as_reliable)
			payload = angular.extend({"PS_Confiance" : 0}, payload);

		var cur_marker_promise = $http.patch(cur_marker_url,payload);

		cur_marker_promise.then(function(result){			
			$scope.markers.source.url = build_adapted_url($location,"ps/?format=json&type=geojson&lat=PS_Latitude&lon=PS_Longitude");
			if(popup.visible){
				var newCoord = ol.proj.transform($scope.cur_marker.coordinates, 'EPSG:4326', 'EPSG:3857');
				popup.show(newCoord);
			}
			$scope.markers.source.refresh = !$scope.markers.source.refresh;
		});
	}

	$scope.debug_is_editable = function(marker){
		return marker && marker.PS_Confiance && parseInt(marker.PS_Confiance)>0;
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
		map.updateSize();
		if($.browser.msie && $.browser.versionNumber<11){
			$scope.mapHeight = (window.innerHeight-100);
			setTimeout( function() { map.updateSize();}, 200);	
			setTimeout( function() { map.updateSize();}, 2000);	
		}
    });

} ]);
