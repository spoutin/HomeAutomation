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

    function url(s) {
        var l = window.location;
        return ((l.protocol === "https:") ? "wss://" : "ws://") + l.host + l.pathname + s;
    }

    var dataStream = $websocket(url('websocket/'));
    dataStream.onMessage(function (message) {
        //console.log(message.data);
        var msg = JSON.parse(message.data);
        if ('__control__' in msg) {
            // Control msg
            if (msg.__control__.error) {
                // Error - Fire Message
                alertService.add('danger', msg.__control__.name + ': ' + msg.__control__.message, null, msg.__control__.msg_id);
                return;
            }
            else {
                //add cleaning alert
                alertService.add('success', msg.__control__.name + ': ' + msg.__control__.message, 20000, msg.__control__.msg_id);
                return;
            }
        }
        if (!($scope.units)) {
            return;
        }
        angular.forEach( $scope.units[msg['unit_update']['type']], function(value, key) {
            if (value.clean_name == msg['unit_update']['clean_name']) {
                if (msg['unit_update']['type'] == 'Nest') {
                    $scope.units[msg['unit_update']['type']][key].newTarget = msg['unit_update'].target;
                }
                angular.forEach(msg['unit_update'], function(value1, key1) {
                    //Clear the refresh flag
                    delete $scope.units[msg['unit_update']['type']][key].refresh;
                    //Clear toggle flag
                    delete $scope.units[msg['unit_update']['type']][key].toggle;
                    //Update all values
                    $scope.units[msg['unit_update']['type']][key][key1] = value1
                });
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

        alertService.add = function (type, msg, timeout, msg_id) {
            msg_id = typeof msg_id !== 'undefined' ? msg_id : false;
            var check = 0;
            angular.forEach(alertService.alerts, function(value, key){
                if (value.type == type && value.msg == msg) {
                    check = 1;
                }
                else if (value.msg_id == msg_id && value.msg_id != false){
                    // Check for clearing msg
                    delete alertService.alerts[key]
                }
            });
            if (check == 1) return;
            var index = alertService.alerts.push({ 'type': type, 'msg': msg, 'msg_id': msg_id });
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
    return function (input) {
        return input + '℃';
    };
});
app.filter('round', function () {
    return function (input, decimal) {
        if ((decimal <= 0) || !(decimal)) {
            x = Math.round(input)
        }
        else if (decimal < 1) {
            x = (Math.round(input * 2) / 2).toFixed(1);
        }
        else if (decimal >= 1) {
            decimal = Math.pow(10, decimal);
            x = Math.round(input * decimal) / decimal;
        }
        else {
            x = input
        }
        return x
    }
});

app.filter('humidity', function () {
    return function (input) {
        return input + '%';
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
               state = "Away";
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