'use strict';

/* Filters */

angular.module('myApp.filters', []).
  filter('newlines', function() {
  	/* This filter just adds line breaks so a multi-line string will display properly
  	   as html.
  	*/
  	return function(text) {
  		if (typeof text === 'undefined') {
  			return ''
  		}
    	return text.replace(/\n/g, '<br/>');	
  	}
  });
