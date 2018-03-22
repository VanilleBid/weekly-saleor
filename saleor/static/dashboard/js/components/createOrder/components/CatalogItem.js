import * as React from 'react';

export default class CatalogItem extends React.Component {
  constructor (data) {
    super();
    this.data = data;
    this.variants = [];
    this.inCartCount = 0;
    this.productAttributes = {};
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
        <a ng-href="[[ product.url ]]" target="_blank" className="img-container">
          <div className="img-overlay"></div>
          <img src={ this.getFirstImage() } className="responsive-img" />
        </a>

        <div className="card-content">
          <div className="card-title">
            { this.name }
          </div>

          <div className="table-toggle">
            { /* TODO handle it in ReactJS */ }
            <span ng-click="show=!show" is-toggled="[[show]]"></span>
          </div>

          { /* TODO handle it in ReactJS */ }
          <table ng-show="show">
            {this.productAttributes.map(
              (attributeName, i) => (
                <tr>
                  <td>{ attributeName }</td>
                  <td>
                    <strong>
                      { this.productAttributes[attributeName].name || this.productAttributes[attributeName] }
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
                    <input type="number" min="0" value="0" className="right"
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
