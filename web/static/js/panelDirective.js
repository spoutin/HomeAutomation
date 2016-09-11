var app = angular.module('customModule', []);

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
    var controller = ['$scope', '$http', 'alertService','$timeout','$filter', function ($scope, $http, alertService, $timeout, $filter) {

        if ($scope.unit.type == 'Nest') {
            $scope.unit.newTarget = $scope.unit.target;
        }

        $scope.actionChangeTemp = function (amount) {
            var delayInMs = 2000;
            this.unit.newTarget = this.unit.newTarget + amount;
            var unit = this.unit;
            $timeout.cancel(unit.timeoutPromise);  //does nothing, if timeout alrdy done
            unit.timeoutPromise = $timeout(function() {   //Set timeout
                var message = {'temperature': unit.newTarget};
                $scope.changeTemp(unit, message)
            }, delayInMs, true, unit);
        };

        $scope.toggleAway = function () {
            var unit = this.unit;
            unit.refresh = true;
            var url = '/api/v1/units/' + this.unit.id + '/toggle_away/';
            var data = '';
            $http.put(url, data, unit).then(
                function () {
                    // This function handles success
                    $scope.requestupdate();
                },
                function (data) {
                    // this function handles error
                    unit.refresh = false;
                    alertService.add('warning', 'Error ' + data.status + ': Unable toggle Away/Home!', 20000);
                });
        };

        $scope.changeTemp = function (unit, message) {
            unit.refresh = true;
            var url = '/api/v1/units/' + unit.id + '/update_temperature/';
            var data = JSON.stringify(message);
            $http.put(url, data).then(
                function (data) {
                    // This function handles success
                    $scope.requestupdate();
                    alertService.add('success', 'Nest temperature adjusted to ' + $filter('round')(unit.newTarget,.5) +'!', 20000);
                },
                function (data) {
                    // this function handles error
                    unit.refresh = false;
                    unit.newTarget = unit.target;
                    alertService.add('warning', 'Error ' + data.status + ': Unable to adjust the Nest temperature!', 20000);
                });
        };

        $scope.requestupdate = function () {
            var that = this;
            this.unit.refresh = true;
             $http.post('/api/v1/units/' + this.unit.id)
                .then(
                    function (data, status, headers, config) {
                        //Success
                    },
                    function (data) {
                        // Failed
                        that.unit.refresh = false;
                        alertService.add('warning', 'Error ' + data.status +  ' - Not able to connect to server.  Request Failed!', 20000);
                    }
                );
        };
        $scope.requestToggle = function () {
            var that = this;
            this.unit.toggle = true;
            $http.put('/api/v1/units/' + this.unit.id + '/toggle/')
                .then(
                    function () {
                        //Success
                    },
                    function (data) {
                        // Failed  Need to clear the toggle toggle and raise an alarm.
                        alertService.add('warning', 'Error ' + data.status +  ' - Toggle request failed for ' + that.unit.name + '..  Request Failed!', 20000);
                        that.unit.toggle = false;
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