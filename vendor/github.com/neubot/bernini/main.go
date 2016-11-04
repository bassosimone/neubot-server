// Part of Neubot <https://neubot.nexacenter.org/>.
// Neubot is free software. See AUTHORS and LICENSE for more
// information on the copying conditions.

package bernini

import (
	"log"
	"os"
)

func GetoptVersionAndHelp(version string, usage string) {
	if len(os.Args) == 2 && os.Args[1] == "--version" {
		log.Printf("%s", version)
		os.Exit(0)
	}
	if len(os.Args) == 2 && os.Args[1] == "--help" {
		log.Printf("%s", usage)
		os.Exit(0)
	}
}
