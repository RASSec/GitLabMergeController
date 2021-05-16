import pika
from threading import Thread
import time


class OneTimeProducer():

   def __init__(self,connection,exchange,routing_key):
       self.channel=connection.channel()
       self.exchange=exchange
       self.routing_key=routing_key


   def sendMessage(self,message):
         try:
            self.channel.basic_publish(exchange=self.exchange,
                                      routing_key=self.routing_key,
                                       body=message)
         finally:
            self.channel.close()

def producer_handler(connection):

    #initial producer object
    producer = OneTimeProducer(connection=connection,
                        exchange="ky-exchange-fanout",
                        routing_key="QA")
    producer.start_handler()

# credentials = pika.PlainCredentials('admin', 'admin123')
# connection = pika.BlockingConnection(pika.ConnectionParameters('10.122.64.110', 5672, 'kongyi', credentials))
#
# if __name__ == '__main__':
#     credentials = pika.PlainCredentials('admin', 'admin123')
#     connection = pika.BlockingConnection(pika.ConnectionParameters(
#         '10.122.64.110', 5672, 'kongyi', credentials))
#     try:
#         producer_handler(connection)
#     finally:
#       connection.close()





