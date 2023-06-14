/*
* Gulpfile
* @version: 1.0.0 (Fri, 08 May 2020)
* @author: HtmlStream
* @license: Htmlstream (https://htmlstream.com/licenses)
* Copyright 2020 Htmlstream
*/

require('./gulpfiles/watch')
require('./gulpfiles/dist')
require('./gulpfiles/build')


// var replace = require('gulp-token-replace');

// gulp.task('token-replace', function () {
//     var config = require('./sjbook-config.json');
//     return gulp.src(['src/*.js', 'src/*.html'])
//         .pipe(replace({ global: config }))
//         .pipe(gulp.dest('dist/'));
// });