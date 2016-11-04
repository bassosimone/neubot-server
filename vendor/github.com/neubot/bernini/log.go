// Part of Neubot <https://neubot.nexacenter.org/>.
// Neubot is free software. See AUTHORS and LICENSE for more
// information on the copying conditions.

package bernini

import (
	"log"
	"log/syslog"
	"os"
)

func InitLogger() {
	log.SetFlags(0)
}

// See http://technosophos.com/2013/09/14/using-gos-built-logger-log-syslog.html
func UseSyslog(progname string) error {
	log.Print("redirecting logs to the system logger")
	logwriter, err := syslog.New(syslog.LOG_NOTICE, progname)
	if err != nil {
		return err
	}
	log.SetOutput(logwriter)
	return nil
}

func UseSyslogOrDie(progname string) {
	if err := UseSyslog(progname); err != nil {
		log.Printf("cannot use syslog: %s", err)
		os.Exit(1)
	}
}
