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
get DavideAllavena/neubot-mod-raw-test 9a6b74e mod_raw_test
get DavideAllavena/neubot-negotiate b0211ac negotiate
rm -rf tmp


# XXX Quick fix just to import the needed dir
git clone https://github.com/bassosimone/neubot-runtime tmp/neubot-runtime 
(cd tmp/neubot-runtime && git checkout v1.0.0-alpha.1)
cp -R tmp/neubot-runtime/neubot_runtime/* neubot/runtime/
rm -rf tmp


