import modelserver_pb2_grpc, modelserver_pb2
import grpc
import threading
import sys

class Client:
    def __init__(self, port, coef, files):
        self.channel = grpc.insecure_channel(f'localhost:{port}')
        self.stub = modelserver_pb2_grpc.ModelServerStub(self.channel)
        self.coef = list(map(float, coef.split(',')))
        self.files = files
        self.total_hits = 0
        self.total_requests = 0
        

    def set_coef(self):

        response = self.stub.SetCoefs(modelserver_pb2.SetCoefsRequest(coefs=self.coef))
        

    def process_csv(self, file):

        hits = 0

        requests = 0

        with open(file, 'r') as f:
            for line in f:
                row = list(map(float, line.strip().split(',')))
                response = self.stub.Predict(modelserver_pb2.PredictRequest(X=row))
                print(type(response))
                if response.hit:
                    hits += 1
                requests += 1
        self.total_hits += hits
        self.total_requests += requests
        

    def run_threads(self):
        threads = []
        for file in self.files:
            thread = threading.Thread(target=self.process_csv, args=(file,))
            threads.append(thread)


        for thread in threads:
            thread.start()
            thread.join()

        hit_rate = self.total_hits / self.total_requests if self.total_requests > 0 else 0
        print(hit_rate)
        
if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python3 client.py <PORT> <COEF> <THREAD1-WORK.csv> <THREAD2-WORK.csv> ...")
        sys.exit(1)

    port = int(sys.argv[1])
    coef = sys.argv[2]
    files = sys.argv[3:]
    print(port)
    print(coef)
    print(files)
    client = Client(port, coef, files)
    client.set_coef()
    client.run_threads()
