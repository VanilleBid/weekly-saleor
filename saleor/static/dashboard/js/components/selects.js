import 'select2';
import {extend} from 'jquery';

function appendOption ($select, option) {
  $select.append($('<option></option>')
    .attr('value', option.id).text(option.text));
}

function initSelects() {
  $('select:not(.browser-default):not(.enable-ajax-select2):not([multiple])').select2({
    width: '100%',
    tags: true,
    minimumResultsForSearch: -1
  });
  $('select[multiple]:not(.browser-default):not(.enable-ajax-select2)').select2({
    width: '100%',
    tags: true
  });

  $('select[data-options]').each((i, select) => {
    const $select = $(select);
    $select.select2({
      width: '100%',
      tags: true
    });
  });

  $('select.enable-ajax-select2:not(.select2-enabled)').each((i, select) => {
    const $select = $(select);
    const initial = $select.data('initial');
    let options = $select.getAttribute('select2-options');

    if (options !== null) {
      options = JSON.parse(options);
    } else {
      options = {};
    }

    if (initial) {
      const initialData = initial instanceof Array ? initial : [initial];
      const selected = initialData.map((item) => {
        appendOption($select, item);
        return (item.id);
      });
      $select.val(selected);
    }

    extend(options, {
      ajax: {
        url: $select.data('url'),
        delay: 250
      },
      width: '100%',
      minimumInputLength: 2
    });

    $select.select2(options);
    $select.addClass('select2-enabled');
  });
}

export {
  initSelects
};
