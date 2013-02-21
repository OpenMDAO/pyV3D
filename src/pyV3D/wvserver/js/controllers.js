'use strict';

/* Controllers */


function CommitsCtrl($scope, $http) {
    $http.get('/tests').
        success(function(data, status, headers, config) {
            $scope.commit_tests = data;
        }).
        error(function(data, status, headers, config) {
            console.log("ERROR while getting /tests");
        });

    /*
        Returns the proper class to bootstrap based on the number of failed or
        skipped tests.
    */
    $scope.outcome = function(test) {
        if (test.fails > 0 || test.passes == 0) {
            return "error";
        }
        return "success";
    };

    $scope.doc_icon = function(docs) {
        if (docs === 'YES') {
            return "icon-ok";
        }
        else if (docs === 'NO') {
            return "icon-warning-sign";
        }
        else {
            return "icon-question-sign";
        }
    }
}
CommitsCtrl.$inject = ['$scope', '$http'];




