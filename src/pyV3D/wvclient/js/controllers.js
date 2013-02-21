'use strict';

/* Controllers */


function WebViewerCtrl($scope, websocketFactory) {
    var url = prompt("Enter server hostname:port", "localhost:8000");
    $scope.socket = websocketFactory("ws://"+url+"/websocket");
    $scope.socket.onopen = function() {
        
    }
}
WebViewerCtrl.$inject = ["$scope", "socket"];




