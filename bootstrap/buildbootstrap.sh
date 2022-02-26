#!/bin/sh
mkdir -p build
if ! sassc "$1" "./build/$1" >&2; then
    exit 1
fi
postcss "./build/$1" --no-map --use autoprefixer cssnano -o "$2" >&2

# NOTE: you will need postcss-cli, cssnano and autoprefixer from npm (install globally), and sassc.
# To run:
# cd tgrsite/bootstrap
# ./buildbootstrap.sh source.scss target.css
# (source is probably a file in this directory, and target is likely in static_resources)