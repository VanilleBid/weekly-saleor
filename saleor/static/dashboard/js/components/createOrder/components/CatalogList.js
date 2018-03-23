import * as React from 'react';
import * as $ from 'jquery';
import PropTypes from 'prop-types';

import CatalogItem from './CatalogItem';

export default class CatalogList extends React.Component {
  static propTypes = {
    selectedCategoryID: PropTypes.number.isRequired,
    searchNameContains: PropTypes.string.optional,
    searchSKUContains: PropTypes.string.optional,
  };
  constructor (props) {
    super(props);

    this.categories = {};
    this.items = {};
  }
  getItemsFromCategoryID (categoryId) {
    /*
     * TODO:
     *   - try to get category products from cache;
     *   - else, get category products data from dashboard API.
     */
    return [];
  }
  getVisibleItems () {
    const res = this.getItemsFromCategoryID(this.props.selectedCategoryID);
    // todo: apply filters here for SKU and name
    return res;
  }
  render () {
    const items = this.getVisibleItems().map(item => {
      return <CatalogItem product-data={ item } key={ item.id } />;
    });
    return items;
  }
}
