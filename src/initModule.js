/**
 * assign a listener to Module.listen
 * @type {function(string):void}
 */
if (!Module['listen']) Module['listen'] = data => console.log(data);

/**
 * assign an error handler to Module.onError
 * @type {function(string):void}
 */
if (!Module['onError']) Module['onError'] = data => console.error(data);

/** @private, @param {number=} index */
Module['getRecommendedNnue'] = (index = 0) => UTF8ToString(_getRecommendedNnue(index));

/** @private, @param {Uint8Array} buf, @param {number=} index */
Module['setNnueBuffer'] = function (buf, index = 0) {
  if (!buf) throw new Error('buf is null');
  if (buf.byteLength <= 0) throw new Error(`${buf.byteLength} bytes?`);
  const heapBuf = _malloc(buf.byteLength); // deallocated in src/wasm/glue.cpp
  if (!heapBuf) throw new Error(`could not allocate ${buf.byteLength} bytes`);
  growMemViews(); // refresh HEAPU8 after allocation
  Module['HEAPU8'].set(buf, heapBuf);
  _setNnueBuffer(heapBuf, buf.byteLength, index);
};

/** @private, @param {string} command */
Module['uci'] = function (command) {
  const sz = lengthBytesUTF8(command) + 1;
  const utf8 = _malloc(sz); // deallocated in src/wasm/glue.cpp
  if (!utf8) throw new Error(`Could not allocate ${sz} bytes`);
  stringToUTF8(command, utf8, sz);
  _uci(utf8);
};

/** @private, @param {string} data */
Module['print'] = data => Module['listen']?.(data);

/** @private, @param {string} data */
Module['printErr'] = data => Module['onError']?.(data);
