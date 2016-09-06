/**
 * Created by ablack on 8/29/2016.
 */

var app = angular.module('myApp', ['customModule', 'ngWebSocket']);
units = [];
app.controller('myCtrl', function ($scope, $http, $websocket, alertService) {
    $http.get("/api/v1/units/")
        .then(
            function (response) {
                //success
                $scope.units = response.data;
            },
            function (response) {
                //failed
                alertService.add('danger', 'Error ' + response.status + ' - Unable to get list of Units');
            }
        );
    var dataStream = $websocket('ws://localhost:8888/websocket/');
    dataStream.onMessage(function (message) {
        //console.log(message.data);
        var msg = JSON.parse(message.data);
        if (!($scope.units)) {
            return;
        }
        angular.forEach( $scope.units[msg['unit_update']['type']], function(value, key) {
            if (value.clean_name == msg['unit_update']['clean_name']) {
               $scope.units[msg['unit_update']['type']][key] = msg['unit_update']
            }
        });
    }).onError(function (err) {
        alertService.add('danger', 'Error - Unable connect to websocket');
    });
});
app.factory('alertService', ['$timeout', function ($timeout) {
        var alertService = {};

        // create an array of alerts
        alertService.alerts = [];

        alertService.add = function (type, msg, timeout) {
            var index = alertService.alerts.push({ 'type': type, 'msg': msg });
            if (!(timeout === undefined || timeout === null)) {
                $timeout(function (index) {alertService.closeAlert(index)}, timeout);
            }
        };

        alertService.closeAlert = function (index) {
            alertService.alerts.splice(index, 1);
        };

        return alertService;
    }]);
app.directive('myAlertDisplay', ['alertService', function (alertService) {
        return {
            restrict: 'AE',
            template: '<div ng-repeat="alert in vm.alerts" class="alert alert-{{alert.type}}" role="alert"><button ng-click="vm.closeAlert($index)" type="button" class="close" aria-label="Close"><span aria-hidden="true">&times;</span></button>{{alert.msg}}</div>',
            controller: function(){
                var vm = this;
                vm.alertService = alertService;

                vm.alerts = vm.alertService.alerts;

                vm.closeAlert = function (index) {
                    vm.alertService.closeAlert(index);
                }
            },
            controllerAs: 'vm'
            }
    }]);
app.filter('temperature', function () {
    return function (input, half) {
        var x = 0;
        if (half)  {
            x = (Math.round(input * 2) / 2).toFixed(1)
        }
        else {
            x = Math.round(input * 100) / 100;
        }
        return x + '℃';
    };
});
app.filter('humidity', function () {
    return function (input, half) {
        var x = 0;
        if (half)  {
            x = (Math.round(input * 2) / 2).toFixed(1)
        }
        else {
            x = input
        }
        return x + '%';
    };
});
app.filter('state', function () {
   return function (input) {
       var state = "";
       switch(input) {
           case 0:
               state = "Off";
               break;
           case 1:
               state = "On";
               break;
           default:
               state = "Unknown";
               break;
       }
       return state;
   };
});
app.filter('nestAway', function () {
   return function (input) {
       var state = "";
       switch(input) {
           case false:
               state = "Home";
               break;
           case true:
               state = "On";
               break;
           default:
               state = "Unknown";
               break;
       }
       return state;
   };
});
app.filter('capitalize', function() {
    return function(input) {
      return (!!input) ? input.charAt(0).toUpperCase() + input.substr(1).toLowerCase() : '';
    }
});
app.filter('distance', function() {
    return function(input) {
        var distance = "";
        if (input > 0) {
            distance = input + ' cm'
        }
        else if (input) {
            distance = 'Error'
        }
        else {
            distance = "Unknown"
        }
        return distance
    }
});