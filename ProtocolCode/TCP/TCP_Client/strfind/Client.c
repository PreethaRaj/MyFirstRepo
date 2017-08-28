#include <stdio.h>
#include <WinSock2.h>
#include <WS2tcpip.h>
#include <Windows.h>

#pragma comment(lib,"ws2_32")


int main()
{
	WSADATA wsaData;
	WSAStartup(MAKEWORD(2, 2), &wsaData);
	
	SOCKET m_socket;
	m_socket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
	
	// Connect to a server.
	struct sockaddr_in clientService;

	clientService.sin_family = AF_INET;	
	clientService.sin_addr.s_addr = inet_addr("127.0.0.1");
	clientService.sin_port = htons(33333);

	connect(m_socket, (SOCKADDR*)&clientService, sizeof(clientService));

	// Send and receive data.
	int bytesSent;
	int bytesRecv = SOCKET_ERROR;	
	char sendbuf[200] = "**********TEST DATA FROM CLIENT**********";
	char recvbuf[200] = "";

	// Received from server...
	while (bytesRecv == SOCKET_ERROR)
	{
		bytesRecv = recv(m_socket, recvbuf, 200, 0);
		if (bytesRecv == 0 || bytesRecv == WSAECONNRESET)
		{
			printf("Client: Connection Closed.\n");
			break;
		}

		if (bytesRecv < 0)
			return 0;
		else
		{
			printf("Client: recv() is OK.\n");
			printf("Client: Received data is: \"%s\"\n", recvbuf);
			printf("Client: Bytes received is: %ld.\n", bytesRecv);
		}
	}

	// Sends data to server...
	bytesSent = send(m_socket, sendbuf, strlen(sendbuf), 0);
	
	printf("Client: send() is OK - Bytes sent: %ld\n", bytesSent);
	//printf("Client: The test string sent: \"%s\"\n", sendbuf);
	

	WSACleanup();
	//return 0;
	getchar();
}
