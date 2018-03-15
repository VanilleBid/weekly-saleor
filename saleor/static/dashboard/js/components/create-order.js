import 'angular';

const angular = window.angular;

function initCreateOrderAngularApp () {
  const app = angular.module('createOrderForm', []).config(
    function($interpolateProvider) {
      $interpolateProvider.startSymbol('[[').endSymbol(']]');
    }
  );
  app.controller('productList', ['$scope', function ($scope) {
    $scope.selected_category = {category_id: 1, category_name: null};
    $scope.category_id = null;
    const select = $('select#id_category');
    select.on('select2:select', function (e) {
      $scope.category_id = parseInt(e.params.data.id);
      $scope.selected_category.category_name = e.params.data.text.replace(/^(-{3})+/g, '');
      $scope.$apply();
    });
    let i = 0;
    $scope.products = this.products = [
      {'category_id': 1, 'name': 'item ' + ++i},
      {'category_id': 1, 'name': 'item ' + ++i},
      {'category_id': 1, 'name': 'item ' + ++i},
      {'category_id': 1, 'name': 'item ' + ++i},
      {'category_id': 1, 'name': 'item ' + ++i},
      {'category_id': 1, 'name': 'item ' + ++i},
      {'category_id': 1, 'name': 'item ' + ++i}
    ];
  }]);
}

export {
  initCreateOrderAngularApp
};
