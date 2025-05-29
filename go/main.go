package main

import (
	"fmt"
	"log"
	"net/http"
	"net/http/httputil"
)

const targetURL = "http://192.168.1.44:3000/open"

func main() {
    http.HandleFunc("/open", func(w http.ResponseWriter, r *http.Request) {
        resp, err := http.Get(targetURL)
        if err != nil {
            http.Error(w, "Failed to reach target", http.StatusBadGateway)
            return
        }
        defer resp.Body.Close()

        dump, _ := httputil.DumpResponse(resp, true)
        w.Write(dump)
    })

    fmt.Println("Server running on :8000")
    log.Fatal(http.ListenAndServe(":8000", nil))
}
