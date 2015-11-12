#!/bin/sh -e
# Clone specific tags from github and update local copy

get() {
  (cd neubot/ && rm -rf $3)
  git clone https://github.com/$1 tmp/$1
  (cd tmp/$1 && git checkout $2)
  (cd tmp/$1 && git archive --prefix=$3/ HEAD$4) | \
    (cd neubot/ && tar -xf-)
}

rm -rf tmp
get DavideAllavena/neubot-mod-speedtest master mod_speedtest
get DavideAllavena/neubot-mod-bittorrent  master mod_bittorrent
get DavideAllavena/neubot-mod-dash master mod_dash
get DavideAllavena/neubot-mod-raw-test master mod_raw_test
get DavideAllavena/neubot-negotiate master negotiate
get bassosimone/neubot-runtime master runtime ':neubot_runtime/'
rm -rf tmp
