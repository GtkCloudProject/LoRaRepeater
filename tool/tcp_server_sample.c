#include <stdio.h>
#include <sys/socket.h>
#include <string.h>
#include <netinet/in.h>
#include <fcntl.h>
#include <sys/ioctl.h>

#define ROBOT_LISTEN_PORT 4006
#define RECV_BUF_LEN 128

int main()
{
     //To create server socket
     int on = 1;
     int robot_ser_sock = socket(AF_INET, SOCK_STREAM, 0);
     int cli_sock = 0;
     int recv_len = 0;
     char recv_buf[RECV_BUF_LEN] = {0};
     struct sockaddr_in pin;
     socklen_t addrsize = (socklen_t)sizeof(struct sockaddr_in);
     if(robot_ser_sock < 0)
     {
         return -1;
     }
     else
     {
         int opt = fcntl(robot_ser_sock, F_GETFD);
         if (opt == -1)
         {
             printf("error !\n");
         }
         else
         {
             if (fcntl(robot_ser_sock, F_SETFD, opt | FD_CLOEXEC) == -1)
             {
                 printf("error !\n");
             }
         }
     }
     setsockopt(robot_ser_sock, SOL_SOCKET, SO_REUSEADDR, (const char *) &on, sizeof(on));
     ioctl(robot_ser_sock, FIONBIO, &on);
     struct sockaddr_in robot_srv;
     bzero(&robot_srv, sizeof(robot_srv));
     robot_srv.sin_family = AF_INET;
     robot_srv.sin_addr.s_addr = INADDR_ANY;
     robot_srv.sin_port = htons(ROBOT_LISTEN_PORT);

     if(bind(robot_ser_sock, (struct sockaddr*)&robot_srv, sizeof(robot_srv)) != 0)
     {
         return 0;
     }
     if (listen(robot_ser_sock, 20) == -1)
     {
         return 0;
     }

     int flag = 0;
     while(1)
     {
         memset(recv_buf, 0x00, RECV_BUF_LEN);
         if (flag == 0)
         {
             cli_sock = accept(robot_ser_sock, (struct sockaddr *)&pin, &addrsize);
         }
         recv_len = recv(cli_sock, recv_buf, RECV_BUF_LEN, 0);
         if(recv_len > 0)
         {
             flag = 1;
             printf("From client: %s\n", recv_buf);
         }
     }
}
