'use strict';


// Declare app level module which depends on filters, and services
var myApp = angular.module('myApp', ['myApp.filters', 'myApp.services', 'myApp.directives'])

myApp.config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/', {templateUrl: 'partials/commits.html', controller: CommitsCtrl});
    $routeProvider.when('/commits', {templateUrl: 'partials/commits.html', controller: CommitsCtrl});
    $routeProvider.otherwise({redirectTo: '/'});
  }]);

