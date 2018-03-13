(function(window, factory) {
  const lazySizes = factory(window, window.document);
  window.lazySizes = lazySizes;
  if (typeof module === 'object' && module.exports) {
    module.exports = lazySizes;
  }
}(window, function l(window, document) {
  'use strict';
  /* jshint eqnull:true */
  if (!document.getElementsByClassName) { return; }

  let lazySizesConfig;

  const docElem = document.documentElement;
  const supportPicture = window.HTMLPictureElement && ('sizes' in document.createElement('img'));
  const _addEventListener = 'addEventListener';
  const _getAttribute = 'getAttribute';
  const addEventListener = window[_addEventListener];
  const setTimeout = window.setTimeout;
  const rAF = window.requestAnimationFrame || setTimeout;
  const regPicture = /^picture$/i;
  const loadEvents = ['load', 'error', 'lazyincluded', '_lazyloaded'];
  const regClassCache = {};
  const forEach = Array.prototype.forEach;

  const hasClass = function(ele, cls) {
    if (!regClassCache[cls]) {
      regClassCache[cls] = new RegExp('(\\s|^)' + cls + '(\\s|$)');
    }
    return regClassCache[cls].test(ele[_getAttribute]('class') || '') && regClassCache[cls];
  };

  const addClass = function(ele, cls) {
    if (!hasClass(ele, cls)) {
      ele.setAttribute('class', (ele[_getAttribute]('class') || '').trim() + ' ' + cls);
    }
  };

  const removeClass = function(ele, cls) {
    let reg;
    if ((reg = hasClass(ele, cls))) {
      ele.setAttribute('class', (ele[_getAttribute]('class') || '').replace(reg, ' '));
    }
  };

  const addRemoveLoadEvents = function(dom, fn, add) {
    const action = add ? _addEventListener : 'removeEventListener';
    if (add) {
      addRemoveLoadEvents(dom, fn);
    }
    loadEvents.forEach(function(evt) {
      dom[action](evt, fn);
    });
  };

  const triggerEvent = function(elem, name, detail, noBubbles, noCancelable) {
    const event = document.createEvent('CustomEvent');

    event.initCustomEvent(name, !noBubbles, !noCancelable, detail || {});

    elem.dispatchEvent(event);
    return event;
  };

  const updatePolyfill = function (el, full) {
    let polyfill;
    if (!supportPicture && (polyfill = (window.picturefill || lazySizesConfig.pf))) {
      polyfill({reevaluate: true, elements: [el]});
    } else if (full && full.src) {
      el.src = full.src;
    }
  };

  const getCSS = function (elem, style) {
    return (getComputedStyle(elem, null) || {})[style];
  };

  const getWidth = function(elem, parent, width) {
    width = width || elem.offsetWidth;

    while (width < lazySizesConfig.minSize && parent && !elem._lazysizesWidth) {
      width = parent.offsetWidth;
      parent = parent.parentNode;
    }

    return width;
  };

  const throttle = function(fn) {
    let running;
    let lastTime = 0;
    const Date = window.Date;
    const run = function() {
      running = false;
      lastTime = Date.now();
      fn();
    };
    const afterAF = function() {
      setTimeout(run);
    };
    const getAF = function() {
      rAF(afterAF);
    };

    return function() {
      if (running) {
        return;
      }
      let delay = 125 - (Date.now() - lastTime);

      running = true;

      if (delay < 6) {
        delay = 6;
      }
      setTimeout(getAF, delay);
    };
  };

  const loader = (function() {
    let lazyloadElems, preloadElems, isCompleted, resetPreloadingTimer, loadMode, started;
    let eLvW, elvH, eLtop, eLleft, eLright, eLbottom;
    let defaultExpand, preloadExpand, hFac;

    const regImg = /^img$/i;
    const regIframe = /^iframe$/i;

    const supportScroll = ('onscroll' in window) && !(/glebot/.test(navigator.userAgent));

    let shrinkExpand = 0;
    let currentExpand = 0;

    let isLoading = 0;
    let lowRuns = 0;

    const resetPreloading = function(e) {
      isLoading--;
      if (e && e.target) {
        addRemoveLoadEvents(e.target, resetPreloading);
      }

      if (!e || isLoading < 0 || !e.target) {
        isLoading = 0;
      }
    };

    const isNestedVisible = function(elem, elemExpand) {
      let outerRect;
      let parent = elem;
      let visible = getCSS(document.body, 'visibility') === 'hidden' || getCSS(elem, 'visibility') !== 'hidden';

      eLtop -= elemExpand;
      eLbottom += elemExpand;
      eLleft -= elemExpand;
      eLright += elemExpand;

      while (visible && (parent = parent.offsetParent) && parent !== document.body && parent !== docElem) {
        visible = ((getCSS(parent, 'opacity') || 1) > 0);

        if (visible && getCSS(parent, 'overflow') !== 'visible') {
          outerRect = parent.getBoundingClientRect();
          visible = eLright > outerRect.left &&
            eLleft < outerRect.right &&
            eLbottom > outerRect.top - 1 &&
            eLtop < outerRect.bottom + 1
          ;
        }
      }

      return visible;
    };

    const _populateElements = function () {
      lazyloadElems = document.getElementsByClassName(lazySizesConfig.lazyClass);
      preloadElems = document.getElementsByClassName(lazySizesConfig.lazyClass + ' ' + lazySizesConfig.preloadClass);
    };

    const checkElements = function() {
      let eLlen, i, rect, autoLoadElem, loadedSomething, elemExpand, elemNegativeExpand, elemExpandVal, beforeExpandVal;
      _populateElements();

      if ((loadMode = lazySizesConfig.loadMode) && isLoading < 8 && (eLlen = lazyloadElems.length)) {
        i = 0;

        lowRuns++;

        if (preloadExpand === null) {
          if (!('expand' in lazySizesConfig)) {
            lazySizesConfig.expand = docElem.clientHeight > 600 ? docElem.clientWidth > 600 ? 550 : 410 : 359;
          }

          defaultExpand = lazySizesConfig.expand;
          preloadExpand = defaultExpand * lazySizesConfig.expFactor;
        }

        if (currentExpand < preloadExpand && isLoading < 1 && lowRuns > 3 && loadMode > 2) {
          currentExpand = preloadExpand;
          lowRuns = 0;
        } else if (loadMode > 1 && lowRuns > 2 && isLoading < 6) {
          currentExpand = defaultExpand;
        } else {
          currentExpand = shrinkExpand;
        }

        for (; i < eLlen; i++) {
          if (!lazyloadElems[i] || lazyloadElems[i]._lazyRace) { continue; }

          if (!supportScroll) { unveilElement(lazyloadElems[i]); continue; }

          if (!(elemExpandVal = lazyloadElems[i][_getAttribute]('data-expand')) || !(elemExpand = elemExpandVal * 1)) {
            elemExpand = currentExpand;
          }

          if (beforeExpandVal !== elemExpand) {
            eLvW = innerWidth + (elemExpand * hFac);
            elvH = innerHeight + elemExpand;
            elemNegativeExpand = elemExpand * -1;
            beforeExpandVal = elemExpand;
          }

          rect = lazyloadElems[i].getBoundingClientRect();

          if ((eLbottom = rect.bottom) >= elemNegativeExpand &&
            (eLtop = rect.top) <= elvH &&
            (eLright = rect.right) >= elemNegativeExpand * hFac &&
            (eLleft = rect.left) <= eLvW &&
            (eLbottom || eLright || eLleft || eLtop) &&
            (
              (isCompleted && isLoading < 3 && !elemExpandVal && (loadMode < 3 || lowRuns < 4)) ||
                isNestedVisible(lazyloadElems[i], elemExpand))) {
            unveilElement(lazyloadElems[i]);
            loadedSomething = true;
            if (isLoading > 9) { break; }
          } else if (!loadedSomething && isCompleted && !autoLoadElem &&
            isLoading < 4 && lowRuns < 4 && loadMode > 2 &&
            (preloadElems[0] || lazySizesConfig.preloadAfterLoad) &&
            (preloadElems[0] || (
              !elemExpandVal && (
                (eLbottom || eLright || eLleft || eLtop) ||
                lazyloadElems[i][_getAttribute](lazySizesConfig.sizesAttr) !== 'auto')
            )
            )) {
            autoLoadElem = preloadElems[0] || lazyloadElems[i];
          }
        }

        if (autoLoadElem && !loadedSomething) {
          unveilElement(autoLoadElem);
        }
      }
    };

    const throttledCheckElements = throttle(checkElements);

    const switchLoadingClass = function(e) {
      addClass(e.target, lazySizesConfig.loadedClass);
      removeClass(e.target, lazySizesConfig.loadingClass);
      addRemoveLoadEvents(e.target, rafSwitchLoadingClass);
    };
    const rafSwitchLoadingClass = function(e) {
      e = {target: e.target};
      rAF(function() {
        switchLoadingClass(e);
      });
    };

    const changeIframeSrc = function(elem, src) {
      try {
        elem.contentWindow.location.replace(src);
      } catch (e) {
        elem.src = src;
      }
    };

    const handleSources = function(source) {
      let customMedia, parent;

      const sourceSrcset = source[_getAttribute](lazySizesConfig.srcsetAttr);

      if ((customMedia = lazySizesConfig.customMedia[source[_getAttribute]('data-media') || source[_getAttribute]('media')])) {
        source.setAttribute('media', customMedia);
      }

      if (sourceSrcset) {
        source.setAttribute('srcset', sourceSrcset);
      }

      // https://bugzilla.mozilla.org/show_bug.cgi?id=1170572
      if (customMedia) {
        parent = source.parentNode;
        parent.insertBefore(source.cloneNode(), source);
        parent.removeChild(source);
      }
    };

    const rafBatch = (function() {
      let isRunning;
      const batch = [];
      const runBatch = function() {
        while (batch.length) {
          (batch.shift())();
        }
        isRunning = false;
      };
      const add = function(fn) {
        batch.push(fn);
        if (!isRunning) {
          isRunning = true;
          rAF(runBatch);
        }
      };

      return {
        add: add,
        run: runBatch
      };
    })();

    const unveilElement = function (elem) {
      let src, srcset, parent, isPicture, event, firesLoad, width;

      const isImg = regImg.test(elem.nodeName);

      // allow using sizes="auto", but don't use. it's invalid.
      // Use data-sizes="auto" or a valid value for sizes instead (i.e.: sizes="80vw")
      const sizes = isImg && (elem[_getAttribute](lazySizesConfig.sizesAttr) || elem[_getAttribute]('sizes'));
      const isAuto = sizes === 'auto';

      if ((isAuto || !isCompleted) &&
            isImg &&
            (elem.src || elem.srcset) &&
            !elem.complete &&
            !hasClass(elem, lazySizesConfig.errorClass)) {
        return;
      }

      if (isAuto) {
        width = elem.offsetWidth;
      }

      elem._lazyRace = true;
      isLoading++;

      if (lazySizesConfig.rC) {
        width = lazySizesConfig.rC(elem, width) || width;
      }

      rafBatch.add(function lazyUnveil() {
        if (!(event = triggerEvent(elem, 'lazybeforeunveil')).defaultPrevented) {
          if (sizes) {
            if (isAuto) {
              autoSizer.updateElem(elem, true, width);
              addClass(elem, lazySizesConfig.autosizesClass);
            } else {
              elem.setAttribute('sizes', sizes);
            }
          }

          srcset = elem[_getAttribute](lazySizesConfig.srcsetAttr);
          src = elem[_getAttribute](lazySizesConfig.srcAttr);

          if (isImg) {
            parent = elem.parentNode;
            isPicture = parent && regPicture.test(parent.nodeName || '');
          }

          firesLoad = event.detail.firesLoad || (('src' in elem) && (srcset || src || isPicture));

          event = {target: elem};

          if (firesLoad) {
            addRemoveLoadEvents(elem, resetPreloading, true);
            clearTimeout(resetPreloadingTimer);
            resetPreloadingTimer = setTimeout(resetPreloading, 2500);

            addClass(elem, lazySizesConfig.loadingClass);
            addRemoveLoadEvents(elem, rafSwitchLoadingClass, true);
          }

          if (isPicture) {
            forEach.call(parent.getElementsByTagName('source'), handleSources);
          }

          if (srcset) {
            elem.setAttribute('srcset', srcset);
          } else if (src && !isPicture) {
            if (regIframe.test(elem.nodeName)) {
              changeIframeSrc(elem, src);
            } else {
              elem.src = src;
            }
          }

          if (srcset || isPicture) {
            updatePolyfill(elem, {src: src});
          }
        }

        rAF(function() {
          if (elem._lazyRace) {
            delete elem._lazyRace;
          }
          removeClass(elem, lazySizesConfig.lazyClass);

          if (!firesLoad || elem.complete) {
            if (firesLoad) {
              resetPreloading(event);
            } else {
              isLoading--;
            }
            switchLoadingClass(event);
          }
        });
      });
    };

    const onload = function() {
      if (isCompleted) { return; }
      if (Date.now() - started < 999) {
        setTimeout(onload, 999);
        return;
      }
      let scrollTimer;
      const afterScroll = function() {
        lazySizesConfig.loadMode = 3;
        throttledCheckElements();
      };

      isCompleted = true;

      lazySizesConfig.loadMode = 3;

      if (document.hidden) {
        checkElements();
        rafBatch.run();
      } else {
        throttledCheckElements();
      }

      addEventListener('scroll', function() {
        if (lazySizesConfig.loadMode === 3) {
          lazySizesConfig.loadMode = 2;
        }
        clearTimeout(scrollTimer);
        scrollTimer = setTimeout(afterScroll, 99);
      }, true);
    };

    return {
      _: function() {
        started = Date.now();

        _populateElements();
        hFac = lazySizesConfig.hFac;

        addEventListener('scroll', throttledCheckElements, true);

        addEventListener('resize', throttledCheckElements, true);

        if (window.MutationObserver) {
          new MutationObserver(throttledCheckElements).observe(
            docElem, {childList: true, subtree: true, attributes: true});
        } else {
          docElem[_addEventListener]('DOMNodeInserted', throttledCheckElements, true);
          docElem[_addEventListener]('DOMAttrModified', throttledCheckElements, true);
          setInterval(throttledCheckElements, 999);
        }

        addEventListener('hashchange', throttledCheckElements, true);

        ['focus', 'mouseover', 'click', 'load', 'transitionend', 'animationend', 'webkitAnimationEnd'].forEach(
          function(name) {
            document[_addEventListener](name, throttledCheckElements, true);
          }
        );

        if ((/d$|^c/.test(document.readyState))) {
          onload();
        } else {
          addEventListener('load', onload);
          document[_addEventListener]('DOMContentLoaded', throttledCheckElements);
          setTimeout(onload, 20000);
        }

        throttledCheckElements(lazyloadElems.length > 0);
      },
      checkElems: throttledCheckElements,
      unveil: unveilElement
    };
  })();

  const autoSizer = (function() {
    let autosizesElems;

    const sizeElement = function (elem, dataAttr, width) {
      let sources, i, len, event;
      const parent = elem.parentNode;

      if (parent) {
        width = getWidth(elem, parent, width);
        event = triggerEvent(elem, 'lazybeforesizes', {width: width, dataAttr: !!dataAttr});

        if (!event.defaultPrevented) {
          width = event.detail.width;

          if (width && width !== elem._lazysizesWidth) {
            elem._lazysizesWidth = width;
            width += 'px';
            elem.setAttribute('sizes', width);

            if (regPicture.test(parent.nodeName || '')) {
              sources = parent.getElementsByTagName('source');
              for (i = 0, len = sources.length; i < len; i++) {
                sources[i].setAttribute('sizes', width);
              }
            }

            if (!event.detail.dataAttr) {
              updatePolyfill(elem, event.detail);
            }
          }
        }
      }
    };

    const updateElementsSizes = function() {
      let i;
      const len = autosizesElems.length;
      if (len) {
        i = 0;

        for (; i < len; i++) {
          sizeElement(autosizesElems[i]);
        }
      }
    };

    const throttledUpdateElementsSizes = throttle(updateElementsSizes);

    return {
      _: function() {
        autosizesElems = document.getElementsByClassName(lazySizesConfig.autosizesClass);
        addEventListener('resize', throttledUpdateElementsSizes);
      },
      checkElems: throttledUpdateElementsSizes,
      updateElem: sizeElement
    };
  })();

  const init = function() {
    if (!init.i) {
      init.i = true;
      autoSizer._();
      loader._();
    }
  };

  (function() {
    let prop;

    const lazySizesDefaults = {
      lazyClass: 'lazyload',
      loadedClass: 'lazyloaded',
      loadingClass: 'lazyloading',
      preloadClass: 'lazypreload',
      errorClass: 'lazyerror',
      // strictClass: 'lazystrict',
      autosizesClass: 'lazyautosizes',
      srcAttr: 'data-src',
      srcsetAttr: 'data-srcset',
      sizesAttr: 'data-sizes',
      minSize: 40,
      customMedia: {},
      init: true,
      expFactor: 1.7,
      hFac: 0.8,
      loadMode: 2
    };

    lazySizesConfig = window.lazySizesConfig || window.lazysizesConfig || {};

    for (prop in lazySizesDefaults) {
      if (!(prop in lazySizesConfig)) {
        lazySizesConfig[prop] = lazySizesDefaults[prop];
      }
    }

    window.lazySizesConfig = lazySizesConfig;

    setTimeout(function() {
      if (lazySizesConfig.init) {
        init();
      }
    });
  })();

  return {
    cfg: lazySizesConfig,
    autoSizer: autoSizer,
    loader: loader,
    init: init,
    uP: updatePolyfill,
    aC: addClass,
    rC: removeClass,
    hC: hasClass,
    fire: triggerEvent,
    gW: getWidth
  };
}
));
