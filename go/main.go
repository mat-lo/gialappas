// --- Final Go Proxy for ESP32 Door Relay ---

package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"time"
)

// --- Configuration ---
// Set this to the static IP address of your ESP32
const esp32BaseURL = "http://192.168.1.35"
// --- End of Configuration ---

const (
	esp32OpenURL   = esp32BaseURL + "/open"
	esp32StatusURL = esp32BaseURL + "/status"
	proxyPort      = "3000"
)

// apiResponse defines the structure of our JSON response to the frontend.
type apiResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

// writeJSONResponse is a helper to send a standardized JSON response to the client.
func writeJSONResponse(w http.ResponseWriter, httpStatusCode int, status, message string) {
	w.Header().Set("Content-Type", "application/json")
	// Allow requests from any origin (useful for web development)
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.WriteHeader(httpStatusCode)
	json.NewEncoder(w).Encode(apiResponse{
		Status:  status,
		Message: message,
	})
}

// writeForwardedJSONResponse passes a raw JSON body from the ESP32 to the client.
func writeForwardedJSONResponse(w http.ResponseWriter, httpStatusCode int, body []byte) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.WriteHeader(httpStatusCode)
	w.Write(body)
}

// handleOpenRequest attempts to trigger the ESP32 relay.
func handleOpenRequest(w http.ResponseWriter, r *http.Request) {
	client := http.Client{
		Timeout: 5 * time.Second,
	}

	resp, err := client.Get(esp32OpenURL)
	if err != nil {
		log.Printf("Error contacting ESP32 for /open: %v", err)
		if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
			writeJSONResponse(w, http.StatusGatewayTimeout, "ERROR_ESP_TIMEOUT", "The ESP32 is not responding. It might be offline or disconnected from Wi-Fi.")
			return
		}
		writeJSONResponse(w, http.StatusBadGateway, "ERROR_ESP_CONNECTION", "Failed to connect to the ESP32. Check if it's powered on and the MicroPython script is running.")
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		writeJSONResponse(w, http.StatusOK, "SUCCESS", "Door activated! The relay was triggered successfully.")
	} else {
		log.Printf("ESP32 returned a non-200 status for /open: %d", resp.StatusCode)
		writeJSONResponse(w, http.StatusBadGateway, "ERROR_ESP_BAD_RESPONSE", fmt.Sprintf("The ESP32 is online but returned an error (Code: %d).", resp.StatusCode))
	}
}

// handleStatusRequest gets a diagnostic report from the ESP32.
func handleStatusRequest(w http.ResponseWriter, r *http.Request) {
	client := http.Client{
		Timeout: 5 * time.Second,
	}

	resp, err := client.Get(esp32StatusURL)
	if err != nil {
		log.Printf("Error contacting ESP32 for /status: %v", err)
		if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
			writeJSONResponse(w, http.StatusGatewayTimeout, "ERROR_ESP_TIMEOUT", "The ESP32 is not responding. It might be offline or disconnected from Wi-Fi.")
			return
		}
		writeJSONResponse(w, http.StatusBadGateway, "ERROR_ESP_CONNECTION", "Failed to connect to the ESP32. Check if it's powered on and the MicroPython script is running.")
		return
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Printf("Failed to read response body from ESP32: %v", err)
		writeJSONResponse(w, http.StatusInternalServerError, "ERROR_PROXY_INTERNAL", "Failed to read response from ESP32.")
		return
	}

	if resp.StatusCode == http.StatusOK {
		// The ESP32 returned its status JSON, so we forward it directly.
		writeForwardedJSONResponse(w, http.StatusOK, body)
	} else {
		log.Printf("ESP32 returned a non-200 status for /status: %d", resp.StatusCode)
		writeJSONResponse(w, http.StatusBadGateway, "ERROR_ESP_BAD_RESPONSE", fmt.Sprintf("The ESP32 is online but returned an error (Code: %d).", resp.StatusCode))
	}
}

func main() {
	// API endpoints
	http.HandleFunc("/api/open", handleOpenRequest)
	http.HandleFunc("/api/status", handleStatusRequest)

	// A simple root handler to confirm the server is running
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprint(w, "all good mate.")
	})

	fmt.Printf("Server starting on port %s...\n", proxyPort)
	fmt.Printf("Proxying requests to ESP32 at %s\n", esp32BaseURL)
	log.Fatal(http.ListenAndServe(":"+proxyPort, nil))
}