const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  entry: './lib/js/index.js',
  output: {
    filename: 'main.js',
    path: path.resolve(__dirname, 'src/example_web/static'),
  },
  plugins: [new HtmlWebpackPlugin()],
};
