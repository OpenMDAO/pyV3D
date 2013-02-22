'use strict';

/* Services */

angular.module('WebViewerApp.services', []).
    factory('websocketFactory', function($window) {
        if ('WebSocket' in $window) {
            return function(url) { return new WebSocket(url); }
        } 
        else if ('MozWebSocket' in $window) {
            return function(url) { return new MozWebSocket(url); }
        }
        return undefined;
    });
