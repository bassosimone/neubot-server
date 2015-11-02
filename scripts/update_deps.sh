#!/bin/sh -e
# Clone specific tags from github and update local copy

get() {
  git clone https://github.com/$1 tmp/$1
  (cd tmp/$1 && git checkout $2)
  (cd tmp/$1 && git archive --prefix=$3/ HEAD) | \
    (cd neubot/ && tar -xf-)
}

rm -rf tmp/*
get DavideAllavena/neubot-mod-speedtest 339e1e8 mod_speedtest
get DavideAllavena/neubot-mod-bittorrent  7d837de mod_bittorrent
get DavideAllavena/neubot-mod-dash d556977 mod_dash
get DavideAllavena/neubot-lib-net bfb39c7 lib_net
get DavideAllavena/neubot-lib-http 7f385dd lib_http
get DavideAllavena/neubot-mod-raw-test 9a6b74e mod_raw_test
get DavideAllavena/neubot-utils 78f4606 utils
get DavideAllavena/neubot-negotiate b0211ac negotiate
