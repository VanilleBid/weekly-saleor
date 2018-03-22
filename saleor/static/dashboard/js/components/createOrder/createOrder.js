import 'angular';

const angular = window.angular;

function initCreateOrderAngularApp () {
  const app = angular.module('createOrderForm', []).config(
    function($interpolateProvider) {
      $interpolateProvider.startSymbol('[[').endSymbol(']]');
    }
  );
  app.controller('productList', ['$scope', '$http', function ($scope, $http) {
    const $baseContainer = $('#order-products');
    const $orderNotesField = $('#id_note')[0];
    const $customerIDField = $('#_customer_id')[0];
    $scope.errors = [];
    $scope.discount = {type: 'fixed', value: '0.00', discount: 0, discountedTotal: ''};
    $scope.products = [];
    const submitURL = $baseContainer.attr('submit-url');
    $http({
      url: $baseContainer.attr('json-url')
    }).then(function successCallback(response) {
      // this callback will be called asynchronously
      // when the response is available
      $scope.products = response.data;
    }, function errorCallback(response) {
      // called asynchronously if an error occurs
      // or server returns response with an error status.
      $scope.error = response.statusText;
    });
    function parseDiscount(typeAsStr, value, cartTotal) {
      let res = cartTotal = cartTotal ? strFloatToInt(cartTotal) : 0;
      $scope.discount.discount = 0;

      if (value && cartTotal) {
        $scope.discount.discount = value = strFloatToInt(value);
        if (typeAsStr === 'percentage') {
          res = cartTotal - Math.floor((cartTotal * value) / 10000);
        } else {
          res = cartTotal - value;
        }
      }
      return Math.max(res, 0);
    }
    $scope.getDiscount = function(cartTotal) {
      const value = parseDiscount($scope.discount.type, $scope.discount.value, cartTotal);
      $scope.discount.discountedTotal = intToDecimal(value);
      return value;
    };
    function intToDecimal (val) {
      val = '' + val;
      return val.slice(0, -2) + '.' + val.slice(-2);
    }
    function strFloatToInt (s) {
      const oneDigitDecimalPos = s.length - 2;
      if (s[oneDigitDecimalPos] === '.') {
        s += '0';
      } else if (s[oneDigitDecimalPos - 1] !== '.') {
        s += '.00';
      }
      return parseInt(s.replace('.', ''));
    }
    $scope.cartTotal = 0;
    $scope.resetCartTotal = function () {
      $scope.cartTotal = 0;
    };
    $scope.getCartTotal = function () {
      if ($scope.cartTotal) {
        let total = $scope.cartTotal;
        return intToDecimal(total);
      }
      return '0.00';
    };
    $scope.getPrice = function (variant) {
      if (!variant._unitPrice) {
        variant._unitPrice = strFloatToInt(variant.unit_price);
      }
      const unitPrice = variant._unitPrice;
      const total = unitPrice * parseInt(variant.in_cart);
      $scope.cartTotal += total;
      return intToDecimal(total);
    };
    $scope.greaterThan = function(prop, val) {
      return function(item) {
        return item[prop] > val;
      };
    };
    $scope.category_id = null;
    const select = $('select#id_category');
    select.on('select2:select', function (e) {
      $scope.category_id = parseInt(e.params.data.id);
      $scope.category_name = e.params.data.text.replace(/^(-{3})+/g, '');
      $scope.$apply();
    });
    $scope.submitForm = function () {
      const cart = [];
      $scope.products.forEach((product) => {
        if (product.variants) {
          product.variants.forEach((variant) => {
            if (variant.in_cart && variant.in_cart > 0) {
              cart.push([
                variant.variant_id,
                variant.in_cart
              ]);
            }
          });
        }
      });
      const data = {
        products: cart,
        discount: $scope.discount.value,
        discount_type: $scope.discount.type,
        note: $orderNotesField.value,
        is_shipping_required: false,
        shipping_address: null,
        billing_address: null,
        shipping_method: null,
        is_shipping_same_as_billing: true
      };

      if ($customerIDField !== undefined) {
        data['customer'] = $customerIDField.value;
      }

      $.ajax({
        method: 'POST',
        url: submitURL,
        data: JSON.stringify(data),
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        traditional: true,
        headers: {
          'X-CSRFToken': $.cookie('csrftoken')
        }
      }).then((data, status, headers) => {
        if (headers.status === 200) {
          window.location = data['location'];
        }
      },
      (data, status, headers) => {
        const errors = data.responseJSON.errors;
        if (typeof errors === typeof []) {
          $scope.errors = ['Some fields weren\'t filled. Please review your submission.'];
          // TODO: $scope.errors = errors;
        } else {
          $scope.errors = ['Unexpected response from server (' + status + ')', data.responseText];
        }
        $scope.$apply();
      });
    };
  }]);
}

export {
  initCreateOrderAngularApp
};
