package main

/*
 * main.go - Stripped down version of botticelli from the `vendor` folder
 * to be build using the `./scripts/get-botticelli` script.
 *
 * Unlike the real botticelli, here we just run the NDT server.
 *
 * As botticelli becomes more and more capable this will eventually
 * become the main binary of neubot-server.
 */

import (
	"github.com/neubot/bernini"
	"github.com/neubot/botticelli/common"
	"github.com/neubot/botticelli/nettests/ndt"
	"log"
)

const usage = `usage: botticelli [--help]
       botticelli [--version]`

func main() {
	bernini.InitLogger()
	bernini.InitRng()

	bernini.GetoptVersionAndHelp(common.Version, usage)
	bernini.UseSyslogOrDie("botticelli")

	log.Printf("botticelli server %s starting up", common.Version)

	ndt.Start(":3007")
}
