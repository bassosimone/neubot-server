#!/bin/sh -e
# Clone specific tags from github and update local copy

get() {
  git clone https://github.com/$1 tmp/$1
  (cd tmp/$1 && git checkout $2)
  (cd tmp/$1 && git archive --prefix=$3/ HEAD) | \
    (cd neubot/ && tar -xf-)
}

rm -rf tmp/*
get DavideAllavena/neubot-mod-speedtest 1a55737 mod_speedtest
get DavideAllavena/neubot-mod-bittorrent cda686c mod_bittorrent
get DavideAllavena/neubot-mod-dash 05328c0 mod_dash
get DavideAllavena/neubot-lib-net beaafd7 lib_net
get DavideAllavena/neubot-lib-http c4ef94f lib_http
get DavideAllavena/neubot-mod-raw-test 76931b3 mod_raw_test
get DavideAllavena/neubot-utils 3290ae1 utils
get DavideAllavena/neubot-negotiate 458fa8f negotiate
