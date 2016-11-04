# Bernini: common go language code for Neubot

This repository contains common pieces of [go language](https://golang.org/)
code used by the Neubot project.

## Usage

```Go

import (
    "github.com/neubot/bernini"
    "log"
    "time"
)

var count int
var data []byte
var err error

// Initialize the random number generator
bernini.InitRng()

// Get 128 random bytes composed of uppercase or lowercase letters
data = bernini.RandByteMaskingImproved(128)

// Get 128 random, printable ascii characters
data = bernini.RandAsciiRemainder(128)

// Set the timeout for I/O operations performed by bernini
bernini.IoTimeout = 42 * time.Second

/*
 * The following I/O operations will timeout (returning an error) after
 * `bernini.IoTimeout` time units have passed without I/O completing.
 *
 * The write functions should write all data in the passed byte, []byte, or
 * string unless an error (including timeout) occurs.
 */

count, err = bernini.IoReadFull(
        conn,    // net.Conn
        reader,  // io.Reader
        dest_buf // []byte
)
if err != nil {
    log.Panic("IoReadFull failed")
}

err = bernini.IoWriteByte(
        conn,   // net.Conn
        writer, // *bufio.Writer
        obuf    // byte
)
if err != nil {
    log.Panic("IoWriteByte failed")
}

count, err = bernini.IoWrite(
        conn,   // net.Conn
        writer, // *bufio.Writer
        obufs   // []byte
)
if err != nil {
    log.Panic("IoWrite failed")
}

err = bernini.IoFlush(
        conn,   // net.Conn
        writer, // *bufio.Writer
)
if err != nil {
    log.Panic("IoFlush failed")
}

count, err = bernini.IoWriteString(
        conn,   // net.Conn
        writer, // *bufio.Writer
        obufs   // string
)
if err != nil {
    log.Panic("IoWriteString failed")
}

// Initialize the logger flags by cleaning up the format
bernini.InitLogger()

// Modify the logger to send messages to syslog
err = bernini.UseSyslog("progname")
if err != nil {
        log.Panic("UseSyslog failed")
}

// Same as above but call `log.Fatal()` in case of failure
bernini.UseSyslogOrDie("progname")

/*
 * The `GetoptVersionAndHelp` function will handle the `--help` and
 * `--version` command line flags for you.
 */

const usage = `usage: progname [--help]
       progname [--version]`

bernini.GetoptVersionAndHelp(
        "0.1.2"  // Version number as string
        usage    // Usage string
)
```

Make sure you set your `GOPATH` environment variable and then `go get`
should automatically get and build the Bernini library for you.
