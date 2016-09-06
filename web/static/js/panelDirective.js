var app = angular.module('customModule', []);

app.factory('debounce', function($timeout) {
    return function(callback, interval) {
        var timeout = null;
        return function() {
            $timeout.cancel(timeout);
            timeout = $timeout(function () {
                callback.apply(this, arguments);
            }, interval);
        };
    };
});
app.directive('myPanel', function () {
    return {
        restrict: 'A',
        templateUrl: 'static/templates/panels.html',
        replace: 'true',
        scope: {
            unitType: '=',
            unitList: '='

        }
    }
});
app.directive('myUnit', function () {
    var controller = ['$scope', '$http', 'alertService','$timeout', 'debounce', function ($scope, $http, alertService, $timeout, debounce) {

        if ($scope.unit.type == 'Nest') {
            $scope.productChanges = 0;
            $scope.$watch('newTarget', debounce(function () {
                console.log('Fired');
                $scope.productChanges++;
            }, 1000), true);
        }

        //Need to write the code to update the nest temperature  -- Above will do the debounce.


        $scope.requestupdate = function ($scope) {
            var that = this;
             $http.post('/api/v1/units/' + this.unit.id)
                .then(
                    function (data, status, headers, config) {
                        //Success
                        console.log(data.status);
                        that.unit.refresh = true;
                    },
                    function (data, status, headers, config) {
                        // Failed
                        alertService.add('warning', 'Error ' + data.status +  ' - Not able to connect to server.  Request Failed!', 20000);
                    }
                );
        };
        $scope.requestToggle = function ($scope) {
            this.unit.toggle = $http.put('/api/v1/units/' + this.unit.id + '/toggle/')
                .then(
                    function (data, status, headers, config) {
                        //Success
                        console.log(data.status);
                        return true;
                    },
                    function (data, status, headers, config) {
                        // Failed
                        console.log("Failed: " + data.status);
                    }
                );
        };
    }];
    return {
        restrict: 'A',
        replace: 'true',
        scope: {
            unit: '=',
            type: '&'
        },
        link: function (scope, element, attrs) {
            // some ode
        },
        templateUrl: function (elem, attrs) {
            return '/static/templates/' + attrs.type + '.html' || '/static/templates/generic.html'
        },
        controller: controller
    }
});