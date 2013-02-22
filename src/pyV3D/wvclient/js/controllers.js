'use strict';

/* Controllers */

function WebViewerCtrl($scope, websocketFactory) {
/*    var wsURLp = prompt("Enter server hostname:port", "localhost:8000");
    wsURLp = "ws://"+wsURLp;
    var socketGp = websocketFactory(wsURLp, "gprim-binary-protocol");

    socketGp.binaryType = 'arraybuffer';
    socketGp.onopen = function(evt) { 
        logger(" Gprim-binary WebSocket Connected!");
    };
    socketGp.onclose = function(evt) { 
        logger(" Gprim-binary WebSocket Disconnected!");
    };
    socketGp.onmessage = function(evt) { 
      g.messageQ.push(evt.data);   
    };
    socketGp.onerror = function(evt) { 
        alert(" Not connected to Server: Try reloading the page!");
        logger(" Gprim-binary WebSocket Error: " + evt.data);
    };
    $scope.socketGp = socketGp;

    var socketUt = websocketFactory(wsURLp, "ui-text-protocol");
    socketUt.onopen = function(evt) { 
        logger(" UI-text WebSocket Connected!");
    };
    socketUt.onclose = function(evt) { 
        logger(" UI-text WebSocket Disconnected!");
    };
    socketUt.onmessage = function(evt) { 
        wvServerMessage(evt.data);
    };
    socketUt.onerror = function(evt) { 
        logger(" UI-text WebSocket Error: " + evt.data);
    };
    $scope.socketUt = socketUt;

    $scope.messageQ = [];              // a place to put the binary messages}*/
    wvStart();
};

WebViewerCtrl.$inject = ["$scope", "websocketFactory"];




