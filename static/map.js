/*

TODO: in the real version, the array should be generated by a php script and requested for example via ajax.
Or this file can also be php-generated.

*/

var app = angular.module('standalonemap', ['openlayers-directive']);
app.config(function($interpolateProvider){
    $interpolateProvider.startSymbol('{[{').endSymbol('}]}');
});
app.controller("defaultcontroller", [ '$scope','$http', function($scope,$http) {
	angular.extend($scope, {
			defaults: {
				interactions: {
					mouseWheelZoom: true
				}
			},
			
		});

	 $http.get('http://dtserv.labscinet.com/ps/?format=json').
        success(function(data) {
            var markers = [];
            for (var i in data) {
			  markers.push({
			  	name: data[i].PS_Nom,
			  	lat: parseFloat(data[i].PS_Latitude),
				lon: parseFloat(data[i].PS_Longitude),
				label: {
					details: data[i].PS_Nom,
					show: false
				},
				onClick: blank
			  });
			}

			markers.push({
			  	name: 'Lyon',
				lat: 45.7600,
				lon: 4.8400,
				label: {
					details: 'Lyon',
					show: false
				},
				onClick: blank
			  });

			angular.extend($scope, {
				markers : markers
			});
        });
	

	function blank(){}

	$scope.close_marker = function(marker) {
		$('canvas').click(); //propagate event to close popups (workaround)
	}
	$scope.select_marker = function(marker) {
		$scope.cur_marker = marker;
		$scope.cur_message = "eventuellement plus de details ici...";
	};
} ]);
