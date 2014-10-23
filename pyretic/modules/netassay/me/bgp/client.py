import asyncore, socket

class Client(asyncore.dispatcher_with_send):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.out_buffer = ''

    def handle_close(self):
        self.close()

    def handle_read(self):
        print 'Received', self.recv(1024)
       
    def writable(self):
        return False
    
    def send_msg(self, message):
        print "send:" + message
        sent = self.sendall(message)
  
