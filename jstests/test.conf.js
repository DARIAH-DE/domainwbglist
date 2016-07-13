module.exports = function (config) {
  config.set({
    basePath: '..',
    frameworks: ['qunit'],
    plugins: ['karma-qunit','karma-junit-reporter','karma-phantomjs-launcher'],
    files: [
      'static/js/jquery.min.1.11.3.js',
      'static/js/bootstrap.min.3.3.6.js',
      'jstests/lib/jquery.mockjax.min.2.2.0.js',
      'static/js/mystuff.js',
      'jstests/**/*.spec.js'
    ],
    reporters: ['progress','junit'],
    port: 9876,
    colors: true,
    logLevel: config.LOG_INFO,
    autoWatch: false,
    browsers: ['PhantomJS'],
    captureTimeout: 10000,
    singleRun: true,
    junitReporter: {
      outputFile: 'test-results.xml'
    },

  })
}
