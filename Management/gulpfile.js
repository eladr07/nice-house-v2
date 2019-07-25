/// <binding AfterBuild='less, less-he' />
///
// include plug-ins
var gulp = require('gulp');
var concat = require('gulp-concat');
var del = require('del');
var minifyCSS = require('gulp-minify-css');
var sourcemaps = require('gulp-sourcemaps');
var less = require('gulp-less');

var root = 'node_modules';

var config = {
    //JavaScript files that will be combined into a jquery bundle
    jquerysrc: [
        root + '/jquery/dist/jquery.min.js',
    ],
    jquerybundle: 'Scripts/dist/jquery-bundle.min.js',

    // jQuery UI
    jqueryuisrc: root + '/jquery-ui-dist/jquery-ui.min.js',

    // Fancybox
    fancyboxSrc: root + '/fancybox/dist/js/jquery.fancybox.pack.js',
    fancyboxCss: root + '/fancybox/dist/css/jquery.fancybox.css',
    fancyboxImages: root + '/fancybox/dist/img/*',

    // DataTable
    dataTableSrc: [
        root + '/datatables.net/js/jquery.dataTables.min.js',
        root + '/datatables.net-buttons/js/dataTables.buttons.min.js',
        root + '/datatables.net-bs/js/dataTables.bootstrap.min.js',
    ],

    dataTableCss: root + '/datatables.net-bs/css/dataTables.bootstrap.min.css',

    //JavaScript files that will be combined into a Bootstrap bundle
    bootstrapsrc: root + '/bootstrap/dist/js/bootstrap.min.js',
    bootstrapbundle: 'Scripts/dist/bootstrap-bundle.min.js',

    // font-awesome
    fontAwesomeCss: root + '/font-awesome/css/font-awesome.css',
    fontAwesomeFonts: root + '/font-awesome/fonts/*',
        
    // bootstrap-datepicker
    bootstrapDatepickerSrc: [
        root + '/bootstrap-datepicker/dist/js/bootstrap-datepicker.min.js',
        root + '/bootstrap-datepicker/dist/locales/bootstrap-datepicker.he.min.js'
    ],

    bootstrap_css: root + "/bootswatch/flatly/bootstrap.css",
    bootstrap_less: root + "/bootstrap/less/bootstrap.less",

    //Bootstrap CSS and Fonts
    bootstrap_datepicker: root + '/bootstrap-datepicker/dist/css/bootstrap-datepicker.css',

    // bootstrap-rtl
    bootstrapRTL: root + '/bootstrap-rtl/dist/css/bootstrap-rtl.css',

    fontsout: 'static/fonts',
    cssout: 'static/css',
    imgout: 'static/images',

    scriptsOut: 'static/js'
}

// Synchronously delete the output script file(s)
gulp.task('clean-vendor-scripts', function (cb) {
    del(config.scriptsOut, cb);
});

//Create a jquery bundled file
gulp.task('jquery-bundle', function () {
    return gulp.src(config.jquerysrc)
     .pipe(concat('jquery-bundle.min.js'))
     .pipe(gulp.dest(config.scriptsOut));
});

//Copy the jquery-ui file
gulp.task('jquery-ui', function () {
    return gulp.src(config.jqueryuisrc)
        .pipe(gulp.dest(config.scriptsOut));
});

gulp.task('fancybox', function () {
    return gulp.src(config.fancyboxSrc)
        .pipe(gulp.dest(config.scriptsOut));
});

gulp.task('datatables-bundle', function () {
    return gulp.src(config.dataTableSrc)
        .pipe(concat('datatables-bundle.js'))
        .pipe(gulp.dest(config.scriptsOut));
});

//Create a bootstrap bundled file
gulp.task('bootstrap-bundle', function () {
    return gulp.src(config.bootstrapsrc)
     .pipe(sourcemaps.init())
     .pipe(concat('bootstrap-bundle.min.js'))
     .pipe(sourcemaps.write('maps'))
     .pipe(gulp.dest(config.scriptsOut));
});

gulp.task('bootstrap-datepicker', function () {
    return gulp.src(config.bootstrapDatepickerSrc)
        .pipe(concat('bootstrap-datepicker.js'))
        .pipe(gulp.dest(config.scriptsOut));
});

// Combine and the vendor files from bower into bundles (output to the Scripts folder)
gulp.task('vendor-scripts', gulp.series('jquery-bundle', 'jquery-ui', 'fancybox', 'datatables-bundle', 'bootstrap-bundle', 'bootstrap-datepicker'));

// Synchronously delete the output style files (css / fonts)
gulp.task('clean-styles', function (cb) {
    del([
        config.fontsout,
        config.cssout,
        config.imgout
    ], cb);
});

gulp.task('fancybox-css', function () {
    return gulp.src(config.fancyboxCss)
        .pipe(gulp.dest(config.cssout));
});

gulp.task('fancybox-images', function () {
    return gulp.src(config.fancyboxImages)
        .pipe(gulp.dest(config.imgout));
});

gulp.task('datatables-css', function () {
    return gulp.src(config.dataTableCss)
        .pipe(gulp.dest(config.cssout));
});

gulp.task('bootstrap-css', function () {
    return gulp.src(config.bootstrap_css)
        .pipe(concat('bootstrap.css'))
        .pipe(gulp.dest(config.cssout))
        .pipe(minifyCSS())
        .pipe(concat('bootstrap.min.css'))
        .pipe(gulp.dest(config.cssout));
});

gulp.task('bootstrap-less', function () {
    return gulp.src(config.bootstrap_less)
        .pipe(less())
        .pipe(concat('bootstrap.css'))
        .pipe(gulp.dest(config.cssout))
        .pipe(minifyCSS())
        .pipe(concat('bootstrap.min.css'))
        .pipe(gulp.dest(config.cssout));
});

gulp.task('bootstrap-datepicker-css', function () {
    return gulp.src(config.bootstrap_datepicker)
        .pipe(gulp.dest(config.cssout));
});

gulp.task('bootstrap-rtl-css', function () {
    return gulp.src(config.bootstrapRTL)
        .pipe(gulp.dest(config.cssout));
});

// copy font-awesome css
gulp.task('font-awesome-css', function () {
    return gulp.src(config.fontAwesomeCss)
        .pipe(gulp.dest(config.cssout));
})

// copy font-awesome fonts
gulp.task('font-awesome-fonts', function () {
    return gulp.src(config.fontAwesomeFonts)
        .pipe(gulp.dest(config.fontsout));
});

// Combine and minify css files and output fonts
gulp.task('styles', gulp.series('fancybox-css', 'fancybox-images', 'datatables-css', 'bootstrap-less', 'bootstrap-rtl-css', 'bootstrap-datepicker-css', 'font-awesome-css', 'font-awesome-fonts'));

//Set a default tasks
gulp.task('default', gulp.series('vendor-scripts', 'styles'));