'use strict'

let gulp = require('gulp');
let sass = require('gulp-sass');
let pug = require('gulp-pug');
let browserify = require('gulp-browserify');
let merge = require('merge-stream');

gulp.task('default', ['html', 'css', 'js']);

gulp.task('html', function () {
    return gulp.src('./*.jade')
        .pipe(pug())
        .pipe(gulp.dest('./public'));
});

gulp.task('css', function () {
    let main = gulp.src('./scss/main.scss')
        .pipe(sass())
        .pipe(gulp.dest('./public/css'));

    let simulate = gulp.src('./scss/simulate.scss')
        .pipe(sass())
        .pipe(gulp.dest('./public/css'));

    return gulp.src('./scss/main.scss')
        .pipe(sass())
        .pipe(gulp.dest('./public/css'));
});

gulp.task('js', function () {
    let app = gulp.src('./js/app.js')
        .pipe(browserify())
        .pipe(gulp.dest('./public/js'));

    let simulation = gulp.src('./js/simulate.js')
        .pipe(browserify())
        .pipe(gulp.dest('./public/js'))

    return merge(app, simulation);
});

gulp.task('watch', function () {
    gulp.watch('./*.jade', ['html']);
    gulp.watch('./scss/*.scss', ['css']);
    gulp.watch('./js/*.js', ['js']);
});