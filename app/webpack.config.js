const path = require('path');

module.exports = {
  entry: './src/js/index.js', // Cambia './src/index.js' por la ruta de tu archivo de entrada principal.
  output: {
    path: path.resolve(__dirname, 'static'), // Cambia 'static' por la carpeta de salida que prefieras.
    filename: 'bundle.js',
  },
  module: {
    rules: [
      {
        test: /\.scss$/,
        use: [
          'style-loader',
          'css-loader',
          'sass-loader',
        ],
      },
    ],
  },
  devServer: {
    static: path.resolve(__dirname, 'templates'), // Cambia 'static' por la carpeta de salida que prefieras.
    port: 8080, // Puedes cambiar el número de puerto si lo deseas.
    watchFiles: ['src/**/*.scss'], // Agrega esta línea para observar los archivos Sass
    proxy: {
      '/': {
        target: 'http://localhost:5000', // Reemplaza esto con la URL de tu servidor Flask
        secure: false,
      },
    },
    hot: true, // Agrega esta línea para habilitar la recarga automática
  },
};
