import { observer } from 'mobx-react';
import React, { Component, PropTypes } from 'react';

@observer
export default class VariantPrice extends Component {

  static propTypes = {
    availability: PropTypes.object.isRequired,
    store: PropTypes.object
  }

  render() {
    let priceText, priceUndiscountedText, priceLocalCurrency, isDiscount;
    const { availability, store } = this.props;
    const variant = store.variant;
    if (!store.isEmpty) {
      // variant price
      isDiscount = variant.taxedPrice.gross !== variant.taxedPriceUndiscounted.gross;
      priceText = `${variant.taxedPrice.grossLocalized}`;
      priceUndiscountedText = `${variant.taxedPriceUndiscounted.grossLocalized}`;
      if (variant.priceLocalCurrency) {
        priceLocalCurrency = variant.priceLocalCurrency.grossLocalized;
      }
    } else {
      // if there's no variant, fall back to product price
      const { discount, taxedPriceRange, taxedPriceRangeUndiscounted } = availability;
      isDiscount = discount && !!Object.keys(discount).length;
      priceText = `${taxedPriceRange.minPrice.grossLocalized}`;
      priceUndiscountedText = `${taxedPriceRangeUndiscounted.minPrice.grossLocalized}`;
      if (availability.priceRangeLocalCurrency) {
        priceLocalCurrency = availability.priceRangeLocalCurrency.minPrice.grossLocalized;
      }
    }
    return (
      <h2 className="product__info__price">
          <span>{priceText}&nbsp;</span>
          {isDiscount && (
            <small className="product__info__price__undiscounted">{priceUndiscountedText}</small>
          )}
          {priceLocalCurrency && (
            <p><small className="text-info">&asymp; {priceLocalCurrency}</small></p>
          )}
      </h2>
    );
  }
}
