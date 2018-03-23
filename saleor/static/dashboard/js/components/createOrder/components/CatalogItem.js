import * as React from 'react';
import * as $ from 'jquery';
import PropTypes from 'prop-types';

export default class CatalogItem extends React.Component {
  static propTypes = {
    productData: PropTypes.shape({
      name: PropTypes.string.isRequired,
      url: PropTypes.string.isRequired,
      product_images: PropTypes.arrayOf(PropTypes.string.isRequired),
      variants: PropTypes.arrayOf(PropTypes.shape({
        variant_id: PropTypes.number.isRequired,
        sku: PropTypes.string.isRequired,
        in_stock: PropTypes.number.isRequired,
        unit_price: PropTypes.string.optional
      }))
    }).isRequired
  };

  constructor (props) {
    super(props);

    this.data = props.productData;
    this.variants = this.data.variants;

    // initialize each variant
    this.variants.forEach((variant) => {
      variant.inCartCount = 0;
    });
  }
  getFirstImage() {
    return this.data.product_images[0] || '/static/images/placeholder540x540.png';
  }
  handleVariantCartChange (e, variant) {
    // todo
  }
  render () {
    return (
      <div className="card">
        <a href={ this.data.url } target="_blank" className="img-container">
          <div className="img-overlay" />
          <img src={ this.getFirstImage() } className="responsive-img" />
        </a>

        <div className="card-content">
          <div className="card-title">
            { this.data.name }
          </div>

          <div className="table-toggle">
            { /* TODO handle it in ReactJS */ }
            <span ng-click="show=!show" data-is-toggled="[[show]]" />
          </div>

          { /* TODO handle it in ReactJS */ }
          <table ng-show="show">
            {$.each(this.data.attributes,
              (attributeName, attributeValue) => (
                <tr>
                  <td>{ attributeName }</td>
                  <td>
                    <strong>
                      { attributeValue.name || attributeValue }
                    </strong>
                  </td>
                </tr>
              )
            )}
          </table>
        </div>

        <div className="card-action">
          <div className="small">
            {this.variants.forEach(
              (variant) => (
                <div className="product-entry">
                  <span>{ variant.sku } — { variant.unit_price }€ </span>
                  <label>
                    <span className="right help-cursor" title="% trans 'in stock' %">{ variant.in_stock }</span>
                    <input type="number" min="0" value={ variant.inCartCount } className="right"
                      onChange={this.handleVariantCartChange(this, {variant})} />
                  </label>
                </div>
              )
            )}
          </div>
        </div>
      </div>
    );
  }
}
