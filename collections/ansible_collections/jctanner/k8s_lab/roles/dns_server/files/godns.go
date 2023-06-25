package main

import (
	"fmt"
	"net"
	"os"
	"strings"
)

const (
	HostsFile   = "/etc/hosts"
	DNSPort     = 53
	DNSProtocol = "udp"
)

var hosts map[string]string

func loadHosts() {
	hosts = make(map[string]string)
	file, err := os.Open(HostsFile)
	if err != nil {
		fmt.Println("Error opening hosts file:", err)
		return
	}
	defer file.Close()

	buffer := make([]byte, 1024)
	for {
		n, err := file.Read(buffer)
		if n == 0 || err != nil {
			break
		}

		lines := strings.Split(string(buffer[:n]), "\n")
		for _, line := range lines {
			line = strings.TrimSpace(line)
			if line != "" && !strings.HasPrefix(line, "#") {
				parts := strings.Fields(line)
				if len(parts) > 1 {
					ip := parts[0]
                    if !strings.HasPrefix(ip, "127.") {
                        for _, host := range parts[1:] {
                            msg := fmt.Sprintf("%s = %s" , host, ip)
                            fmt.Println(msg)
                            hosts[host] = ip
                        }
                    }
				}
			}
		}
	}
}

func extractHostname(data []byte) string {
	// Skip the first 12 bytes (DNS header)
	data = data[12:]

	var hostname string
	for i := 0; i < len(data); i++ {
		labelLength := int(data[i])
		if labelLength == 0 {
			break
		}
		if i != 0 {
			hostname += "."
		}
		hostname += string(data[i+1 : i+1+labelLength])
		i += labelLength
	}
	return hostname
}

func buildNameErrorResponse(data []byte) []byte {
	response := make([]byte, len(data))

	copy(response, data) // Copy the DNS request header to the response

	// Set the response flags to indicate a "Name Error"
	response[2] |= 0x81 // Set the response flag (bit 15) and the error code (bit 0-3)

	// Set the answer count to 0
	response[6] = 0x00
	response[7] = 0x00

	return response
}

func buildDNSResponse(data []byte, ip string) []byte {
	response := make([]byte, len(data)+16) // Increase response size by 16 bytes for the answer

	copy(response, data) // Copy the DNS request header to the response

	// Set the response flags
	response[2] |= 0x80 // Set the response flag (bit 15)
	response[3] |= 0x80 // Set the recursion available flag (bit 7)

	// Set the answer count to 1
	response[6] = 0x00
	response[7] = 0x01

	// Set the answer section
	answerSection := response[len(data):]
	answerSection[0] = 0xC0 // Compression pointer to the question section
	answerSection[1] = 0x0C
	answerSection[2] = 0x00 // Type: A
	answerSection[3] = 0x01
	answerSection[4] = 0x00 // Class: IN
	answerSection[5] = 0x01
	answerSection[6] = 0x00 // TTL: 0 seconds
	answerSection[7] = 0x00
	answerSection[8] = 0x00
	answerSection[9] = 0x00
	answerSection[10] = 0x00 // Data length
	answerSection[11] = 0x04 // Data length
	copy(answerSection[12:], net.ParseIP(ip).To4()) // Copy the IP address to the answer section

	return response
}

func handleDNSRequest(conn *net.UDPConn, addr *net.UDPAddr, data []byte) {
	// Extract the hostname from the DNS request
	hostname := extractHostname(data)

	var response []byte
	if ip, ok := hosts[hostname]; ok {
		// Build the DNS response
		response = buildDNSResponse(data, ip)

		// Print human-readable response
		fmt.Printf("DNS response for %s:\n", hostname)
		fmt.Printf("IP: %s\n", ip)
	} else {
		// Build a "Name Error" DNS response
		response = buildNameErrorResponse(data)

		// Print human-readable response
		fmt.Printf("DNS response for %s:\n", hostname)
		fmt.Println("Name Error")
	}

	conn.WriteToUDP(response, addr)
}

func main() {
	loadHosts()

    fmt.Println("---------------------------------------------")

	addr := net.UDPAddr{
		Port: DNSPort,
		IP:   net.ParseIP("0.0.0.0"),
	}

	conn, err := net.ListenUDP(DNSProtocol, &addr)
	if err != nil {
		fmt.Println("Error creating UDP socket:", err)
		return
	}
	defer conn.Close()

	fmt.Println("DNS server is running")

	buffer := make([]byte, 1024)
	for {
		n, addr, err := conn.ReadFromUDP(buffer)
		if err != nil {
			fmt.Println("Error reading UDP packet:", err)
			continue
		}

		go handleDNSRequest(conn, addr, buffer[:n])
	}
}

