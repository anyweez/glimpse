'use strict'

let gulp = require('gulp');
let sass = require('gulp-sass');
let pug = require('gulp-pug');
let browserify = require('gulp-browserify');
let typescript = require('gulp-typescript');
let babel = require('gulp-babel');
let merge = require('merge-stream');

let ts = typescript.createProject('tsconfig.json');

gulp.task('default', ['html', 'css', 'js']);

gulp.task('html', function () {
    return gulp.src('./*.jade')
        .pipe(pug())
        .pipe(gulp.dest('./public'));
});

gulp.task('css', function () {
    return gulp.src('./scss/main.scss')
        .pipe(sass())
        .pipe(gulp.dest('./public/css'));
});

/**
 * Based on Typescript guidance in:
 * https://www.typescriptlang.org/docs/handbook/gulp.html
 */
gulp.task('typescript', function () {
    return ts.src()
        .pipe(typescript(ts))
        // I'm transpiling because Browserify can't handle ES6.
        .js.pipe(babel({
            presets: ['es2015'],
        }))
        .pipe(gulp.dest('./_out'));
});

gulp.task('js', ['typescript'], function () {
    return gulp.src('./_out/app.js')
        .pipe(browserify({
            sourceType: 'module',
        }))
        .pipe(gulp.dest('./public/js'));
});

/**
 * Run tests with Mocha. Glimpse modules use ES6 module syntax so there's a 
 * build step involved here as well.
 */
gulp.task('test', ['js'], function () {
    return gulp.src('test/*.js')
        .pipe(babel({
            presets: ['es2015'],
        }))
        .pipe(gulp.dest('tests/'))
        // .pipe(mocha());
});

gulp.task('watch', ['default'], function () {
    gulp.watch('./*.jade', ['html']);
    gulp.watch('./scss/*.scss', ['css']);
    gulp.watch('./src/*.ts', ['js']);
    gulp.watch('./test/*.js', ['test']);
});