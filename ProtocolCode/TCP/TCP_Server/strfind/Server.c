#include <stdio.h>
#include <WinSock2.h>
#include <WS2tcpip.h>
#include <Windows.h>

#pragma comment(lib,"ws2_32")

int main()
{
	WORD wVersionRequested;
	WSADATA wsaData;
	WSAStartup(MAKEWORD(2, 2), &wsaData);
	
	SOCKET m_socket;

    m_socket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

	struct sockaddr_in service;

	service.sin_family = AF_INET;	
	service.sin_addr.s_addr = inet_addr("127.0.0.1");	
	service.sin_port = htons(33333);

	bind(m_socket, (SOCKADDR*)&service, sizeof(service));	

	listen(m_socket, 10);
	// socket for accepting client connections.
	SOCKET AcceptSocket;

	printf("Server: Waiting for a client to connect...\n");
	printf("***plz run client program...***\n");
	
	while (1)
	{
		AcceptSocket = SOCKET_ERROR;
		while (AcceptSocket == SOCKET_ERROR)
		{
			AcceptSocket = accept(m_socket, NULL, NULL);
		}

		printf("Server: Client Connected!\n");
		m_socket = AcceptSocket;
		break;
	}

	int bytesSent;
	int bytesRecv = SOCKET_ERROR;
	char sendbuf[200] = "**********TEST DATA FROM SERVER**********";	
	char recvbuf[200] = "";

	// Send to client...
	printf("Server: Sending some test data to client...\n");
	bytesSent = send(m_socket, sendbuf, strlen(sendbuf), 0);

	printf("Server: send() is OK.\n");
	printf("Server: Bytes Sent: %ld.\n", bytesSent);	

	// Receives from client
	bytesRecv = recv(m_socket, recvbuf, 200, 0);


	printf("Server: recv() is OK.\n");
	printf("Server: Received data is: \"%s\"\n", recvbuf);
	printf("Server: Bytes received: %ld.\n", bytesRecv);	

	WSACleanup();
	//return 0;
	getchar();
}